import argparse
import os
import os.path as op
import string
from glob import glob

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import image, masking


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
        "--clean_dir",
        dest="clean_dir",
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
        help="Session identifier, with the ses- prefix.",
    )
    parser.add_argument(
        "--template",
        dest="template",
        default=None,
        required=False,
        help="Template to resample data",
    )
    parser.add_argument(
        "--template_mask",
        dest="template_mask",
        default=None,
        required=False,
        help="Template to resample masks",
    )
    parser.add_argument(
        "--group",
        dest="group",
        default="full",
        required=False,
        help="group label",
    )
    parser.add_argument(
        "--roi_lst",
        dest="roi_lst",
        nargs="+",
        required=True,
        help="ROI label list",
    )
    parser.add_argument(
        "--roi",
        dest="roi",
        required=True,
        help="ROI label",
    )
    parser.add_argument(
        "--n_jobs",
        dest="n_jobs",
        required=True,
        help="CPUs",
    )
    return parser


def afni2nifti(afni_fn, nifti_fn):
    cmd = f"3dAFNItoNIFTI \
                -prefix {nifti_fn} \
                {afni_fn}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def conn_resample(roi_in, roi_out, template):

    cmd = f"3dresample \
            -prefix {roi_out} \
            -master {template} \
            -inset {roi_in}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def remove_ouliers(mriqc_dir, briks_files, mask_files):

    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")
    runs_to_exclude = runs_to_exclude_df["bids_name"].tolist()
    prefixes_tpl = tuple(runs_to_exclude)

    clean_briks_files = [x for x in briks_files if not op.basename(x).startswith(prefixes_tpl)]
    clean_mask_files = [x for x in mask_files if not op.basename(x).startswith(prefixes_tpl)]

    return clean_briks_files, clean_mask_files


def remove_families(participants_df, briks_files, mask_files):

    subjects_to_exclude = participants_df.loc[
        participants_df["FamConf"] == 1, "participant_id"
    ].tolist()
    prefixes_tpl = tuple(subjects_to_exclude)

    clean_briks_files = [x for x in briks_files if not op.basename(x).startswith(prefixes_tpl)]
    clean_mask_files = [x for x in mask_files if not op.basename(x).startswith(prefixes_tpl)]

    return clean_briks_files, clean_mask_files


def remove_missingdat(covariates_df, briks_files, mask_files):
    covariates_df = covariates_df.replace([999, 777], np.nan)
    covariates_df = covariates_df.dropna()
    subjects_to_keep = covariates_df["participant_id"].tolist()

    prefixes_tpl = tuple(subjects_to_keep)

    clean_briks_files = [x for x in briks_files if op.basename(x).startswith(prefixes_tpl)]
    clean_mask_files = [x for x in mask_files if op.basename(x).startswith(prefixes_tpl)]

    return clean_briks_files, clean_mask_files


def subj_ave_roi(clean_subj_dir, subj_briks_files, subjAve_roi_briks_file, roi_idx):
    n_runs = len(subj_briks_files)
    letters = list(string.ascii_lowercase[0:n_runs])

    subj_roi_briks_files = [
        "-{0} {1}'[{2}]'".format(letters[idx], x.split(".HEAD")[0], roi_idx)
        for idx, x in enumerate(subj_briks_files)
    ]
    input_str = " ".join(subj_roi_briks_files)

    # Get weights from number of volumes left in the time series
    weight_lst = []
    for subj_briks_file in subj_briks_files:
        prefix = op.basename(subj_briks_file).split("desc-")[0].rstrip("_")
        censor_files = glob(op.join(clean_subj_dir, f"{prefix}_censoring*.1D"))
        assert len(censor_files) == 1
        censor_file = censor_files[0]
        tr_censor = pd.read_csv(censor_file, header=None)
        tr_left = len(tr_censor.index[tr_censor[0] == 1].tolist())
        weight_lst.append(tr_left)
    # Normalize weights
    weight_norm_lst = [float(x) / sum(weight_lst) for x in weight_lst]

    # Conform equation (a*w[1]+b*w[2]+...)/n_runs
    equation = [f"{letters[idx]}*{round(w,4)}" for idx, w in enumerate(weight_norm_lst)]
    if n_runs > 1:
        equation_str = "+".join(equation)
        exp_str = f"({equation_str})/{n_runs}"
    else:
        exp_str = f"{equation[0]}"

    cmd = f"3dcalc {input_str} -expr '{exp_str}' -prefix {subjAve_roi_briks_file}"
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
    mean_fd = np.around(mean_fd, 4)
    with open(subj_mean_fd_file, "w") as fo:
        fo.write(f"{mean_fd}")

    return mean_fd


