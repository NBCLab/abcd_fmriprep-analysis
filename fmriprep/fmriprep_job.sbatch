#!/bin/bash
#SBATCH --job-name=fmriprep
#SBATCH --time=60:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_40C_512G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.err
# ------------------------------------------

pwd; hostname; date
set -e

# sbatch --array=1-$(( $( wc -l /home/data/abcd/abcd-hispanic-via/dset/participants.tsv | cut -f1 -d' ' ) - 1 ))%38 fmriprep_job.sbatch

#==============Shell script==============#
#Load the software needed
# source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
module load singularity-3.5.3
fmriprep_ver=21.0.0

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"

THISJOBVALUE=${SLURM_ARRAY_TASK_ID}
# Use for array > 1000 elements uncomment the following two lines and comment the previous line
# VALUES=({1000..1200})
# THISJOBVALUE=${VALUES[${SLURM_ARRAY_TASK_ID}]}

# Parse the participants.tsv file and extract one subject ID from the line corresponding to this SLURM task.
subject=$( sed -n -E "$((${THISJOBVALUE} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )

CODE_DIR="${DSET_DIR}/code"
IMG_DIR="/home/data/cis/singularity-images"
DERIVS_DIR="${BIDS_DIR}/derivatives/fmriprep-${fmriprep_ver}"
SCRATCH_DIR="/scratch/nbc/jpera054/abcd_work/fmriprep-${fmriprep_ver}/$subject"
mkdir -p ${DERIVS_DIR}
mkdir -p ${SCRATCH_DIR}

# Prepare some writeable bind-mount points.
TEMPLATEFLOW_HOST_HOME="/home/data/cis/templateflow"
# TEMPLATEFLOW_HOST_HOME=${HOME}/.cache/templateflow
FMRIPREP_HOST_CACHE=${HOME}/.cache/fmriprep
mkdir -p ${TEMPLATEFLOW_HOST_HOME}
mkdir -p ${FMRIPREP_HOST_CACHE}


# Make sure FS_LICENSE is defined in the container.
FS_LICENSE="/home/jpera054/Documents/freesurfer"

# Designate a templateflow bind-mount point
export SINGULARITYENV_TEMPLATEFLOW_HOME=${TEMPLATEFLOW_HOST_HOME}

# Add Slice timing information
# python /home/data/abcd/code/abcd_fmriprep-analysis/fmriprep/metadata_fix.py -b ${BIDS_DIR} -s ${subject}

SINGULARITY_CMD="singularity run --cleanenv \
      -B ${BIDS_DIR}:/data \
      -B ${DERIVS_DIR}:/out \
      -B ${TEMPLATEFLOW_HOST_HOME}:${SINGULARITYENV_TEMPLATEFLOW_HOME} \
      -B ${SCRATCH_DIR}:/work \
      -B ${FS_LICENSE}:/freesurfer \
      -B ${CODE_DIR}:/code
      $IMG_DIR/poldracklab-fmriprep_${fmriprep_ver}.sif"

# Get manufacture to set dummy scans
jsonlist=($(ls ${BIDS_DIR}/sub-${subject}/*/*/*.json))
json=${jsonlist[-1]}
manufacturer=$(grep -oP '(?<="Manufacturer": ")[^"]*' ${json})
if [[ ${manufacturer} ==  "GE" ]]; then
	echo "Assign dummy-scans for ${manufacturer}"
	dummyscans=5
elif [[ ${manufacturer} == "Siemens" ]] || [[ ${manufacturer} == "Philips" ]]; then
	echo "Assign dummy-scans for ${manufacturer}"
    dummyscans=8
fi

# Compose the command line
# --bids-filter-file /code/rest-config.json \
mem_gb=`echo "${SLURM_MEM_PER_CPU} * ${SLURM_CPUS_PER_TASK}" | bc -l`
cmd="${SINGULARITY_CMD} /data \
      /out \
      participant \
      --participant-label ${subject} \
      -w /work/ \
      -vv \
      --omp-nthreads ${SLURM_CPUS_PER_TASK} \
      --nprocs ${SLURM_CPUS_PER_TASK} \
      --mem_mb ${mem_gb} \
      --output-spaces MNI152NLin2009cAsym:res-native fsaverage5 \
      --dummy-scans ${dummyscans} \
      --ignore slicetiming \
      --return-all-components \
      --debug compcor \
      --notrack \
      --no-submm-recon \
      --fs-license-file /freesurfer/license.txt"

# Setup done, run the command
echo Running task ${THISJOBVALUE}
echo Commandline: $cmd
eval $cmd
exitcode=$?

# Output results to a table
echo "sub-$subject   ${THISJOBVALUE}    $exitcode" \
      >> ${CODE_DIR}/log/${SLURM_JOB_NAME}/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${THISJOBVALUE} with exit code $exitcode
rm -r ${SCRATCH_DIR}
date

exit $exitcode