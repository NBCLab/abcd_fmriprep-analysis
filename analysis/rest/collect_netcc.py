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


def get_netcc(netcc):
    netcc_mtx = []
    with open(netcc, "r") as input_file:
        for line in input_file:
            str_lst = line.split()
            if (str_lst[0] == "#") and (str_lst[1] == "FZ"):
                for line in input_file:
                    str_lst = line.split()
                    float_lst = [float(x) for x in str_lst]
                    netcc_mtx.append(float_lst)
    return netcc_mtx


def main(dset, denoising_dir):
    """Generate list of subject ID from participants.tsv but not in dset"""
    session = "ses-baselineYear1Arm1"

    participant_ids_fn = op.join(dset, "participants.tsv")
    participant_ids_df = pd.read_csv(participant_ids_fn, sep="\t")
    participant_ids = participant_ids_df["participant_id"].tolist()

    derivs_dir = op.join(dset, "derivatives")

    metrics = ["NETCC"]
    research_questions = ["RQ12b"]
    for research_question in research_questions:
        seed_regions = ["insulaDlh", "insulaDrh", "TPJplh", "TPJprh", "vmPFC3"]
        rsfc_dir = op.join(derivs_dir, f"rsfc-roi2roi")

        metric_df = pd.DataFrame()
        metric_df["participant_id"] = participant_ids
        for metric in metrics:
            for idx0 in range(len(seed_regions)):
                for idx1 in range(idx0 + 1, len(seed_regions)):
                    metric_lst = []
                    for participant_id in participant_ids:
                        # print(f"Processing {participant_id}", flush=True)
                        weighted_avg = float("NaN")
                        rsfc_subj_dir = op.join(rsfc_dir, participant_id, session, "func")
                        clean_subj_dir = op.join(denoising_dir, participant_id, session, "func")
                        # GEt path to netcc files
                        roi_subj_netcc_files = sorted(glob(op.join(rsfc_subj_dir, "*.netcc")))
                        if len(roi_subj_netcc_files) == 0:
                            metric_lst.append(weighted_avg)
                            continue

                        weight_lst = []
                        metric_val_lst = []
                        for roi_subj_netcc_file in roi_subj_netcc_files:
                            # Get metric
                            netcc_mtx = get_netcc(roi_subj_netcc_file)
                            if len(netcc_mtx) != len(seed_regions):
                                continue
                            # print(idx0, idx1)
                            # print(participant_id, netcc_mtx)
                            metric_val = netcc_mtx[idx0][idx1]
                            metric_val_lst.append(metric_val)

                            # Get weights
                            prefix = op.basename(roi_subj_netcc_file).split("desc-")[0].rstrip("_")
                            censor_files = glob(op.join(clean_subj_dir, f"{prefix}_censoring*.1D"))
                            assert len(censor_files) == 1
                            censor_file = censor_files[0]
                            tr_censor = pd.read_csv(censor_file, header=None)
                            tr_left = len(tr_censor.index[tr_censor[0] == 1].tolist())
                            weight_lst.append(tr_left)
                        
                        if len(metric_val_lst) == 0:
                            metric_lst.append(float("NaN"))
                            continue

                        # Normalize weights
                        weight_norm_lst = [float(x) / sum(weight_lst) for x in weight_lst]

                        weighted_avg = np.average(metric_val_lst, weights=weight_norm_lst)
                        metric_lst.append(weighted_avg)

                    metric_df[f"{seed_regions[idx0]}_{seed_regions[idx1]}"] = metric_lst

        metric_df.to_csv(
            op.join(derivs_dir, f"{metric}_{research_question}.tsv"), sep="\t", index=False
        )


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
