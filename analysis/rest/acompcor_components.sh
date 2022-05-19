#!/bin/bash
#SBATCH --job-name=acompcor
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
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

# sbatch mriqc-group_job.sh

#==============Shell script==============#
#Load the software needed
source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
mriqc_ver=0.16.1
fmriprep_ver=21.0.0

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
MRIQC_DIR="${DERIVS_DIR}/mriqc-${mriqc_ver}"


session="ses-baselineYear1Arm1"

# Perform QCFC analyses
cmd="python ${CODE_DIR}/analysis/rest/acompcor_components.py \
    --mriqc_dir ${MRIQC_DIR} \
    --preproc_dir ${FMRIPREP_DIR} \
    --sessions ${session}"
# Setup done, run the command
echo
echo Commandline: $cmd
eval $cmd 

exitcode=$?
date

exit $exitcode
