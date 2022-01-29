import argparse
import os.path as op

import numpy as np
import pandas as pd


def _get_parser():
    parser = argparse.ArgumentParser(description="Get outliers from QC metrics")
    parser.add_argument(
        "--data",
        dest="data",
        required=True,
        help="Path to MRIQC derivatives",
    )
    return parser


def main(data):
    # Adaptede from a function written by Michael Riedel
    mriqc_group_df = pd.read_csv(op.join(data, "group_bold.tsv"), sep="\t")

    # get task specific runs
    mriqc_group_rest_df = mriqc_group_df[mriqc_group_df["bids_name"].str.contains("task-rest")]

    # functional qc metrics of interest
    qc_metrics = ["efc", "snr", "fd_mean", "tsnr", "gsr_x", "gsr_y"]
    runs_exclude_df = pd.DataFrame()
    for qc_metric in qc_metrics:
        upper, lower = np.percentile(mriqc_group_rest_df[qc_metric].values, [99, 1])

        if qc_metric in ["efc", "fd_mean", "gsr_x", "gsr_y"]:
            runs_exclude_df = runs_exclude_df.append(
                mriqc_group_rest_df.loc[mriqc_group_rest_df[qc_metric].values > upper],
                ignore_index=True,
            )
        elif qc_metric in ["snr", "tsnr"]:
            runs_exclude_df = runs_exclude_df.append(
                mriqc_group_rest_df.loc[mriqc_group_rest_df[qc_metric].values < lower],
                ignore_index=True,
            )

    # drop duplicates
    runs_exclude_df = runs_exclude_df.drop_duplicates(subset=["bids_name"])
    runs_exclude_df.to_csv(op.join(data, "runs_to_exclude.tsv"), sep="\t", index=False)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
