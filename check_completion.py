import argparse
import os.path as op
from glob import glob

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
        "--fmriprep_dir",
        dest="fmriprep_dir",
        required=True,
        help="Path to fMRIPrep directory",
    )
    parser.add_argument(
        "--mriqc_dir",
        dest="mriqc_dir",
        required=True,
        help="Path to MRIQC directory",
    )
    parser.add_argument(
        "--denoising_dir",
        dest="denoising_dir",
        required=True,
        help="Path to denoising directory",
    )
    parser.add_argument(
        "--rsfc_dir",
        dest="rsfc_dir",
        required=True,
        help="Path to RSFC directory",
    )
    parser.add_argument(
        "--session",
        dest="session",
        required=True,
        help="Session ID",
    )
    return parser


def main(dset, fmriprep_dir, mriqc_dir, denoising_dir, rsfc_dir, session):
    """Generate list of subject ID from participants.tsv but not in dset"""

    participant_ids_fn = op.join(dset, "participants.tsv")
    participant_ids_df = pd.read_csv(participant_ids_fn, sep="\t")
    participant_ids = participant_ids_df["participant_id"].tolist()

    # Get competed MRIQC
    mriqc_files = sorted(glob(op.join(mriqc_dir, "sub-*_task-rest*_bold.html")))
    mriqc_ids_lst = [op.basename(x).split("_")[0] for x in mriqc_files]
    mriqc_ids_lst = set(mriqc_ids_lst)

    # Get completed fmriprep
    fmriprep_files = sorted(
        glob(op.join(fmriprep_dir, "sub-*", session, "func", "sub-*_task-rest*_bold*"))
    )
    fmriprep_ids_lst = [op.basename(x).split("_")[0] for x in fmriprep_files]
    fmriprep_ids_lst = set(fmriprep_ids_lst)

    # Get completed denoising
    denoising_files = sorted(
        glob(op.join(denoising_dir, "sub-*", session, "func", "sub-*_task-rest*_bold.nii.gz"))
    )
    denoising_ids_lst = [op.basename(x).split("_")[0] for x in denoising_files]
    denoising_ids_lst = set(denoising_ids_lst)

    # Get completed rsfc
    rsfc_files = sorted(
        glob(op.join(rsfc_dir, "sub-*", session, "func", "sub-*_task-rest*_bucketREML+tlrc.BRIK"))
    )
    rsfc_ids_lst = [op.basename(x).split("_")[0] for x in rsfc_files]
    rsfc_ids_lst = set(rsfc_ids_lst)

    completion_df = pd.DataFrame()
    mriqc_lst = []
    fmriprep_lst = []
    denoising_lst = []
    rsfc_lst = []
    for participant_id in participant_ids:
        if participant_id in fmriprep_ids_lst:
            fmriprep_lst.append(1)
        else:
            fmriprep_lst.append(0)
        if participant_id in mriqc_ids_lst:
            mriqc_lst.append(1)
        else:
            mriqc_lst.append(0)
        if participant_id in denoising_ids_lst:
            denoising_lst.append(1)
        else:
            denoising_lst.append(0)
        if participant_id in rsfc_ids_lst:
            rsfc_lst.append(1)
        else:
            rsfc_lst.append(0)

    completion_df["participant_id"] = participant_ids
    completion_df["fMRIPrep"] = fmriprep_lst
    completion_df["MRIQC"] = mriqc_lst
    completion_df["Denoising"] = denoising_lst
    completion_df["RSFC"] = rsfc_lst
    completion_df.to_csv(op.join(fmriprep_dir, "..", "completion.tsv"), sep="\t", index=False)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
