#!/bin/bash
#SBATCH --job-name=rsfc
#SBATCH --time=50:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=IB_16C_96G
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x_%A-%a.err
# ------------------------------------------

pwd; hostname; date
set -e

# sbatch --array=1-1200%150 rsfc_job.sbatch

#==============Shell script==============#
#Load the software needed
# source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
module load singularity-3.5.3

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
ROIs_DIR="${DSET_DIR}/seed-regions"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis"
DERIVS_DIR="${BIDS_DIR}/derivatives"
IMG_DIR="/home/data/abcd/code/singularity-images"

mriqc_ver=0.16.1
fmriprep_ver=21.0.0
afni_ver=22.0.20
MRIQC_DIR="${DERIVS_DIR}/mriqc-${mriqc_ver}"
FMRIPREP_DIR="${DERIVS_DIR}/fmriprep-${fmriprep_ver}"
CLEAN_DIR="${DERIVS_DIR}/denoising-${afni_ver}"


# THISJOBVALUE=${SLURM_ARRAY_TASK_ID}
# Use for array > 1000 elements uncomment the following two lines and comment the previous line
VALUES=({1000..1200})
THISJOBVALUE=${VALUES[${SLURM_ARRAY_TASK_ID}]}

subject=$( sed -n -E "$((${THISJOBVALUE} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )
session="ses-baselineYear1Arm1"
desc_clean="aCompCorCens"
desc_sm="aCompCorSM6Cens"
space="MNI152NLin2009cAsym"

# Run RSFC pipeline
# For individual Clusters, just change the derivatives output name
# research_questions=(RQ1 RQ2)
research_questions=(RQ1)
for research_question in ${research_questions[@]}; do
    if [[ ${research_question} ==  "RQ1" ]]; then
        seed_regions=(vmPFC insula TPJ)
    elif [[ ${research_question} ==  "RQ2" ]]; then
        seed_regions=(vmPFC insula hippocampus striatum amygdala TPJ)
    fi
    for seed_region in ${seed_regions[@]}; do
        if [[ ${seed_region} ==  "vmPFC" ]]; then
            hemispheres=(none)
        elif [[ ${seed_region} ==  "TPJ" ]]; then
            if [[ ${research_question} ==  "RQ1" ]]; then
                hemispheres=(lh rh)
            elif [[ ${research_question} ==  "RQ2" ]]; then
                hemispheres=(none)
            fi
        else
            hemispheres=(lh rh)
        fi
        for hemis in ${hemispheres[@]}; do
            if [[ ${seed_region} ==  "vmPFC" ]]; then
                if [[ ${research_question} ==  "RQ1" ]]; then
                    C3="/rois_dir/${seed_region}/sub-vmPFC3_desc-brain_mask.nii.gz"
                    clusters=(${C3})
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C3"
                elif [[ ${research_question} ==  "RQ2" ]]; then
                    C1="/rois_dir/${seed_region}/sub-vmPFC1_desc-brain_mask.nii.gz"
                    C2="/rois_dir/${seed_region}/sub-vmPFC2_desc-brain_mask.nii.gz"
                    C3="/rois_dir/${seed_region}/sub-vmPFC3_desc-brain_mask.nii.gz"
                    C4="/rois_dir/${seed_region}/sub-vmPFC4_desc-brain_mask.nii.gz"
                    C5="/rois_dir/${seed_region}/sub-vmPFC5_desc-brain_mask.nii.gz"
                    C6="/rois_dir/${seed_region}/sub-vmPFC6_desc-brain_mask.nii.gz"
                    clusters=(${C1} ${C2} ${C3} ${C4} ${C5} ${C6})
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1-C2-C3-C4-C5-C6"
                fi
            elif [[ ${seed_region} ==  "insula" ]]; then
                if [[ ${research_question} ==  "RQ1" ]]; then
                    C1="/rois_dir/${seed_region}/sub-insulaD${hemis}_desc-brain_mask.nii.gz"
                    clusters=(${C1})
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_D${hemis}"
                elif [[ ${research_question} ==  "RQ2" ]]; then
                    C1="/rois_dir/${seed_region}/sub-insulaD${hemis}_desc-brain_mask.nii.gz"
                    C2="/rois_dir/${seed_region}/sub-insulaP${hemis}_desc-brain_mask.nii.gz"
                    C3="/rois_dir/${seed_region}/sub-insulaV${hemis}_desc-brain_mask.nii.gz"
                    clusters=(${C1} ${C2} ${C3})
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_D${hemis}-P${hemis}-V${hemis}"
                fi
            elif [[ ${seed_region} ==  "hippocampus" ]]; then
                C1="/rois_dir/${seed_region}/sub-hippocampus3solF1${hemis}_desc-brain_mask.nii.gz"
                C2="/rois_dir/${seed_region}/sub-hippocampus3solF2${hemis}_desc-brain_mask.nii.gz"
                C3="/rois_dir/${seed_region}/sub-hippocampus3solF3${hemis}_desc-brain_mask.nii.gz"
                clusters=(${C1} ${C2} ${C3})
                RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_3solF1${hemis}-3solF2${hemis}-3solF3${hemis}"
            elif [[ ${seed_region} ==  "striatum" ]]; then
                C1="/rois_dir/${seed_region}/sub-striatumMatchCD${hemis}_desc-brain_mask.nii.gz"
                C2="/rois_dir/${seed_region}/sub-striatumMatchCV${hemis}_desc-brain_mask.nii.gz"
                C3="/rois_dir/${seed_region}/sub-striatumMatchDL${hemis}_desc-brain_mask.nii.gz"
                C4="/rois_dir/${seed_region}/sub-striatumMatchD${hemis}_desc-brain_mask.nii.gz"
                C5="/rois_dir/${seed_region}/sub-striatumMatchR${hemis}_desc-brain_mask.nii.gz"
                C6="/rois_dir/${seed_region}/sub-striatumMatchV${hemis}_desc-brain_mask.nii.gz"
                clusters=(${C1} ${C2} ${C3} ${C4} ${C5} ${C6})
                RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_matchCD${hemis}-matchCV${hemis}-matchDL${hemis}-matchD${hemis}-matchR${hemis}-matchV${hemis}"
            elif [[ ${seed_region} ==  "amygdala" ]]; then
                C1="/rois_dir/${seed_region}/sub-amygdala1${hemis}_desc-brain_mask.nii.gz"
                C2="/rois_dir/${seed_region}/sub-amygdala2${hemis}_desc-brain_mask.nii.gz"
                C3="/rois_dir/${seed_region}/sub-amygdala3${hemis}_desc-brain_mask.nii.gz"
                clusters=(${C1} ${C2} ${C3})
                RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1${hemis}-C2${hemis}-C3${hemis}"
            elif [[ ${seed_region} ==  "TPJ" ]]; then
                if [[ ${research_question} ==  "RQ1" ]]; then
                    C2="/rois_dir/${seed_region}/sub-TPJp${hemis}_desc-brain_mask.nii.gz"
                    clusters=(${C2})
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_Cp${hemis}"
                elif [[ ${research_question} ==  "RQ2" ]]; then
                    C1="/rois_dir/${seed_region}/sub-TPJa_desc-brain_mask.nii.gz"
                    C2="/rois_dir/${seed_region}/sub-TPJp_desc-brain_mask.nii.gz"
                    clusters=(${C1} ${C2})
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_Ca-Cp"
                fi
            fi
            mkdir -p ${RSFC_DIR}

            SHELL_CMD="singularity exec --cleanenv \
                -B ${CODE_DIR}:/code \
                -B ${MRIQC_DIR}:/mriqc \
                -B ${CLEAN_DIR}:/clean \
                -B ${RSFC_DIR}:/rsfc \
                -B ${ROIs_DIR}:/rois_dir \
                ${IMG_DIR}/afni-${afni_ver}.sif"

            rsfc="${SHELL_CMD} python /code/analysis/rest/rsfc.py \
                --mriqc_dir /mriqc \
                --clean_dir /clean \
                --rsfc_dir /rsfc \
                --subject sub-${subject} \
                --sessions ${session} \
                --space ${space} \
                --desc_list ${desc_clean} ${desc_sm} \
                --rois ${clusters[@]} \
                --n_jobs ${SLURM_CPUS_PER_TASK}"
            # Setup done, run the command
            echo
            echo Commandline: $rsfc
            eval $rsfc 
            exitcode=$?
        done
    done
done

# Output results to a table
echo "sub-$subject   ${THISJOBVALUE}    $exitcode" \
      >> ${DSET_DIR}/code/log/${SLURM_JOB_NAME}/${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
echo Finished tasks ${THISJOBVALUE} with exit code $exitcode
date

exit $exitcode