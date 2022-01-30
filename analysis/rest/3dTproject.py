import argparse
import json
import os
import os.path as op
import sys
from glob import glob

import numpy as np
import pandas as pd

sys.path.append("/home/data/abcd/code/abcd_fmriprep-analysis")
from utils import enhance_censoring, fd_censoring


def _get_parser():
    parser = argparse.ArgumentParser(description="Run 3dTproject in fmriprep derivatives")
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
        help="Path to output directory",
    )
    parser.add_argument(
        "--subject",
        dest="subject",
        required=True,
        help="Subject identifier, with the sub- prefix.",
    )
    parser.add_argument(
        "--session",
        dest="session",
        required=True,
        help="Session identifier, with the ses- prefix.",
    )
    parser.add_argument(
        "--fd_thresh",
        dest="fd_thresh",
        required=True,
        help="FD threshold",
    )
    parser.add_argument(
        "--dummy_scans",
        dest="dummy_scans",
        required=True,
        help="Dummy Scans",
    )
    parser.add_argument(
        "--desc_list",
        dest="desc_list",
        required=True,
        nargs="+",
        help="Name of the output files in the order [Clean, Clean + Smooth]",
    )
    parser.add_argument(
        "--n_jobs",
        dest="n_jobs",
        required=True,
        help="CPUs",
    )
    return parser


def get_motionpar(confounds_file, derivatives=None):
    confounds_df = pd.read_csv(confounds_file, sep="\t")
    if derivatives:
        motion_labels = [
            "trans_x",
            "trans_x_derivative1",
            "trans_y",
            "trans_y_derivative1",
            "trans_z",
            "trans_z_derivative1",
            "rot_x",
            "rot_x_derivative1",
            "rot_y",
            "rot_y_derivative1",
            "rot_z",
            "rot_z_derivative1",
        ]
    else:
        motion_labels = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
    motion_regressors = confounds_df[motion_labels].values
    return motion_regressors


# Taken from Cody's pipeline
def get_acompcor(confounds_file):
    print("\t\tGet aCompCor")
    confounds_json_file = confounds_file.replace(".tsv", ".json")
    confounds_df = pd.read_csv(confounds_file, sep="\t")
    with open(confounds_json_file) as json_file:
        data = json.load(json_file)
    w_comp_cor = sorted([x for x in data.keys() if "w_comp_cor" in x])
    c_comp_cor = sorted([x for x in data.keys() if "c_comp_cor" in x])
    # for muschelli 2014
    acompcor_list_CSF = [x for x in c_comp_cor if data[x]["Mask"] == "CSF"]
    acompcor_list_CSF = acompcor_list_CSF[0:3]
    acompcor_list_WM = [x for x in w_comp_cor if data[x]["Mask"] == "WM"]
    acompcor_list_WM = acompcor_list_WM[0:3]
    acompcor_list = []
    acompcor_list.extend(acompcor_list_CSF)
    acompcor_list.extend(acompcor_list_WM)

    print(f"\t\t\tComponents: {acompcor_list}", flush=True)
    acompcor_arr = confounds_df[acompcor_list].values

    return acompcor_arr


def keep_trs(confounds_file, qc_thresh):
    print("\tGet TRs to censor")
    confounds_df = pd.read_csv(confounds_file, sep="\t")
    qc_arr = confounds_df["framewise_displacement"].values
    qc_arr = np.nan_to_num(qc_arr, 0)
    threshold = 3

    mask = qc_arr >= qc_thresh

    K = np.ones(threshold)
    dil = np.convolve(mask, K, mode="same") >= 1
    dil_erd = np.convolve(dil, K, mode="same") >= threshold

    prop_incl = np.sum(dil_erd) / qc_arr.shape[0]
    print(f"\t\tPecentage of TRS flagged {round(prop_incl*100,2)}", flush=True)
    out = np.ones(qc_arr.shape[0])
    out[dil_erd] = 0
    return out


