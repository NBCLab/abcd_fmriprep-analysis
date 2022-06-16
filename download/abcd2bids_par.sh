#!/bin/bash

pwd; hostname; date
set -e

#==============Shell script==============#
#Load the software needed
module load singularity-3.5.3

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="/home/data/abcd/abcd-hispanic-via/raw/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
LOG_DIR="${DSET_DIR}/code/log/abcd2bids"
RAW_DIR="${DSET_DIR}/raw"
IMG_DIR="/home/data/abcd/code/singularity-images"
QC_DIR="/home/data/abcd/code/spreadsheets"
mkdir -p ${LOG_DIR}
mkdir -p ${RAW_DIR}
sessions=baseline_year_1_arm_1

sub2download="${RAW_DIR}/sub2download.txt"
# parallel -j 4 ./abcd2bids_par.sh {} < /home/data/abcd/abcd-hispanic-via/raw/sub2download.txt

# Get subjects to download
sub=$1

echo "Processing ${sub}"
SCRATCH_DIR="/scratch/nbc/jpera054/abcd_work/abcd2bids/${sub}"
mkdir -p ${SCRATCH_DIR}/spreadsheets
log_file=${LOG_DIR}/${sub}

SINGULARITY_CMD="singularity run --cleanenv \
    -B ${BIDS_DIR}:/out \
    -B ${SCRATCH_DIR}:/work \
    -B ${RAW_DIR}:/raw \
    -B ${DSET_DIR}/code/config.ini:/data/config_file.ini \
    -B ${QC_DIR}/abcd_fastqc01.txt:/data/qc_spreadsheet.txt \
    -B ${SCRATCH_DIR}/spreadsheets:/opt/abcd-dicom2bids/spreadsheets \
    ${IMG_DIR}/abcddicom2bids-21.07.15.sif"

# Compose the command line
cmd="${SINGULARITY_CMD} \
    --subjects ${sub} \
    --sessions ${sessions} \
    --modalities 'anat' 'func' > ${log_file}"

# Setup done, run the command
echo Commandline: $cmd
eval $cmd
rm -rf ${SCRATCH_DIR}
rm -rf ${RAW_DIR}/${sub}
date