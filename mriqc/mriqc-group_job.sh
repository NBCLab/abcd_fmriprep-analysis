#!/bin/bash
#SBATCH --job-name=mriqc
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
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

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
IMG_DIR="/home/data/cis/singularity-images"
DERIVS_DIR="${BIDS_DIR}/derivatives/mriqc-${mriqc_ver}"
SCRATCH_DIR="/scratch/nbc/jpera054/abcd_work/mriqc-${mriqc_ver}/group"
mkdir -p ${DERIVS_DIR}
mkdir -p ${SCRATCH_DIR}

TEMPLATEFLOW_HOST_HOME="/home/data/cis/templateflow"
export SINGULARITYENV_TEMPLATEFLOW_HOME=${TEMPLATEFLOW_HOST_HOME}

SINGULARITY_CMD="singularity run --cleanenv \
      -B $BIDS_DIR:/data \
      -B ${DERIVS_DIR}:/out \
      -B ${TEMPLATEFLOW_HOST_HOME}:${SINGULARITYENV_TEMPLATEFLOW_HOME} \
      -B ${SCRATCH_DIR}:/work \
      ${IMG_DIR}/poldracklab_mriqc_${mriqc_ver}.sif"

# Compose the command line
mem_gb=`echo "${SLURM_MEM_PER_CPU} * ${SLURM_CPUS_PER_TASK} / 1024" | bc`
cmd="${SINGULARITY_CMD} /data \
      /out \
      group \
      --no-sub \
      --verbose-reports \
      -w /work \
      --fd_thres 0.35 \
      --n_procs ${SLURM_CPUS_PER_TASK} \
      --mem_gb ${mem_gb}"

# Setup done, run the command
echo Commandline: $cmd
# eval $cmd
exitcode=$?

mriqc="python ${CODE_DIR}/mriqc/mriqc-group.py \
          --data ${DERIVS_DIR}"
# Setup done, run the command
echo
echo Commandline: $mriqc
eval $mriqc 
exitcode=$?

# Output results to a table
echo "MRIQC-group $exitcode"
rm -r ${SCRATCH_DIR}
date

exit $exitcode
