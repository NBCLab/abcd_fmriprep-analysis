#!/bin/bash
#SBATCH --job-name=rsfc-roi2roi
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

# sbatch --array=1-1200%150 rsfc_job.sbatch

#==============Shell script==============#
#Load the software needed
# source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
module load singularity-3.5.3

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
ROIs_DIR="${DSET_DIR}/seed-regions"
ATLAS_DIR="${DSET_DIR}/atlas"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
IMG_DIR="/home/data/abcd/code/singularity-images"

afni_ver=22.0.20
CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"

# THISJOBVALUE=${SLURM_ARRAY_TASK_ID}
# Use for array > 1000 elements uncomment the following two lines and comment the previous line
VALUES=({1000..1200})
THISJOBVALUE=${VALUES[${SLURM_ARRAY_TASK_ID}]}

subject=$( sed -n -E "$((${THISJOBVALUE} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )

desc_clean="aCompCorCens"
desc_sm="aCompCorSM6Cens"
space="MNI152NLin2009cAsym"

# Run RSFC pipeline
RSFC_DIR="${DERIVS_DIR}/rsfc-roi2roi"
mkdir -p ${RSFC_DIR}

# Run denoising pipeline
# Compose the command line
SHELL_CMD="singularity exec --cleanenv \
    -B ${CODE_DIR}:/code \
    -B ${CLEAN_DIR}:/clean \
    -B ${RSFC_DIR}:/rsfc \
    -B ${ATLAS_DIR}:/atlas_dir \
    ${IMG_DIR}/afni-${afni_ver}.sif"
# Run python script inside fmriprep environment
rsfc="${SHELL_CMD} python /code/analysis/rest/rsfc-roi2roi.py \
    --clean_dir /clean \
    --rsfc_dir /rsfc \
    --atlas_dir /atlas_dir \
    --subject sub-${subject} \
    --space ${space} \
    --desc_list ${desc_clean} ${desc_sm} \
    --n_jobs ${SLURM_CPUS_PER_TASK}"
# Setup done, run the command

echo
echo Commandline: $rsfc
eval $rsfc 
exitcode=$?

# Output results to a table
echo "sub-$subject   ${THISJOBVALUE}    $exitcode" \
      >> ${DSET_DIR}/code/log/${SLURM_JOB_NAME}/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${THISJOBVALUE} with exit code $exitcode
date

exit $exitcode