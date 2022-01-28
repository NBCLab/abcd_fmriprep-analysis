#!/bin/bash
#SBATCH --job-name=3dTproject
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_16C_96G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x_%A-%a.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x_%A-%a.err
# ------------------------------------------

pwd; hostname; date
set -e

# sbatch --array=1-$(( $( wc -l /home/data/abcd/abcd-hispanic-via/dset/participants.tsv | cut -f1 -d' ' ) - 1 ))%2 3dTproject_job.sbatch

#==============Shell script==============#
#Load the software needed
source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
fmriprep_ver=21.0.0
afni_ver=20.2.06

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
3DTPROJECT_DIR="${DERIVS_DIR}/3dTproject-${afni_ver}"
RSFC_DIR="${DERIVS_DIR}/rsfc"
mkdir -p ${3DTPROJECT_DIR}
mkdir -p ${RSFC_DIR}

subject=$( sed -n -E "$((${SLURM_ARRAY_TASK_ID} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )
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
# Run denoising pipeline
denoising="python ${CODE_DIR}/analysis/rest/3dTproject.py \
          --preproc_dir ${FMRIPREP_DIR} \
          --clean_dir ${3DTPROJECT_DIR_DIR} \
          --subject sub-${subject} \
          --session ${session} \
          --fd_thresh ${FD_THR} \
          --dummy_scans ${DM_SCANS} \
          --desc_list ${desc_clean} ${desc_sm} \
          --n_jobs ${SLURM_CPUS_PER_TASK}"
# Setup done, run the command
echo Commandline: $denoising
eval $denoising 
exitcode=$?

# Run RSFC pipeline
C1="${DSET_DIR}/code/vmPFC_rsfc/rsfc_rois/sub-cluster1_desc-brain_mask.nii.gz"
C2="${DSET_DIR}/code/vmPFC_rsfc/rsfc_rois/sub-cluster2_desc-brain_mask.nii.gz"
C3="${DSET_DIR}/code/vmPFC_rsfc/rsfc_rois/sub-cluster3_desc-brain_mask.nii.gz"
C4="${DSET_DIR}/code/vmPFC_rsfc/rsfc_rois/sub-cluster4_desc-brain_mask.nii.gz"
C5="${DSET_DIR}/code/vmPFC_rsfc/rsfc_rois/sub-cluster5_desc-brain_mask.nii.gz"
C6="${DSET_DIR}/code/vmPFC_rsfc/rsfc_rois/sub-cluster6_desc-brain_mask.nii.gz"

rsfc="python ${CODE_DIR}/analysis/rest/rsfc.py \
          --preproc_dir ${FMRIPREP_DIR} \
          --clean_dir ${3DTPROJECT_DIR} \
          --rsfc_dir ${RSFC_DIR} \
          --subject sub-${subject} \
          --session ${session} \
          --desc_list ${desc_clean} ${desc_sm} \
          --rois ${C1} ${C2} ${C3} ${C4} ${C5} ${C6} \
          --n_jobs ${SLURM_CPUS_PER_TASK}"
# Setup done, run the command
echo Commandline: $rsfc
eval $rsfc 
exitcode=$?

# Output results to a table
echo "sub-$subject   ${SLURM_ARRAY_TASK_ID}    $exitcode" \
      >> ${DSET_DIR}/code/log/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${SLURM_ARRAY_TASK_ID} with exit code $exitcode
date

exit $exitcode