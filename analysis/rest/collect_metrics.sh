#!/bin/bash
#SBATCH --job-name=metric
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
afni_ver=22.0.20

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis/analysis/rest"
DERIVS_DIR="${BIDS_DIR}/derivatives"
CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"
session="ses-baselineYear1Arm1"


# Run denoising pipeline
completion="python ${CODE_DIR}/collect_metrics.py \
          --dset ${BIDS_DIR} \
          --denoising_dir ${CLEAN_DIR}"
# Setup done, run the command
echo
echo Commandline: $completion
eval $completion 
exitcode=$?

exit $exitcode

date