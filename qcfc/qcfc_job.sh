#!/bin/bash
#SBATCH --job-name=qcfc
#SBATCH --time=60:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_16C_96G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%j.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%j.err
# ------------------------------------------

pwd; hostname; date
set -e

# sbatch mriqc-group_job.sh

#==============Shell script==============#
#Load the software needed
source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
mriqc_ver=0.16.1
fmriprep_ver=21.0.0
afni_ver=20.2.10

FD_THR=0.2
DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
MRIQC_DIR="${DERIVS_DIR}/mriqc-${mriqc_ver}"
# CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"
CLEAN_DIR="${DERIVS_DIR}/denoisingFD${FD_THR}-${afni_ver}"
# QCFC_DIR="${DERIVS_DIR}/qcfc"
QCFC_DIR="${DERIVS_DIR}/qcfcFD${FD_THR}"
mkdir -p ${QCFC_DIR}

session="ses-baselineYear1Arm1"
desc_clean="aCompCorCens"
desc_sm="aCompCorSM6Cens"
space="MNI152NLin2009cAsym"

# Perform QCFC analyses
cmd="python ${CODE_DIR}/qcfc/qcfc.py \
    --dset ${BIDS_DIR} \
    --mriqc_dir ${MRIQC_DIR} \
    --preproc_dir ${FMRIPREP_DIR} \
    --clean_dir ${CLEAN_DIR} \
    --qcfc_dir ${QCFC_DIR} \
    --session ${session} \
    --space ${space} \
    --qc_thresh ${FD_THR} \
    --desc_list ${desc_clean} ${desc_sm} \
    --n_jobs ${SLURM_CPUS_PER_TASK}"
# Setup done, run the command
echo
echo Commandline: $cmd
eval $cmd 

exitcode=$?
date

exit $exitcode
