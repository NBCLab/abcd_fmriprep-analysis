import argparse
import os
import os.path as op
from glob import glob

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import masking


def _get_parser():
    parser = argparse.ArgumentParser(description="Run group analysis")
    parser.add_argument(
        "--dset",
        dest="dset",
        required=True,
        help="Path to BIDS directory",
    )
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


def remove_ouliers(mriqc_dir, briks_files, mask_files):

    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")
    runs_to_exclude = (
        runs_to_exclude_df["bids_name"].str.replace("run-0", "run-").str.rstrip("_bold")
    ).tolist()

    prefixes_tpl = tuple(runs_to_exclude)

    clean_briks_files = [x for x in briks_files if not op.basename(x).startswith(prefixes_tpl)]
    clean_mask_files = [x for x in mask_files if not op.basename(x).startswith(prefixes_tpl)]

    return clean_briks_files, clean_mask_files


def subj_ave_roi(subj_briks_files, subjAve_roi_briks_file, roi_idx):
    subj_roi_briks_files = [
        "{0}'[{1}]'".format(x.split(".HEAD")[0], roi_idx) for x in subj_briks_files
    ]
    subj_roi_briks_list = " ".join(subj_roi_briks_files)

    if len(subj_roi_briks_files) > 1:
        cmd = f"3dMean -prefix {subjAve_roi_briks_file} {subj_roi_briks_list}"
        print(f"\t{cmd}", flush=True)
        os.system(cmd)
    else:
        cmd = f"3dcalc -a {subj_roi_briks_files} -expr 'a' -prefix {subjAve_roi_briks_file}"
        print(f"\t{cmd}", flush=True)
        os.system(cmd)


def subj_mean_fd(preproc_subj_dir, subj_briks_files, subj_mean_fd_file):
    fd = [
        pd.read_csv(
            op.join(
                preproc_subj_dir,
                "{}_desc-confounds_timeseries.tsv".format(op.basename(x).split("_space-")[0]),
            ),
            sep="\t",
        )["framewise_displacement"].mean()
        for x in subj_briks_files
    ]
    mean_fd = np.mean(fd)
    with open(subj_mean_fd_file, "w") as fo:
        fo.write(f"{mean_fd}")

    return mean_fd


def writearg_1sample(onettest_args_fn):
    with open(onettest_args_fn, "w") as fo:
        fo.write("-setA Group\n")


def append2arg_1sample(subject, subjAve_roi_briks_file, onettest_args_fn):
    with open(onettest_args_fn, "w") as fo:
        fo.write(f"{subject} {subjAve_roi_briks_file}\n")


def get_setAB(subject, subjAve_roi_briks_file, lpa_df, setA, setB):
    sub_df = lpa_df[lpa_df["subjectkey"] == "NDAR_{}".format(subject.split("sub-NDAR")[1])]
    brik_id = "{brik}'[0]'".format(brik=subjAve_roi_briks_file)
    if sub_df["CProb1"].values[0] >= 0.8:
        setA.append("{sub_id} {brik_id}\n".format(sub_id=subject, brik_id=brik_id))
    elif sub_df["CProb2"].values[0] >= 0.8:
        setB.append("{sub_id} {brik_id}\n".format(sub_id=subject, brik_id=brik_id))
    else:
        print(sub_df)
    return setA, setB


def writearg_2sample(setA, setB, twottest_args_fn):
    setA = " ".join(setA)
    setB = " ".join(setB)
    with open(twottest_args_fn, "w") as fo:
        fo.write("-setA Bicult {setA}\n -setB Detached {setB}\n")


def writecov_1sample(onettest_cov_fn):
    with open(onettest_cov_fn) as fo:
        fo.write(
            "subject age_p age_c site FD education income nativity_p nativity_c gender_p gender_c\n"
        )


