#!/bin/bash
#SBATCH --job-name=vmPFC
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=investor
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x-img_%j.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x/%x-img_%j.err
# ------------------------------------------

pwd; hostname; date
set -e

source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
DERIVS_DIR="${BIDS_DIR}/derivatives"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis/analysis/rest"

bg_img="/home/data/cis/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_desc-brain_T1w.nii.gz"


seed_regions=(vmPFC insula hippocampus striatum amygdala TPJ)
for seed_region in ${seed_regions[@]}; do
    if [[ ${seed_region} ==  "vmPFC" ]]; then
        hemispheres=(none)
    else
        hemispheres=(lh rh)
    fi
    for hemis in ${hemispheres[@]}; do
        if [[ ${seed_region} ==  "vmPFC" ]]; then
            ROIs=("vmPFC1" "vmPFC2" "vmPFC3" "vmPFC4" "vmPFC5" "vmPFC6")
            RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1-C2-C3-C4-C5-C6"
        elif [[ ${seed_region} ==  "insula" ]]; then
            ROIs=("insulaD${hemis}" "insulaP${hemis}" "insulaV${hemis}")
            RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_D${hemis}-P${hemis}-V${hemis}"
        elif [[ ${seed_region} ==  "hippocampus" ]]; then
            ROIs=("hippocampus3solF1${hemis}" "hippocampus3solF2${hemis}" "hippocampus3solF3${hemis}")
            RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_3solF1${hemis}-3solF2${hemis}-3solF3${hemis}"
        elif [[ ${seed_region} ==  "striatum" ]]; then
            ROIs=("striatumMatchCD${hemis}" "striatumMatchCV${hemis}" "striatumMatchDL${hemis}" "striatumMatchD${hemis}" "striatumMatchR${hemis}" "striatumMatchV${hemis}")
            RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_matchCD${hemis}-matchCV${hemis}-matchDL${hemis}-matchD${hemis}-matchR${hemis}-matchV${hemis}"
        elif [[ ${seed_region} ==  "amygdala" ]]; then
            ROIs=("amygdala1${hemis}" "amygdala2${hemis}" "amygdala3${hemis}")
            RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1${hemis}-C2${hemis}-C3${hemis}"
        elif [[ ${seed_region} ==  "TPJ" ]]; then
        fi

        analyses_directory=${RSFC_DIR}/group-nonFam

        tests=('1SampletTest' '2SampletTest')
        for test in ${tests[@]}; do
            for analysis in ${ROIs[@]}; do
                if [[ ${test} == '1SampletTest' ]]; then
                    labels="Group_Zscr"
                    pvoxel=0.0001
                    pval=$(ptoz $pvoxel -2)
                fi

                if [[ ${test} == '2SampletTest' ]]; then
                    labels="nonUser-User_Zscr"
                    pvoxel=0.001
                    pval=$(ptoz $pvoxel -2)
                fi

                label_count=1
                for label in $labels; do
                    echo "Generating image for ${analysis}, ${seed_region}, ${hemis}, ${test}, $label"
                    result_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}Pos_result.nii.gz
                    result_file_img=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}Pos_result.nii.gz
                    result_neg_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}Neg_result.nii.gz
                    brik_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}_briks+tlrc.BRIK
                    stat_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}_briks.CSimA.NN2_2sided.1D

                    3dAFNItoNIFTI -prefix ${result_file_img} ${brik_file}\'[$label_count]\'

                    if [[ ${test} == '1SampletTest' ]]; then
                        csize=`1dcat ${stat_file}"{22}[6]"`
                    fi
                    if [[ ${test} == '2SampletTest' ]]; then
                        csize=`1dcat ${stat_file}"{16}[6]"`
                    fi
                    echo "\t$csize"

                    posthr_pos_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}PosP${pvoxel}minextent${csize}_result.nii.gz
                    posthr_neg_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}NegP${pvoxel}minextent${csize}_result.nii.gz
                    posthr_both_file=${analyses_directory}/${analysis}/sub-group_task-rest_desc-${test}${analysis}BothP${pvoxel}minextent${csize}_result.nii.gz

                    cluster --in=${result_file} --thresh=$pval --connectivity=6 --minextent=$csize --no_table --othresh=${posthr_pos_file}
                    fslmaths ${result_file} -mul -1 ${result_neg_file}
                    cluster --in=${result_neg_file} --thresh=$pval --connectivity=6 --minextent=$csize --no_table --othresh=${posthr_neg_file}

                    fslmaths ${posthr_pos_file} -sub ${posthr_neg_file} ${posthr_both_file}

                    # Plot image
                    out_img=${analyses_directory}/${analysis}/${test}${analysis}_result.png
                    python ${CODE_DIR}/generate_images.py --result_img ${posthr_both_file} --template_img ${bg_img} --out_img ${out_img}

                    label_count=$((label_count + 1))
                done
            done
        done
    done
done
date