def writearg_1sample(onettest_args_fn):
    with open(onettest_args_fn, "w") as fo:
        fo.write("-setA Group\n")


def append2arg_1sample(subject, subjAve_roi_briks_file, onettest_args_fn):
    brik_id = "{brik}'[0]'".format(brik=subjAve_roi_briks_file)
    with open(onettest_args_fn, "a") as fo:
        fo.write(f"{subject} {brik_id}\n")


def get_setAB(subject, subjAve_roi_briks_file, participants_df, setA, setB):
    sub_df = participants_df[participants_df["participant_id"] == subject]
    brik_id = "{brik}'[0]'".format(brik=subjAve_roi_briks_file)
    if sub_df["CProb1"].values[0] >= 0.7:
        setA.append("{sub_id} {brik_id}\n".format(sub_id=subject, brik_id=brik_id))
    elif sub_df["CProb2"].values[0] >= 0.7:
        setB.append("{sub_id} {brik_id}\n".format(sub_id=subject, brik_id=brik_id))
    else:
        pass
    return setA, setB


def writearg_2sample(setA, setB, twottest_args_fn):
    setA = "".join(setA)
    setB = "".join(setB)
    with open(twottest_args_fn, "w") as fo:
        fo.write(f"-setA Bicult\n{setA}\n-setB Detached\n{setB}\n")


def writecov_1sample(onettest_cov_fn):
    cov_labels = [
        "subject",
        "age_p",
        "age_c",
        "site",
        "education",
        "income",
        "nativity_p",
        "nativity_c",
        "gender_p",
        "gender_c",
    ]
    # "FD",
    with open(onettest_cov_fn, "w") as fo:
        fo.write("{}\n".format(" ".join(cov_labels)))


def append2cov_1sample(subject, mean_fd, behavioral_df, onettest_cov_fn):
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
    cov_variables = [
        subject,
        age_p,
        age_c,
        site,
        education,
        income,
        nativity_p,
        nativity_c,
        gender_p,
        gender_c,
    ]
    # mean_fd,
    cov_variables_str = [str(x) for x in cov_variables]
    with open(onettest_cov_fn, "a") as fo:
        fo.write("{}\n".format(" ".join(cov_variables_str)))


def run_ttest(bucket_fn, mask_fn, covariates_file, args_file, n_jobs):
    """
    with open(args_file) as file:
        arg_list = file.readlines()
    arg_list_up = [x.replace("\n", "") for x in arg_list]
    arg_list = " ".join(arg_list_up)
    """
    cmd = f"3dttest++ -prefix {bucket_fn} \
            -mask {mask_fn} \
            -Covariates {covariates_file} \
            -Clustsim {n_jobs} \
            -ETAC {n_jobs} \
            -ETAC_opt NN=2:sid=2:hpow=0:pthr=0.05,0.01,0.005,0.002,0.001:name=etac \
            -@ < {args_file}"
    # {arg_list}"
    print(f"\t\t{cmd}", flush=True)
    os.system(cmd)