def append2cov(subject, mean_fd, behavioral_df, onettest_cov_fn):
    site_dict = {site: i for i, site in enumerate(behavioral_df["site_id_l"].unique())}
    sub_df = behavioral_df[
        behavioral_df["subjectkey"] == "NDAR_{}".format(subject.split("sub-NDAR")[1])
    ]
    sub_df = sub_df.fillna(0)
    age_p = sub_df["demo_prnt_age_v2"].values[0]
    age_c = sub_df["interview_age"].values[0]
    site = site_dict[sub_df["site_id_l"].values[0]]
    education = sub_df["demo_prnt_ed_v2"].values[0]
    income = sub_df["demo_comb_income_v2"].values[0]
    nativity_p = sub_df["demo_prnt_origin_v2"].values[0]
    nativity_c = sub_df["demo_origin_v2"].values[0]
    gender_p = sub_df["demo_prnt_gender_id_v2"].values[0]
    gender_c = sub_df["demo_gender_id_v2"].values[0]
    with open(onettest_cov_fn) as fo:
        fo.write(
            f"{subject} {age_p} {age_c} {site} {mean_fd} {education} {income} {nativity_p} {nativity_c} {gender_p} {gender_c}\n"
        )


def run_ttest(bucket_fn, mask_fn, covariates_file, args_file):
    cmd = f"3dttest++ -prefix {bucket_fn} \
            -mask {mask_fn} \
            -Covariates {covariates_file} \
            -Clustsim -@ < {args_file}"
    print(f"\t{cmd}", flush=True)
    os.system(cmd)


