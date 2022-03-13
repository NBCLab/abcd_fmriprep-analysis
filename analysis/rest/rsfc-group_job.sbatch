#!/bin/bash
#SBATCH --job-name=vmPFC
#SBATCH --time=50:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --mem-per-cpu=1gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_40C_512G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.err
# ------------------------------------------

pwd; hostname; date
set -e

# sbatch --array=0-2 rsfc-group_job.sh

#==============Shell script==============#
#Load the software needed
# source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
module load singularity-3.5.3
mriqc_ver=0.16.1
fmriprep_ver=21.0.0
afni_ver=20.2.10

FD_THR=0.2
seed_region=vmPFC
hemis=L
DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis/analysis/rest"
DERIVS_DIR="${BIDS_DIR}/derivatives"
IMG_DIR="/home/data/abcd/code/singularity-images"

FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
MRIQC_DIR="${DERIVS_DIR}/mriqc-${mriqc_ver}"
CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"
# CLEAN_DIR="${DERIVS_DIR}/denoisingFD${FD_THR}-${afni_ver}"
# RSFC_DIR="${DERIVS_DIR}/rsfcFD${FD_THR}-${seed_region}_d${hemis}-p${hemis}-v${hemis}"
RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1-C2-C3-C4-C5-C6"
# RSFC_DIR="${DERIVS_DIR}/rsfcFD${FD_THR}-${seed_region}_C1-C2-C3-C4-C5-C6"

TEMPLATE_DIR="/home/data/abcd/abcd-hispanic-via/dset/derivatives/templates"
template="sub-24x24x24_bucket+tlrc.BRIK"
template_mask="sub-24x24x24_desc-brain_mask.nii.gz"
session="ses-baselineYear1Arm1"
group="nonFam"

# Run group analysis
if [[ ${seed_region} ==  "vmPFC" ]]; then
    ROIs=("vmPFC1" "vmPFC2" "vmPFC3" "vmPFC4" "vmPFC5" "vmPFC6")
    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1-C2-C3-C4-C5-C6"
elif [[ ${seed_region} ==  "insula" ]]; then
    ROIs=("insulaD${hemis}" "insulaP${hemis}" "insulaV${hemis}")
    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_D${hemis}-P${hemis}-V${hemis}"
elif [[ ${seed_region} ==  "hippocampus" ]]; then
    ROIs=("hippocampus3solF1${hemis}" "hippocampus3solF2${hemis}" "hippocampus3solF3${hemis}")
    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_3solF1${hemis}-3solF2${hemis}-3solF3${hemis}"
elif [[ ${seed_region} ==  "striatum" ]]; then
    ROIs=("striatumMatchCD${hemis}" "striatumMatchCV${hemis}" "striatumMatchDL${hemis}" "striatumMatchD${hemis}" "striatumMatchR${hemis}" "striatumMatchV${hemis}")
    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_matchCD${hemis}-matchCV${hemis}-matchDL${hemis}-matchD${hemis}-matchR${hemis}-matchV${hemis}"
fi

ROI=${ROIs[${SLURM_ARRAY_TASK_ID}]}
SHELL_CMD="singularity exec --cleanenv \
    -B ${BIDS_DIR}:/data \
    -B ${CODE_DIR}:/code \
    -B ${MRIQC_DIR}:/mriqc \
    -B ${FMRIPREP_DIR}:/fmriprep \
    -B ${CLEAN_DIR}:/clean \
    -B ${TEMPLATE_DIR}:/template_dir
    -B ${RSFC_DIR}:/rsfc \
    $IMG_DIR/afni-22.0.17.sif"

analysis="${SHELL_CMD} python /code/rsfc-group.py \
    --dset /data
    --mriqc_dir /mriqc \
    --preproc_dir /fmriprep \
    --clean_dir /clean \
    --rsfc_dir /rsfc \
    --session ${session} \
    --template /template_dir/${template} \
    --template_mask /template_dir/${template_mask} \
    --group ${group} \
    --roi_lst ${ROIs[@]} \
    --roi ${ROI} \
    --n_jobs ${SLURM_CPUS_PER_TASK}"

# Setup done, run the command
echo
echo Commandline: $analysis
eval $analysis 
exitcode=$?

# Run threshold_images.sh


echo Finished tasks with exit code $exitcode
date

exit $exitcode