def run_3dtproject(
    preproc_file, mask_file, confounds_file, dummy_scans, fd_thresh, out_dir, desc_list
):
    preproc_name = op.basename(preproc_file)
    prefix = preproc_name.split("desc-")[0].rstrip("_")
    preproc_json_file = preproc_file.replace(".nii.gz", ".json")

    # Determine output files
    denoised_file = op.join(out_dir, f"{prefix}_desc-temp_bold.nii.gz")
    denoisedSM_file = op.join(out_dir, f"{prefix}_desc-tempSM6_bold.nii.gz")
    cens_file = op.join(out_dir, f"{prefix}_desc-{desc_list[0]}_bold.nii.gz")
    censSM_file = op.join(out_dir, f"{prefix}_desc-{desc_list[1]}_bold.nii.gz")

    # Create regressor file
    regressor_file = op.join(out_dir, f"{prefix}_regressors.1D")
    if not op.exists(regressor_file):
        # Create regressor matrix
        motionpar = get_motionpar(confounds_file, derivatives=True)
        acompcor = get_acompcor(confounds_file)
        nuisance_regressors = np.column_stack((motionpar, acompcor))

        # Some fMRIPrep nuisance regressors have NaN in the first row (e.g., derivatives)
        nuisance_regressors = np.nan_to_num(nuisance_regressors, 0)
        nuisance_regressors = np.delete(nuisance_regressors, range(dummy_scans), axis=0)
        np.savetxt(regressor_file, nuisance_regressors, fmt="%.5f")

    # Create censoring file
    myCensoring = False
    fd_before = 1
    fd_contig = 0
    fd_after = 1
    censor_file = op.join(out_dir, f"{prefix}_censoring{fd_thresh}.1D")
    if not op.exists(censor_file):
        if myCensoring:
            censor_data = keep_trs(confounds_file, fd_thresh)[dummy_scans:]
        else:
            fd_cens = fd_censoring(confounds_file, fd_thresh)
            censor_data = enhance_censoring(
                fd_cens, n_contig=fd_contig, n_before=fd_before, n_after=fd_after
            )[dummy_scans:]
        np.savetxt(censor_file, censor_data, fmt="%d")
        tr_keep = np.where(censor_data == 1)[0].tolist()
    else:
        tr_censor = pd.read_csv(censor_file, header=None)
        tr_keep = tr_censor.index[tr_censor[0] == 1].tolist()

    if (not op.exists(denoised_file)) and (not op.exists(cens_file)):
        cmd = f"3dTproject \
                -input {preproc_file}[{dummy_scans}..$] \
                -polort 1 \
                -prefix {denoised_file} \
                -ort {regressor_file} \
                -passband 0.01 0.10 \
                -mask {mask_file}"
        print(f"\t\t{cmd}", flush=True)
        os.system(cmd)
    if not op.exists(cens_file):
        cmd = f"3dTcat -prefix {cens_file} {denoised_file}'{tr_keep}'"
        print(f"\t\t{cmd}", flush=True)
        print(f"\t\t\tKeeping {len(tr_keep)} TRs", flush=True)
        os.system(cmd)
        os.remove(denoised_file)

    if (not op.exists(denoisedSM_file)) and (not op.exists(censSM_file)):
        cmd = f"3dTproject \
                -input {preproc_file}[{dummy_scans}..$] \
                -polort 1 \
                -blur 6 \
                -prefix {denoisedSM_file} \
                -ort {regressor_file} \
                -passband 0.01 0.10 \
                -mask {mask_file}"
        print(f"\t\t{cmd}", flush=True)
        os.system(cmd)
    if not op.exists(censSM_file):
        cmd = f"3dTcat -prefix {censSM_file} {denoisedSM_file}'{tr_keep}'"
        print(f"\t\t{cmd}", flush=True)
        print(f"\t\t\tKeeping {len(tr_keep)} TRs", flush=True)
        os.system(cmd)
        os.remove(denoisedSM_file)

    # Create json files with Sources and Description fields
    # Load metadata for writing out later and TR now
    with open(preproc_json_file, "r") as fo:
        json_info = json.load(fo)
    json_info["Sources"] = [cens_file, mask_file, regressor_file]

    SUFFIXES = {
        "desc-aCompCorCens_bold": (
            "Denoising with an aCompCor regression model including 3 PCA components from"
            "WM and 3 from CSF deepest white matter, 6 motion parameters, and first"
            "temporal derivatives of motion parameters."
        ),
        "desc-aCompCorSM6Cens_bold": (
            "Denoising with an aCompCor regression model including 3 PCA components from"
            "WM and 3 from CSF deepest white matter, 6 motion parameters, and first"
            "temporal derivatives of motion parameters. Spatial smoothing was applied."
        ),
    }
    for suffix, description in SUFFIXES.items():
        nii_file = op.join(out_dir, f"{prefix}_{suffix}.nii.gz")
        assert op.isfile(nii_file)

        suff_json_file = op.join(out_dir, f"{prefix}_{suffix}.json")
        json_info["Description"] = description
        with open(suff_json_file, "w") as fo:
            json.dump(json_info, fo, sort_keys=True, indent=4)


def main(preproc_dir, clean_dir, subject, session, fd_thresh, dummy_scans, desc_list, n_jobs):
    """Run denoising workflows on a given dataset."""
    # Taken from Taylor's pipeline: https://github.com/ME-ICA/ddmra
    space = "MNI152NLin2009cAsym"
    fd_thresh = float(fd_thresh)
    dummy_scans = int(dummy_scans)
    os.system(f"export OMP_NUM_THREADS={n_jobs}")

    if session is not None:
        preproc_subj_func_dir = op.join(preproc_dir, subject, session, "func")
        nuis_subj_dir = op.join(clean_dir, subject, session, "func")
    else:
        preproc_subj_func_dir = op.join(preproc_dir, subject, "func")
        nuis_subj_dir = op.join(clean_dir, subject, "func")

    os.makedirs(nuis_subj_dir, exist_ok=True)

    # Collect important files
    confounds_files = sorted(
        glob(op.join(preproc_subj_func_dir, "*task-rest*_desc-confounds_timeseries.tsv"))
    )
    preproc_files = sorted(
        glob(
            op.join(preproc_subj_func_dir, f"*task-rest*_space-{space}*_desc-preproc_bold.nii.gz")
        )
    )
    mask_files = sorted(
        glob(op.join(preproc_subj_func_dir, f"*task-rest*_space-{space}*_desc-brain_mask.nii.gz"))
    )
    assert len(preproc_files) == len(confounds_files)
    assert len(preproc_files) == len(mask_files)
    assert len(desc_list) == 2

    # ###################
    # Nuisance Regression
    # ###################
    for file, preproc_file in enumerate(preproc_files):
        print(f"\tProcessing {subject} {session} files:", flush=True)
        print(f"\t\tDenoising: {preproc_file}", flush=True)
        print(f"\t\tMask:      {mask_files[file]}", flush=True)
        print(f"\t\tConfound:  {confounds_files[file]}", flush=True)
        run_3dtproject(
            preproc_file,
            mask_files[file],
            confounds_files[file],
            dummy_scans,
            fd_thresh,
            nuis_subj_dir,
            desc_list,
        )


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