def main(dset, mriqc_dir, preproc_dir, rsfc_dir, session, n_jobs):
    """Run group analysis workflows on a given dataset."""
    os.system(f"export OMP_NUM_THREADS={n_jobs}")
    space = "MNI152NLin2009cAsym"
    # Load important tsv files
    participants_df = pd.read_csv(op.join(dset, "participants.tsv"), sep="\t")
    behavioral_df = pd.read_csv(
        op.join(
            dset, "derivatives", "ltnx_demo_via_lt_acspsw03_asr_cbcl_crpbi_pmq_pfe_pfes_tbss.csv"
        ),
        sep="\t",
    )
    lpa_df = pd.read_csv(op.join(dset, "derivatives", "ABCD_Accult_Share.dat"), sep="\t")
    subjects = participants_df["participant_id"].tolist()[:10]

    # Define directories
    if session is not None:
        preproc_subjs_dir = op.join(preproc_dir, "*", session, "func")
        rsfc_subjs_dir = op.join(rsfc_dir, "*", session, "func")
    else:
        preproc_subjs_dir = op.join(preproc_dir, "*", "func")
        rsfc_subjs_dir = op.join(rsfc_dir, "*", "func")

    rsfc_group_dir = op.join(rsfc_dir, "group")
    os.makedirs(rsfc_group_dir, exist_ok=True)

    # Collect important files
    briks_files = sorted(
        glob(op.join(rsfc_subjs_dir, f"*task-rest*_space-{space}*_desc-norm_bucketREML+tlrc.HEAD"))
    )
    mask_files = sorted(
        glob(op.join(preproc_subjs_dir, f"*task-rest*_space-{space}*_desc-brain_mask.nii.gz"))
    )

    # Remove outliers using MRIQC metrics
    clean_briks_files, clean_mask_files = remove_ouliers(mriqc_dir, briks_files, mask_files)
    assert len(clean_briks_files) == len(clean_mask_files)

    # Write group file
    clean_briks_fn = op.join(
        rsfc_group_dir, f"sub-group_{session}_task-rest_space-{space}_briks.txt"
    )
    if not op.exists(clean_briks_fn):
        with open(clean_briks_fn, "w") as fo:
            for tmp_brik_fn in clean_briks_files:
                fo.write(f"{tmp_brik_fn}\n")

    # Create group mask
    group_mask_fn = op.join(
        rsfc_group_dir, f"sub-group_{session}_task-rest_space-{space}_desc-brain_mask.nii.gz"
    )
    if not op.exists(group_mask_fn):
        group_mask = masking.intersect_masks(clean_mask_files, threshold=0.5)
        nib.save(group_mask, group_mask_fn)

    label_bucket_dict = {
        "ROI1": 1,
        "ROI2": 4,
        "ROI3": 7,
        "ROI4": 10,
        "ROI5": 13,
        "ROI6": 16,
    }
    for label in label_bucket_dict.keys():
        # Conform onettest_args_fn and twottest_args_fn
        onettest_args_fn = op.join(
            rsfc_group_dir, f"sub-group_{session}_task-rest_desc-1SampletTest{label}_args.txt"
        )
        twottest_args_fn = op.join(
            rsfc_group_dir, f"sub-group_{session}_task-rest_desc-2SampletTest{label}_args.txt"
        )
        if not op.exists(onettest_args_fn):
            writearg_1sample(onettest_args_fn)

        # Conform onettest_cov_fn and twottest_cov_fn
        onettest_cov_fn = op.join(
            rsfc_group_dir, f"sub-group_{session}_task-rest_desc-1SampletTest{label}_cov.txt"
        )
        if not op.exists(onettest_cov_fn):
            writecov_1sample(onettest_cov_fn)

        setA = []
        setB = []
        # Calculate subject and ROI level average connectivity
        for subject in subjects:
            rsfc_subj_dir = op.join(rsfc_dir, subject, session, "func")
            preproc_subj_dir = op.join(preproc_dir, subject, session, "func")
            subj_briks_files = [x for x in clean_briks_files if subject in x]
            assert len(subj_briks_files) > 0

            if "run-" in subj_briks_files[0]:
                prefix = op.basename(subj_briks_files[0]).split("run-")[0].rstrip("_")

            subjAve_roi_briks_file = op.join(
                rsfc_subj_dir,
                f"{prefix}_space-{space}_desc-ave{label}_bucket",
            )
            subj_mean_fd_file = op.join(
                rsfc_subj_dir,
                f"{prefix}_meanFD.txt",
            )

            if not op.exists(subjAve_roi_briks_file):
                subj_ave_roi(subj_briks_files, subjAve_roi_briks_file, label_bucket_dict[label])

            # Get subject level mean FD
            mean_fd = subj_mean_fd(preproc_subj_dir, subj_briks_files, subj_mean_fd_file)

            # Append subject specific info for onettest_args_fn and twottest_args_fn
            if not op.exists(onettest_args_fn):
                append2arg_1sample(subject, subjAve_roi_briks_file, onettest_args_fn)

            if not op.exists(twottest_args_fn):
                setA, setB = get_setAB(subject, subjAve_roi_briks_file, lpa_df, setA, setB)

            # Append subject specific info for onettest_cov_fn and twottest_cov_fn
            if not op.exists(onettest_cov_fn):
                append2cov(subject, mean_fd, behavioral_df, onettest_cov_fn)

        if not op.exists(twottest_args_fn):
            writearg_2sample(setA, setB, twottest_args_fn)

        # Statistical analysis
        # Whole-brain, one-sample t-tests
        onettest_briks_fn = op.join(
            rsfc_group_dir,
            f"sub-group_{session}_task-rest_desc-1SampletTest{label}_briks",
        )
        # Whole-brain, two-sample t-tests
        twottest_briks_fn = op.join(
            rsfc_group_dir,
            f"sub-group_{session}_task-rest_desc-2SampletTest{label}_briks",
        )
        ttest_briks_files = [onettest_briks_fn, twottest_briks_fn]
        covariates_files = [onettest_cov_fn, onettest_cov_fn]
        args_files = [onettest_args_fn, twottest_args_fn]

        for file, ttest_briks_fn in enumerate(ttest_briks_files):
            if not op.exists(ttest_briks_fn):
                run_ttest(ttest_briks_fn, group_mask_fn, covariates_files[file], args_files[file])


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
