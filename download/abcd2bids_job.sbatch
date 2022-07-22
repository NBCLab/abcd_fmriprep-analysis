#!/bin/bash
#SBATCH --job-name=abcd2bids
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=12gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_16C_96G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.err
# ------------------------------------------

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

# Get subjects to download
sub2download="${RAW_DIR}/sub2download.txt"

while IFS=\= read var; do
    subjects+=($var)
done < ${sub2download}

sub=${subjects[${SLURM_ARRAY_TASK_ID}]}

echo "Processing ${sub}"
SCRATCH_DIR="/scratch/nbc/jpera054/abcd_work/abcd2bids/${sub}"
mkdir -p ${SCRATCH_DIR}/spreadsheets
log_file=${LOG_DIR}/${sub}_dcm2bids

SINGULARITY_CMD="singularity run --cleanenv \
    -B ${BIDS_DIR}:/out \
    -B ${SCRATCH_DIR}:/work \
    -B ${RAW_DIR}:/raw \
    -B ${DSET_DIR}/code/config.ini:/data/config_file.ini \
    -B ${QC_DIR}/abcd_fastqc01.txt:/data/qc_spreadsheet.txt \
    -B ${SCRATCH_DIR}/spreadsheets:/opt/abcd-dicom2bids/spreadsheets \
    ${IMG_DIR}/abcddicom2bids-21.07.17.sif"

# Compose the command line
cmd="${SINGULARITY_CMD} \
    --subjects ${sub} \
    --sessions ${sessions} \
    --start_at unpack_and_setup \
    --stop_before validate_bids \
    --modalities 'anat' 'func' > ${log_file}"

# Setup done, run the command
echo Commandline: $cmd
eval $cmd
exitcode=$?


echo "sub-$sub   ${SLURM_ARRAY_TASK_ID}    $exitcode" \
      >> ${DSET_DIR}/code/log/${SLURM_JOB_NAME}/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${SLURM_ARRAY_TASK_ID} with exit code $exitcode
rm -rf ${SCRATCH_DIR}

date

exit $exitcode