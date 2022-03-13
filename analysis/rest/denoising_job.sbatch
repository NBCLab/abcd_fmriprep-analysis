#!/bin/bash
#SBATCH --job-name=denoising
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
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

# sbatch --array=1-$(( $( wc -l /home/data/abcd/abcd-hispanic-via/dset/participants.tsv | cut -f1 -d' ' ) - 1 ))%2 3dTproject_job.sbatch

#==============Shell script==============#
#Load the software needed
# source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
module load singularity-3.5.3

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
IMG_DIR="/home/data/abcd/code/singularity-images"
# IMG_DIR="/home/data/cis/singularity-images"

mriqc_ver=0.16.1
fmriprep_ver=21.0.0
afni_ver=22.0.18
MRIQC_DIR="${DERIVS_DIR}/mriqc-${mriqc_ver}"
FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"
mkdir -p ${CLEAN_DIR}


THISJOBVALUE=${SLURM_ARRAY_TASK_ID}
# Use for array > 1000 elements uncomment the following two lines and comment the previous line
# VALUES=({1000..1200})
# THISJOBVALUE=${VALUES[${SLURM_ARRAY_TASK_ID}]}

subject=$( sed -n -E "$((${THISJOBVALUE} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )
session="ses-baselineYear1Arm1"

# Get manufacture to set dummy scans
jsonlist=($(ls ${BIDS_DIR}/sub-${subject}/*/*/*.json))
json=${jsonlist[-1]}
manufacturer=$(grep -oP '(?<="Manufacturer": ")[^"]*' ${json})
if [[ ${manufacturer} ==  "GE" ]]; then
	echo "Assign dummy-scans for ${manufacturer}"
	DM_SCANS=5
elif [[ ${manufacturer} == "Siemens" ]] || [[ ${manufacturer} == "Philips" ]]; then
	echo "Assign dummy-scans for ${manufacturer}"
    DM_SCANS=8
fi

FD_THR=0.35
desc_clean="aCompCorCens"
desc_sm="aCompCorSM6Cens"
space="MNI152NLin2009cAsym"
# Run denoising pipeline
SHELL_CMD="singularity exec --cleanenv \
    -B ${CODE_DIR}:/code \
    -B ${MRIQC_DIR}:/mriqc \
    -B ${FMRIPREP_DIR}:/fmriprep \
    -B ${CLEAN_DIR}:/clean \
    $IMG_DIR/afni-${afni_ver}.sif"
# /poldracklab-fmriprep_${fmriprep_ver}.sif
# /afni-${afni_ver}.sif
denoising="${SHELL_CMD} python /code/analysis/rest/denoising.py \
    --mriqc_dir /mriqc \
    --preproc_dir /fmriprep \
    --clean_dir /clean \
    --subject sub-${subject} \
    --sessions ${session} \
    --space ${space} \
    --fd_thresh ${FD_THR} \
    --dummy_scans ${DM_SCANS} \
    --desc_list ${desc_clean} ${desc_sm} \
    --n_jobs ${SLURM_CPUS_PER_TASK}"

# Setup done, run the command
echo
echo Commandline: $denoising
eval $denoising 
exitcode=$?

# Output results to a table
echo "sub-$subject   ${THISJOBVALUE}    $exitcode" \
      >> ${DSET_DIR}/code/log/${SLURM_JOB_NAME}/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${THISJOBVALUE} with exit code $exitcode
date

exit $exitcode