#!/bin/bash
#SBATCH --job-name=get-atlas
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

#==============Shell script==============#
#Load the software needed
source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment

CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"

# Perform QCFC analyses
cmd="python ${CODE_DIR}/analysis/rest/get_ma-atlas.py"
# Setup done, run the command
echo
echo Commandline: $cmd
eval $cmd 

exitcode=$?
date

exit $exitcode
