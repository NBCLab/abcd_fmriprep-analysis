#!/bin/bash
#SBATCH --job-name=images
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2gb
#SBATCH --account=iacc_nbc
#SBATCH --qos=pq_nbc
#SBATCH --partition=investor
# Outputs ----------------------------------
#SBATCH --output=/home/data/abcd/abcd-hispanic-via/code/log/%x_%j.out
#SBATCH --error=/home/data/abcd/abcd-hispanic-via/code/log/%x_%j.err
# ------------------------------------------

pwd; hostname; date
set -e

# source /home/data/abcd/code/abcd_fmriprep-analysis/env/environment
module load singularity-3.5.3

afni_ver=22.0.20

DSET_DIR="/home/data/abcd/abcd-hispanic-via"
BIDS_DIR="${DSET_DIR}/dset"
DERIVS_DIR="${BIDS_DIR}/derivatives"
CODE_DIR="/home/data/abcd/code/abcd_fmriprep-analysis/analysis/rest"
IMG_DIR="/home/data/abcd/code/singularity-images"

# bg_img="/home/data/cis/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-01_desc-brain_T1w.nii.gz"
TEMP_DIR="/home/data/cis/templateflow/tpl-MNI152NLin2009cAsym"
bg_img="tpl-MNI152NLin2009cAsym_res-01_desc-brain_T1w.nii.gz"

tests=('1SampletTest' '2SampletTest')

