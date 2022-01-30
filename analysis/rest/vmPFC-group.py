import argparse
import os
import os.path as op
from glob import glob

import nibabel as nib
import pandas as pd
from nilearn import masking


def _get_parser():
    parser = argparse.ArgumentParser(description="Run group analysis")
    parser.add_argument(
        "--mriqc_dir",
        dest="mriqc_dir",
        required=True,
        help="Path to MRIQC directory",
    )
    parser.add_argument(
        "--preproc_dir",
        dest="preproc_dir",
        required=True,
        help="Path to fMRIPrep directory",
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
        help="Session identifier, with the ses- prefix.",
    )
    parser.add_argument(
        "--n_jobs",
        dest="n_jobs",
        required=True,
        help="CPUs",
    )
    return parser


def main(mriqc_dir, preproc_dir, rsfc_dir, session, n_jobs):
    """Run group analysis workflows on a given dataset."""
    os.system(f"export OMP_NUM_THREADS={n_jobs}")
    space = "MNI152NLin2009cAsym"
    if session is not None:
        preproc_subj_func_dir = op.join(preproc_dir, "*", session, "func")
        rsfc_subj_dir = op.join(rsfc_dir, "*", session, "func")
    else:
        preproc_subj_func_dir = op.join(preproc_dir, "*", "func")
        rsfc_subj_dir = op.join(rsfc_dir, "*", "func")

    rsfc_group_dir = op.join(rsfc_dir, "group")
    os.makedirs(rsfc_group_dir, exist_ok=True)

    # Collect important files
    briks_files = sorted(
        glob(op.join(rsfc_subj_dir, f"*task-rest*_space-{space}*_desc-norm_bucketREML+tlrc.HEAD"))
    )
    mask_files = sorted(
        glob(op.join(preproc_subj_func_dir, f"*task-rest*_space-{space}*_desc-brain_mask.nii.gz"))
    )

    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")
    runs_to_exclude = (
        runs_to_exclude_df["bids_name"].str.replace("run-0", "run-").str.rstrip("_bold")
    ).tolist()
    prefixes_tpl = tuple(runs_to_exclude)
    clean_briks_files = [x for x in briks_files if not op.basename(x).startswith(prefixes_tpl)]
    clean_mask_files = [x for x in mask_files if not op.basename(x).startswith(prefixes_tpl)]

    print(len(clean_briks_files), len(clean_mask_files))
    assert len(clean_briks_files) == len(clean_mask_files)

    with open(op.join(rsfc_group_dir, "rest-group-briks.txt"), "w") as fo:
        for tmp_brik_fn in clean_briks_files:
            fo.write(f"{tmp_brik_fn}\n")

    # Create group mask
    group_mask = masking.intersect_masks(clean_mask_files, threshold=0.5)
    group_mask_fn = op.join(
        rsfc_group_dir, f"sub-group_{session}_task-rest_space-{space}_desc-brain_mask.nii.gz"
    )
    nib.save(group_mask, group_mask_fn)

    label_bucket_dict = {
        "Cluster1": 1,
        "Cluster2": 4,
        "Cluster3": 7,
        "Cluster4": 10,
        "Cluster5": 13,
        "Cluster6": 16,
    }

    # Calculate subject level average connectivity matrix


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
