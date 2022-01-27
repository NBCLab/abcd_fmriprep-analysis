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

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
mkdir -p ${DERIVS_DIR}

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

cmd="python ${CODE_DIR}/analysis/rest/3dTproject.py \
          --dset ${BIDS_DIR} \
          --subject sub-${subject} \
          --session ${session} \
          --fd_thresh ${FD_THR} \
          --dummy_scans ${DM_SCANS} \
          --fmriprep_ver ${fmriprep_ver} \
          --n_jobs ${SLURM_CPUS_PER_TASK}"
# Setup done, run the command
echo Commandline: $cmd
eval $cmd 

exitcode=$?

# Output results to a table
echo "sub-$subject   ${SLURM_ARRAY_TASK_ID}    $exitcode" \
      >> ${DSET_DIR}/code/log/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${SLURM_ARRAY_TASK_ID} with exit code $exitcode
date

exit $exitcode