# research_questions=(RQ1 RQ2)
research_questions=(RQ2)
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
                    ROIs=("vmPFC3")
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C3"
                elif [[ ${research_question} ==  "RQ2" ]]; then
                    ROIs=("vmPFC1" "vmPFC2" "vmPFC3" "vmPFC4" "vmPFC5" "vmPFC6")
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_C1-C2-C3-C4-C5-C6"
                fi
            elif [[ ${seed_region} ==  "insula" ]]; then
                if [[ ${research_question} ==  "RQ1" ]]; then
                    ROIs=("insulaD${hemis}")
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_D${hemis}"
                elif [[ ${research_question} ==  "RQ2" ]]; then
                    ROIs=("insulaD${hemis}" "insulaP${hemis}" "insulaV${hemis}")
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_D${hemis}-P${hemis}-V${hemis}"
                fi
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
                if [[ ${research_question} ==  "RQ1" ]]; then
                    ROIs=("TPJp${hemis}")
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_Cp${hemis}"
                elif [[ ${research_question} ==  "RQ2" ]]; then
                    ROIs=("TPJa" "TPJp")
                    RSFC_DIR="${DERIVS_DIR}/rsfc-${seed_region}_Ca-Cp"
                fi
            fi
            analyses_directory=${RSFC_DIR}

            SHELL_CMD="singularity exec --cleanenv \
                -B ${analyses_directory}:/data \
                -B ${CODE_DIR}:/code \
                -B ${TEMP_DIR}:/template \
                ${IMG_DIR}/afni-${afni_ver}.sif"

            for test in ${tests[@]}; do
                for analysis in ${ROIs[@]}; do
                    if [[ ${test} == '1SampletTest' ]]; then
                        labels=("Group_Zscr")
                    fi
                    if [[ ${test} == '2SampletTest' ]]; then
                        labels=("Detached-Bicult_Zscr")
                    fi
                    for label in ${labels[@]}; do
                        if [[ ${test} == '1SampletTest' ]]; then
                            pvoxel=0.0001
                            pval=`${SHELL_CMD} ptoz $pvoxel -2`
                            label_count=1
                        fi

                        if [[ ${test} == '2SampletTest' ]]; then
                            # pvoxel=0.001
                            pvoxel=0.01
                            # pvoxel=0.05
                            pval=`${SHELL_CMD} ptoz $pvoxel -2`
                            label_count=1
                        fi

                        echo "Generating image for ${analysis}, ${seed_region}, ${hemis}, ${test}, $label, $pval"
                        result_file_img=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}Pos_result.nii.gz
                        result_neg_file=group-nonFAMnonFD/${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}Neg_result.nii.gz
                        brik_file=group-nonFAMnonFD/${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}_briks+tlrc.BRIK
                        stat_file=group-nonFAMnonFD/${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}_briks.CSimA.NN2_2sided.1D

                        rm -rf ${analyses_directory}/group-nonFAMnonFD/${result_file_img}

                        convert="${SHELL_CMD} 3dAFNItoNIFTI \
                                                -prefix /data/group-nonFAMnonFD/${result_file_img} \
                                                /data/${brik_file}'[$label_count]'"
                        echo Commandline: $convert
                        eval $convert 

                        if [[ ${test} == '1SampletTest' ]]; then
                            csize=`${SHELL_CMD} 1dcat /data/${stat_file}"{22}[6]"`
                        fi
                        if [[ ${test} == '2SampletTest' ]]; then
                            # csize=`${SHELL_CMD} 1dcat /data/${stat_file}"{16}[6]"`
                            csize=`${SHELL_CMD} 1dcat /data/${stat_file}"{10}[6]"`
                            #csize=`${SHELL_CMD} 1dcat /data/${stat_file}"{5}[6]"`
                        fi
                        echo $csize

                        posthr_pos_file=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}PosP${pvoxel}_result.nii.gz
                        posthr_pos_clust=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}PosP${pvoxel}minextent${csize}_result.nii.gz
                        posthr_pos_txt=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}PosP${pvoxel}minextent${csize}_result.txt
                        posthr_neg_file=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}NegP${pvoxel}_result.nii.gz
                        posthr_neg_clust=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}NegP${pvoxel}minextent${csize}_result.nii.gz
                        posthr_neg_txt=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}NegP${pvoxel}minextent${csize}_result.txt
                        posthr_both_file=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}BothP${pvoxel}_result.nii.gz
                        posthr_both_clust=${analysis}/sub-group_ses-baselineYear1Arm1_task-rest_desc-${test}${analysis}BothP${pvoxel}minextent${csize}_result.nii.gz

                        cmd="${SHELL_CMD} fslmaths \
                                            /data/group-nonFAMnonFD/${result_file_img} \
                                            -thr $pval
                                            /data/group-nonFAMnonFD/${posthr_pos_file}"
                        echo Commandline: $cmd
                        eval $cmd

                        cmd="${SHELL_CMD} cluster \
                                            --in=/data/group-nonFAMnonFD/${result_file_img} \
                                            --thresh=$pval \
                                            --connectivity=6 \
                                            --no_table \
                                            --minextent=$csize \
                                            --othresh=/data/group-nonFAMnonFD/${posthr_pos_clust}"
                        echo Commandline: $cmd
                        # > /data/group-${program}/${posthr_pos_txt}
                        eval $cmd

                        cmd="${SHELL_CMD} fslmaths \
                                            /data/group-nonFAMnonFD/${result_file_img} \
                                            -mul -1 /data/${result_neg_file}"
                        echo Commandline: $cmd
                        eval $cmd 


                        cmd="${SHELL_CMD} fslmaths \
                                            /data/${result_neg_file} \
                                            -thr $pval
                                            /data/group-nonFAMnonFD/${posthr_neg_file}"
                        echo Commandline: $cmd
                        eval $cmd

                        cmd="${SHELL_CMD} cluster \
                                            --in=/data/${result_neg_file} \
                                            --thresh=$pval \
                                            --connectivity=6 \
                                            --no_table \
                                            --minextent=$csize \
                                            --othresh=/data/group-nonFAMnonFD/${posthr_neg_clust}"
                        echo Commandline: $cmd
                        # > /data/group-${program}/${posthr_neg_txt}
                        eval $cmd 

                        cmd="${SHELL_CMD} fslmaths \
                                            /data/group-nonFAMnonFD/${posthr_pos_file} \
                                            -sub /data/group-nonFAMnonFD/${posthr_neg_file} \
                                            /data/group-nonFAMnonFD/${posthr_both_file}"
                        echo Commandline: $cmd
                        eval $cmd 

                        cmd="${SHELL_CMD} fslmaths \
                                            /data/group-nonFAMnonFD/${posthr_pos_clust} \
                                            -sub /data/group-nonFAMnonFD/${posthr_neg_clust} \
                                            /data/group-nonFAMnonFD/${posthr_both_clust}"
                        echo Commandline: $cmd
                        eval $cmd 
                        
                        # Plot unthresholded image
                        out_3dttest=group-nonFAMnonFD/${analysis}/1-${test}${analysis}_unthreshold_result-3dttest.png
                        cmd="${SHELL_CMD} python /code/generate_images.py \
                                            --result_3dttest /data/group-nonFAMnonFD/${result_file_img} \
                                            --template_img /template/${bg_img} \
                                            --out_3dttest /data/${out_3dttest}"
                        echo Commandline: $cmd
                        eval $cmd 
                            
                        # Plot thresholded image
                        out_3dttest=group-nonFAMnonFD/${analysis}/2-${test}${analysis}_threshold_result-3dttest.png
                        cmd="${SHELL_CMD} python /code/generate_images.py \
                                            --result_3dttest /data/group-nonFAMnonFD/${posthr_both_file} \
                                            --template_img /template/${bg_img} \
                                            --out_3dttest /data/${out_3dttest}"
                        echo Commandline: $cmd
                        eval $cmd 

                        # Plot thresholded + cluster image
                        out_3dttest=group-nonFAMnonFD/${analysis}/3-${test}${analysis}_threshold+cluster_result-3dttest.png
                        cmd="${SHELL_CMD} python /code/generate_images.py \
                                            --result_3dttest /data/group-nonFAMnonFD/${posthr_both_clust} \
                                            --template_img /template/${bg_img} \
                                            --out_3dttest /data/${out_3dttest}"
                        echo Commandline: $cmd
                        eval $cmd 

                        label_count=$((label_count + 1))
                    done
                done
            done
        done
    done
done
date
date