def main(
    dset,
    mriqc_dir,
    preproc_dir,
    clean_dir,
    rsfc_dir,
    session,
    template,
    template_mask,
    group,
    roi_lst,
    roi,
    n_jobs,
):
    """Run group analysis workflows on a given dataset."""
    os.system(f"export OMP_NUM_THREADS={n_jobs}")
    roi_dict = {label: x * 3 + 1 for x, label in enumerate(roi_lst)}
    print(roi_dict, flush=True)
    space = "MNI152NLin2009cAsym"
    n_jobs = int(n_jobs)
    # Load important tsv files
    participants_df = pd.read_csv(op.join(dset, "participants.tsv"), sep="\t")
    covariates_df = pd.read_csv(op.join(dset, "derivatives", "covariates.tsv"), sep="\t")
    behavioral_df = pd.read_csv(
        op.join(
            dset, "derivatives", "ltnx_demo_via_lt_acspsw03_asr_cbcl_crpbi_pmq_pfe_pfes_tbss.csv"
        ),
        sep="\t",
    )

    # Define directories
    if session is not None:
        # preproc_subjs_dir = op.join(preproc_dir, "*", session, "func")
        rsfc_subjs_dir = op.join(rsfc_dir, "*", session, "func")
    else:
        # preproc_subjs_dir = op.join(preproc_dir, "*", "func")
        rsfc_subjs_dir = op.join(rsfc_dir, "*", "func")

    rsfc_group_dir = op.join(rsfc_dir, f"group-{group}")
    os.makedirs(rsfc_group_dir, exist_ok=True)

    # Collect important files
    print(rsfc_subjs_dir)
    briks_files = sorted(
        glob(op.join(rsfc_subjs_dir, f"*task-rest*_space-{space}*_desc-norm_bucketREML+tlrc.HEAD"))
    )
    mask_files = sorted(
        glob(op.join(rsfc_subjs_dir, f"*task-rest*_space-{space}*_desc-brain_mask.nii.gz"))
    )

    # Remove outliers using MRIQC metrics
    print(
        f"Initial number of runs. Briks: {len(briks_files)}, Masks: {len(mask_files)}", flush=True
    )

    clean_briks_files, clean_mask_files = remove_ouliers(mriqc_dir, briks_files, mask_files)
    print(
        f"Outliers. Briks: {len(clean_briks_files)}, Masks: {len(clean_mask_files)}",
        flush=True,
    )
    if group.startswith("nonFAM"):
        clean_briks_files, clean_mask_files = remove_families(
            participants_df, clean_briks_files, clean_mask_files
        )
    print(
        f"Siblings. Briks: {len(clean_briks_files)}, Masks: {len(clean_mask_files)}",
        flush=True,
    )

    clean_briks_files, clean_mask_files = remove_missingdat(
        covariates_df, clean_briks_files, clean_mask_files
    )
    print(
        f"Missing. Briks: {len(clean_briks_files)}, Masks: {len(clean_mask_files)}",
        flush=True,
    )
    assert len(clean_briks_files) == len(clean_mask_files)
    # clean_briks_nm = [op.basename(x).split("_space-")[0] for x in clean_briks_files]
    # clean_mask_nm = [op.basename(x).split("_space-")[0] for x in clean_mask_files]
    # clean_briks_tpl = tuple(clean_briks_nm)
    # mask_not_brik = [x for x in clean_mask_nm if not x.startswith(clean_briks_tpl)]

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
        if template_mask is None:
            for clean_mask_file in clean_mask_files:
                clean_mask_obj = image.load_img(clean_mask_file)
                if clean_mask_obj.shape[0] == 81:
                    affine, shape = clean_mask_obj.affine, clean_mask_obj.shape
                    break
        else:
            template_mask_obj = image.load_img(template_mask)
            affine, shape = template_mask_obj.affine, template_mask_obj.shape
        for clean_mask_file in clean_mask_files:
            clean_mask_img = image.load_img(clean_mask_file)
            if clean_mask_img.shape[0] != 81:
                clean_res_mask_img = image.resample_img(
                    clean_mask_img, affine, shape[:3], interpolation="nearest"
                )
                nib.save(clean_res_mask_img, clean_mask_file)

        group_mask = masking.intersect_masks(clean_mask_files, threshold=0.5)
        nib.save(group_mask, group_mask_fn)

    roi_dir = op.join(rsfc_group_dir, roi)
    os.makedirs(roi_dir, exist_ok=True)
    # Conform onettest_args_fn and twottest_args_fn
    onettest_args_fn = op.join(
        roi_dir, f"sub-group_{session}_task-rest_desc-1SampletTest{roi}_args.txt"
    )
    twottest_args_fn = op.join(
        roi_dir, f"sub-group_{session}_task-rest_desc-2SampletTest{roi}_args.txt"
    )
    if not op.exists(onettest_args_fn):
        writearg_1sample(onettest_args_fn)

    # Conform onettest_cov_fn and twottest_cov_fn
    onettest_cov_fn = op.join(
        roi_dir, f"sub-group_{session}_task-rest_desc-1SampletTest{roi}_cov.txt"
    )
    if not op.exists(onettest_cov_fn):
        writecov_1sample(onettest_cov_fn)

    setA = []
    setB = []
    # Calculate subject and ROI level average connectivity
    subjects = [op.basename(x).split("_")[0] for x in clean_briks_files]
    subjects = list(set(subjects))
    print(f"Group analysis sample size: {len(subjects)}")

    # Get template
    if template is None:
        for clean_briks_file in clean_briks_files:
            temp_template = op.join(f"{clean_briks_file}'{roi_dict[roi]}'")
            temp_template_img = image.load_img(temp_template)
            if temp_template_img.shape[0] == 81:
                template = temp_template
                print(f"Template {template}")
                break
    else:
        assert image.load_img(template).shape[0] == 81

    for subject in subjects:
        rsfc_subj_dir = op.join(rsfc_dir, subject, session, "func")
        preproc_subj_dir = op.join(preproc_dir, subject, session, "func")
        clean_subj_dir = op.join(clean_dir, subject, session, "func")
        subj_briks_files = [x for x in clean_briks_files if subject in x]

        if "run-" in subj_briks_files[0]:
            prefix = op.basename(subj_briks_files[0]).split("run-")[0].rstrip("_")
        else:
            prefix = op.basename(subj_briks_files[0]).split("space-")[0].rstrip("_")

        subjAve_roi_briks_file = op.join(
            rsfc_subj_dir,
            f"{prefix}_space-{space}_desc-ave{roi}_bucket",
        )
        subjAveRes_roi_briks_file = op.join(
            rsfc_subj_dir,
            f"{prefix}_space-{space}_desc-ave{roi}res_bucket",
        )
        subj_mean_fd_file = op.join(
            rsfc_subj_dir,
            f"{prefix}_meanFD.txt",
        )
        if not op.exists(f"{subjAve_roi_briks_file}+tlrc.BRIK"):
            subj_ave_roi(clean_subj_dir, subj_briks_files, subjAve_roi_briks_file, roi_dict[roi])

        # Resample
        subjAve_roi_briks = image.load_img(f"{subjAve_roi_briks_file}+tlrc.BRIK")
        if subjAve_roi_briks.shape[0] != 81:
            if not op.exists(f"{subjAveRes_roi_briks_file}+tlrc.BRIK"):
                conn_resample(
                    f"{subjAve_roi_briks_file}+tlrc",
                    subjAveRes_roi_briks_file,
                    template,
                )
            subjAve_roi_briks_file = subjAveRes_roi_briks_file
        if (op.exists(f"{subjAve_roi_briks_file}+tlrc.HEAD")) and (
            not op.exists(f"{subjAve_roi_briks_file}.nii.gz")
        ):
            afni2nifti(f"{subjAve_roi_briks_file}+tlrc.HEAD", f"{subjAve_roi_briks_file}.nii.gz")

        # Get subject level mean FD
        mean_fd = subj_mean_fd(preproc_subj_dir, subj_briks_files, subj_mean_fd_file)

        # Append subject specific info for onettest_args_fn
        if op.exists(onettest_args_fn):
            append2arg_1sample(subject, f"{subjAve_roi_briks_file}+tlrc.BRIK", onettest_args_fn)

        # Get setA and setB to write twottest_args_fn
        # if not op.exists(twottest_args_fn):
        setA, setB = get_setAB(
            subject, f"{subjAve_roi_briks_file}+tlrc.BRIK", participants_df, setA, setB
        )

        # Append subject specific info for onettest_cov_fn
        if op.exists(onettest_cov_fn):
            append2cov_1sample(subject, mean_fd, behavioral_df, onettest_cov_fn)

    # Write twottest_args_fn
    if not op.exists(twottest_args_fn):
        writearg_2sample(setA, setB, twottest_args_fn)

    # Statistical analysis
    # Whole-brain, one-sample t-tests
    onettest_briks_fn = op.join(
        roi_dir,
        f"sub-group_{session}_task-rest_desc-1SampletTest{roi}_briks",
    )
    # Whole-brain, two-sample t-tests
    twottest_briks_fn = op.join(
        roi_dir,
        f"sub-group_{session}_task-rest_desc-2SampletTest{roi}_briks",
    )
    ttest_briks_files = [onettest_briks_fn, twottest_briks_fn]
    covariates_files = [onettest_cov_fn, onettest_cov_fn]
    args_files = [onettest_args_fn, twottest_args_fn]

    for file, ttest_briks_fn in enumerate(ttest_briks_files):
        os.chdir(op.dirname(ttest_briks_fn))
        if not op.exists(f"{ttest_briks_fn}+tlrc.BRIK"):
            run_ttest(
                op.basename(ttest_briks_fn),
                group_mask_fn,
                covariates_files[file],
                args_files[file],
                n_jobs,
            )


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
