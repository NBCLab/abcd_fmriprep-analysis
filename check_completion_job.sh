#!/bin/bash
#SBATCH --job-name=completion
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_16C_96G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x_%j.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x_%j.err
# ------------------------------------------

pwd; hostname; date
set -e

#==============Shell script==============#
#Load the software needed
source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
mriqc_ver=0.16.1
fmriprep_ver=21.0.0
afni_ver=20.2.10

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
MRIQC_DIR="${DERIVS_DIR}/mriqc-${mriqc_ver}"
FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"
RSFC_DIR="${DERIVS_DIR}/rsfc-vmPFC_C1-C2-C3-C4-C5-C6"
session="ses-baselineYear1Arm1"


# Run denoising pipeline
completion="python ${CODE_DIR}/check_completion.py \
          --dset ${BIDS_DIR} \
          --fmriprep_dir ${FMRIPREP_DIR} \
          --mriqc_dir ${MRIQC_DIR} \
          --denoising_dir ${CLEAN_DIR} \
          --rsfc_dir ${RSFC_DIR} \
          --session ${session}"
# Setup done, run the command
echo
echo Commandline: $completion
eval $completion 
exitcode=$?

exit $exitcode

date