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
        help="Path to fMRIPrep directory",
    )
    parser.add_argument(
        "--out",
        dest="out",
        required=True,
        help="Path to fMRIPrep directory",
    )
    return parser


def main(dset, out):
    """Generate list of subject ID from participants.tsv but not in dset"""
    downloaded_dirs = sorted(glob(op.join(dset, "sub-*")))
    downloaded_ids = [op.basename(x) for x in downloaded_dirs]
    downloaded_ids = tuple(downloaded_ids)

    participant_ids_fn = op.join(dset, "participants.tsv")
    participant_ids = pd.read_csv(participant_ids_fn, sep="\t")["participant_id"].tolist()

    output_ids = [x for x in participant_ids if not x.startswith(downloaded_ids)]

    with open(out, "w") as fo:
        for output_id in output_ids:
            fo.write(f"{output_id}\n")


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
