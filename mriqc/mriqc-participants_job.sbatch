#!/bin/bash
#SBATCH --job-name=mriqc
#SBATCH --time=20:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_16C_96G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.err
# ------------------------------------------

pwd; hostname; date
set -e

# sbatch --array=1-$(( $( wc -l /home/data/abcd/abcd-hispanic-via/dset/participants.tsv | cut -f1 -d' ' ) - 1 ))%38 mriqc-participants_job.sbatch

#==============Shell script==============#
#Load the software needed
source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
mriqc_ver=0.16.1

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"

# THISJOBVALUE=${SLURM_ARRAY_TASK_ID}
# Use for array > 1000 elements uncomment the following two lines and comment the previous line
VALUES=({1000..1200})
THISJOBVALUE=${VALUES[${SLURM_ARRAY_TASK_ID}]}

# Parse the participants.tsv file and extract one subject ID from the line corresponding to this SLURM task.
subject=$( sed -n -E "$((${THISJOBVALUE} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )

CODE_DIR="${DSET_DIR}/code"
IMG_DIR="/home/data/cis/singularity-images"
DERIVS_DIR="${BIDS_DIR}/derivatives/mriqc-${mriqc_ver}"
SCRATCH_DIR="/scratch/nbc/jpera054/abcd_work/mriqc-${mriqc_ver}/${subject}"
mkdir -p ${DERIVS_DIR}
mkdir -p ${SCRATCH_DIR}

TEMPLATEFLOW_HOST_HOME="/home/data/cis/templateflow"
export SINGULARITYENV_TEMPLATEFLOW_HOME=${TEMPLATEFLOW_HOST_HOME}

SINGULARITY_CMD="singularity run --cleanenv \
      -B $BIDS_DIR:/data \
      -B ${DERIVS_DIR}:/out \
      -B ${TEMPLATEFLOW_HOST_HOME}:${SINGULARITYENV_TEMPLATEFLOW_HOME} \
      -B ${SCRATCH_DIR}:/work \
      ${IMG_DIR}/poldracklab_mriqc_${mriqc_ver}.sif"

# Compose the command line
mem_gb=`echo "${SLURM_MEM_PER_CPU} * ${SLURM_CPUS_PER_TASK} / 1024" | bc`
cmd="${SINGULARITY_CMD} /data \
      /out \
      participant \
      --participant-label $subject \
      --no-sub \
      --verbose-reports \
      -w /work \
      --fd_thres 0.35 \
      --ants-nthreads ${SLURM_CPUS_PER_TASK} \
      --n_procs ${SLURM_CPUS_PER_TASK} \
      --mem_gb ${mem_gb}"

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
