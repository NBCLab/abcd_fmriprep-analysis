import argparse
import os.path as op
from glob import glob

import numpy as np
import pandas as pd


def _get_parser():
    parser = argparse.ArgumentParser(description="Get subjects to download")
    parser.add_argument(
        "--dset",
        dest="dset",
        required=True,
        help="Path to BIDS directory",
    )
    parser.add_argument(
        "--denoising_dir",
        dest="denoising_dir",
        required=True,
        help="Path to denoising directory",
    )
    return parser


def main(dset, denoising_dir):
    """Generate list of subject ID from participants.tsv but not in dset"""
    session = "ses-baselineYear1Arm1"

    participant_ids_fn = op.join(dset, "participants.tsv")
    participant_ids_df = pd.read_csv(participant_ids_fn, sep="\t")
    participant_ids = participant_ids_df["participant_id"].tolist()

    derivs_dir = op.join(dset, "derivatives")

    metrics = ["FALFF", "REHO"]
    # research_questions = ["RQ1", "RQ2"]
    research_questions = ["RQ1"]
    for research_question in research_questions:
        if research_question == "RQ1":
            seed_regions = ["vmPFC", "insula", "TPJ"]
        elif research_question == "RQ2":
            seed_regions = ["vmPFC", "insula", "hippocampus", "striatum", "amygdala", "TPJ"]
    
        for metric in metrics:
            metric_df = pd.DataFrame()
            metric_df["participant_id"] = participant_ids

            for seed_region in seed_regions:
                if seed_region == "vmPFC":
                    hemispheres = ["none"]
                elif seed_region == "TPJ":
                    if research_question == "RQ1":
                        hemispheres = ["lh", "rh"]
                    elif research_question == "RQ2":
                        hemispheres = ["none"]
                else:
                    hemispheres = ["lh", "rh"]
                for hemis in hemispheres:
                    if seed_region == "vmPFC":
                        if research_question == "RQ1":
                            clusters = ["vmPFC3"]
                            rsfc_dir = op.join(derivs_dir, f"rsfc-{seed_region}_C3")
                        elif research_question == "RQ2":
                            clusters = ["vmPFC1", "vmPFC2", "vmPFC3", "vmPFC4", "vmPFC5", "vmPFC6"]
                            rsfc_dir = op.join(derivs_dir, f"rsfc-{seed_region}_C1-C2-C3-C4-C5-C6")
                    elif seed_region == "insula":
                        if research_question == "RQ1":
                            clusters = [f"insulaD{hemis}"]
                            rsfc_dir = op.join(
                                derivs_dir, f"rsfc-{seed_region}_D{hemis}"
                            )
                        elif research_question == "RQ2":
                            clusters = [f"insulaD{hemis}", f"insulaP{hemis}", f"insulaV{hemis}"]
                            rsfc_dir = op.join(
                                derivs_dir, f"rsfc-{seed_region}_D{hemis}-P{hemis}-V{hemis}"
                            )
                    elif seed_region == "hippocampus":
                        clusters = [
                            f"hippocampus3solF1{hemis}",
                            f"hippocampus3solF2{hemis}",
                            f"hippocampus3solF3{hemis}",
                        ]
                        rsfc_dir = op.join(
                            derivs_dir, f"rsfc-{seed_region}_3solF1{hemis}-3solF2{hemis}-3solF3{hemis}"
                        )
                    elif seed_region == "striatum":
                        clusters = [
                            f"striatumMatchCD{hemis}",
                            f"striatumMatchCV{hemis}",
                            f"striatumMatchDL{hemis}",
                            f"striatumMatchD{hemis}",
                            f"striatumMatchR{hemis}",
                            f"striatumMatchV{hemis}",
                        ]
                        rsfc_dir = op.join(
                            derivs_dir,
                            f"rsfc-{seed_region}_matchCD{hemis}-matchCV{hemis}-matchDL{hemis}-matchD{hemis}-matchR{hemis}-matchV{hemis}",
                        )
                    elif seed_region == "amygdala":
                        clusters = [f"amygdala1{hemis}", f"amygdala2{hemis}", f"amygdala3{hemis}"]
                        rsfc_dir = op.join(
                            derivs_dir, f"rsfc-{seed_region}_C1{hemis}-C2{hemis}-C3{hemis}"
                        )
                    elif seed_region == "TPJ":
                        if research_question == "RQ1":
                            clusters = [f"TPJp{hemis}"]
                            rsfc_dir = op.join(derivs_dir, f"rsfc-{seed_region}_Cp{hemis}")
                        elif research_question == "RQ2":
                            clusters = ["TPJa", "TPJp"]
                            rsfc_dir = op.join(derivs_dir, f"rsfc-{seed_region}_Ca-Cp")
                    for cluster in clusters:
                        metric_lst = []
                        for participant_id in participant_ids:
                            # print(f"Processing {participant_id}", flush=True)
                            weighted_avg = float("NaN")
                            rsfc_subj_dir = op.join(rsfc_dir, participant_id, session, "func")
                            clean_subj_dir = op.join(denoising_dir, participant_id, session, "func")
                            # Average fALFF of each voxel within each ROIs
                            roi_subj_falff_files = sorted(
                                glob(op.join(rsfc_subj_dir, f"*_desc-{cluster}_{metric}.txt"))
                            )
                            if len(roi_subj_falff_files) == 0:
                                metric_lst.append(weighted_avg)
                                continue

                            weight_lst = []
                            metric_val_lst = []
                            for roi_subj_falff_file in roi_subj_falff_files:
                                # Get metric
                                metric_val = pd.read_csv(roi_subj_falff_file, header=None)[0][0]
                                metric_val_lst.append(metric_val)
                                # Get weights
                                prefix = op.basename(roi_subj_falff_file).split("desc-")[0].rstrip("_")
                                censor_files = glob(op.join(clean_subj_dir, f"{prefix}_censoring*.1D"))
                                assert len(censor_files) == 1
                                censor_file = censor_files[0]
                                tr_censor = pd.read_csv(censor_file, header=None)
                                tr_left = len(tr_censor.index[tr_censor[0] == 1].tolist())
                                weight_lst.append(tr_left)
                            # Normalize weights
                            weight_norm_lst = [float(x) / sum(weight_lst) for x in weight_lst]
                            # print(f"\tProcessing files\n\t{roi_subj_falff_files}\n\t{metric_val_lst} {weight_norm_lst}", flush=True)

                            weighted_avg = np.average(metric_val_lst, weights=weight_norm_lst)
                            metric_lst.append(weighted_avg)

                        metric_df[cluster] = metric_lst

            metric_df.to_csv(op.join(derivs_dir, f"{metric}_{research_question}.tsv"), sep="\t", index=False)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
