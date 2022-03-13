import argparse
import json
import os
import os.path as op
import sys
from glob import glob
from shutil import copyfile

import numpy as np
import pandas as pd

sys.path.append("/code")
from utils import enhance_censoring, fd_censoring, get_nvol, run_command


def _get_parser():
    parser = argparse.ArgumentParser(description="Run 3dTproject in fmriprep derivatives")
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
        "--subject",
        dest="subject",
        required=True,
        help="Subject identifier, with the sub- prefix.",
    )
    parser.add_argument(
        "--sessions",
        dest="sessions",
        default=[None],
        required=False,
        nargs="+",
        help="Sessions identifier, with the ses- prefix.",
    )
    parser.add_argument(
        "--space",
        dest="space",
        default="MNI152NLin2009cAsym",
        required=False,
        help="Standard space, MNI152NLin2009cAsym",
    )
    parser.add_argument(
        "--fd_thresh",
        dest="fd_thresh",
        default=0.35,
        required=False,
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
        default=4,
        required=False,
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


def add_outlier(mriqc_dir, prefix):
    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")
    runs_to_exclude = runs_to_exclude_df["bids_name"].tolist()

    if prefix in runs_to_exclude:
        print(f"\t\t\t{prefix} already in runs_to_exclude.tsv")
    else:
        runs_to_exclude.append(prefix)
        new_runs_to_exclude_df = pd.DataFrame()
        new_runs_to_exclude_df["bids_name"] = runs_to_exclude
        new_runs_to_exclude_df.to_csv(
            op.join(mriqc_dir, f"runs_to_exclude.tsv"), sep="\t", index=False
        )


def nuisance_reg(
    preproc_fn, dummy_scans, denoised_fn, regressor_fn, mask_fn, smooth=False, band_pass=False
):
    cmd = f"3dTproject \
                -input {preproc_fn}[{dummy_scans}..$] \
                -polort 1 \
                -prefix {denoised_fn} \
                -ort {regressor_fn} \
                -mask {mask_fn}"
    if smooth:
        cmd = cmd + " -blur 6"
    if band_pass:
        cmd = cmd + " -passband 0.01 0.10"
    print(f"\t\t{cmd}", flush=True)
    os.system(cmd)


def afni2nifti(afni_fn, nifti_fn):
    cmd = f"3dAFNItoNIFTI \
                -prefix {nifti_fn} \
                {afni_fn}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def get_reho(denoised_fn, reho_fn, mask_fn):
    cmd = f"3dReHo \
                -inset {denoised_fn} \
                -prefix {reho_fn} \
                -nneigh 27 \
                -mask {mask_fn}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def rsfc_metrics(denoised_fn, rsfc_fn, mask_fn):
    cmd = f"3dRSFC \
                -input {denoised_fn} \
                -prefix {rsfc_fn} \
                -band 0 99999 \
                -nodetrend \
                -mask {mask_fn}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def power_spectrum(denoised_fn, rsfc_fn, censor_fn, mask_fn):
    cmd = f"3dLombScargle \
                -inset {denoised_fn} \
                -prefix {rsfc_fn} \
                -censor_1D {censor_fn} \
                -mask {mask_fn} \
                -nifti"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def rsfc_spectrum2metrics(rsfc_fn, mask_fn):
    cmd = f"3dAmpToRSFC \
                -in_amp {rsfc_fn}_amp.nii.gz \
                -prefix {rsfc_fn} \
                -band 0.01  0.1 \
                -mask {mask_fn} \
                -nifti"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def normalize_metric(metric_nifti_file, metric_norm_file, mask_fn):
    cmd = f"fslstats {metric_nifti_file} -M"
    print(f"\t\t\t\t{cmd}", flush=True)
    meanMetric = run_command(cmd)

    cmd = f"fslstats {metric_nifti_file} -S"
    print(f"\t\t\t\t{cmd}", flush=True)
    stdMetric = run_command(cmd)

    cmd = f"fslmaths \
                {metric_nifti_file} \
                -sub {meanMetric} \
                -div {stdMetric} \
                -mul {mask_fn} \
                {metric_norm_file}"
    print(f"\t\t\t\t{cmd}", flush=True)
    os.system(cmd)


def run_3dtproject(
    mriqc_dir, preproc_file, mask_file, confounds_file, dummy_scans, fd_thresh, out_dir, desc_list
):
    preproc_name = op.basename(preproc_file)
    prefix = preproc_name.split("desc-")[0].rstrip("_")
    preproc_json_file = preproc_file.replace(".nii.gz", ".json")

    # Determine output files
    denoised_file = op.join(out_dir, f"{prefix}_desc-temp_bold.nii.gz")
    # cens_file = op.join(out_dir, f"{prefix}_desc-tempCens_bold.nii.gz")
    reho_file = op.join(out_dir, f"{prefix}_desc-REHO_REHO")
    reho_norm_file = op.join(out_dir, f"{prefix}_desc-REHOnorm_REHO.nii.gz")
    rsfc_file = op.join(out_dir, f"{prefix}_desc-RSFC")
    rsfc_norm_file = op.join(out_dir, f"{prefix}_desc-RSFCnorm")
    denoisedFilt_file = op.join(out_dir, f"{prefix}_desc-tempFilt_bold.nii.gz")
    denoisedFiltSM_file = op.join(out_dir, f"{prefix}_desc-tempFiltSM6_bold.nii.gz")
    censFilt_file = op.join(out_dir, f"{prefix}_desc-{desc_list[0]}_bold.nii.gz")
    censFiltSM_file = op.join(out_dir, f"{prefix}_desc-{desc_list[1]}_bold.nii.gz")

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
    fd_before = 1
    fd_contig = 0
    fd_after = 1
    censor_file = op.join(out_dir, f"{prefix}_censoring{fd_thresh}.1D")
    if not op.exists(censor_file):
        fd_cens = fd_censoring(confounds_file, fd_thresh)
        censor_data = enhance_censoring(
            fd_cens, n_contig=fd_contig, n_before=fd_before, n_after=fd_after
        )[dummy_scans:]
        np.savetxt(censor_file, censor_data, fmt="%d")
        tr_keep = np.where(censor_data == 1)[0].tolist()
    else:
        tr_censor = pd.read_csv(censor_file, header=None)
        tr_keep = tr_censor.index[tr_censor[0] == 1].tolist()

    exclude = False
    # Add runs with < 100 volumes to outlier file
    if len(tr_keep) < 100:
        exclude = True
        run_name = preproc_name.split("_space-")[0]
        print(f"\t\tVolumes={len(tr_keep)}, adding run {run_name} to outliers", flush=True)
        add_outlier(mriqc_dir, run_name)

    # Add preproc runs < 375 volumes to outlier file
    preproc_nvol = get_nvol(preproc_file)
    if preproc_nvol < 365:
        exclude = True
        run_name = preproc_name.split("_space-")[0]
        print(f"\t\tVolumes={preproc_nvol}, adding run {run_name} to outliers", flush=True)
        add_outlier(mriqc_dir, run_name)

    # Denoise + band pass filter
    if (not op.exists(denoisedFilt_file)) and (not op.exists(censFilt_file)) and (not exclude):
        nuisance_reg(
            preproc_file,
            dummy_scans,
            denoisedFilt_file,
            regressor_file,
            mask_file,
            smooth=False,
            band_pass=True,
        )
    if (op.exists(denoisedFilt_file)) and (not op.exists(censFilt_file)):
        cmd = f"3dTcat -prefix {censFilt_file} {denoisedFilt_file}'{tr_keep}'"
        print(f"\t\t{cmd}", flush=True)
        os.system(cmd)
        os.remove(denoisedFilt_file)

    # Denoise + band pass filter + smoothing
    if (not op.exists(denoisedFiltSM_file)) and (not op.exists(censFiltSM_file)) and (not exclude):
        nuisance_reg(
            preproc_file,
            dummy_scans,
            denoisedFiltSM_file,
            regressor_file,
            mask_file,
            smooth=True,
            band_pass=True,
        )
    if (op.exists(denoisedFiltSM_file)) and (not op.exists(censFiltSM_file)):
        cmd = f"3dTcat -prefix {censFiltSM_file} {denoisedFiltSM_file}'{tr_keep}'"
        print(f"\t\t{cmd}", flush=True)
        os.system(cmd)
        os.remove(denoisedFiltSM_file)

    # Calculate ReHo.
    reho_afniH_file = f"{reho_file}+tlrc.HEAD"
    reho_afniB_file = f"{reho_file}+tlrc.BRIK"
    reho_nifti_file = f"{reho_file}.nii.gz"
    if (not op.exists(reho_nifti_file)) and (op.exists(censFilt_file)):
        get_reho(censFilt_file, reho_file, mask_file)
        afni2nifti(reho_afniH_file, reho_nifti_file)
        os.remove(reho_afniH_file)
        os.remove(reho_afniB_file)
        # Add Normalization
        normalize_metric(reho_nifti_file, reho_norm_file, mask_file)
        os.remove(reho_nifti_file)

    # Calculate ALFF, mALFF, fALFF, RSFA, etc.
    metrics = ["ALFF", "FALFF", "FRSFA", "MALFF", "MRSFA", "RSFA"]
    if (not op.exists(denoised_file)) and (not exclude):
        nuisance_reg(
            preproc_file,
            dummy_scans,
            denoised_file,
            regressor_file,
            mask_file,
            smooth=False,
            band_pass=False,
        )
    amp_file = f"{rsfc_file}_amp.nii.gz"
    if (not op.exists(amp_file)) and (op.exists(denoised_file)):
        power_spectrum(denoised_file, rsfc_file, censor_file, mask_file)
        os.remove(denoised_file)

    fALFF_file = f"{rsfc_file}_FALFF.nii.gz"
    if (not op.exists(fALFF_file)) and (op.exists(amp_file)):
        rsfc_spectrum2metrics(rsfc_file, mask_file)
        # Normalize metrics
        for metric in metrics:
            metric_file = f"{rsfc_file}_{metric}.nii.gz"
            metric_norm_file = f"{rsfc_norm_file}_{metric}.nii.gz"
            normalize_metric(metric_file, metric_norm_file, mask_file)
            os.remove(metric_file)

    """
    if (op.exists(denoised_file)) and (not op.exists(cens_file)):
        cmd = f"3dTcat -prefix {cens_file} {denoised_file}'{tr_keep}'"
        print(f"\t\t{cmd}", flush=True)
        os.system(cmd)
        os.remove(denoised_file)
    if op.exists(cens_file):
        rsfc_metrics(cens_file, rsfc_file, mask_file)
    """

    # Create json files with Sources and Description fields
    # Load metadata for writing out later and TR now
    if (op.exists(censFilt_file)) and (op.exists(censFiltSM_file)):
        with open(preproc_json_file, "r") as fo:
            json_info = json.load(fo)
        json_info["Sources"] = [censFilt_file, mask_file, regressor_file]

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


def main(
    mriqc_dir,
    preproc_dir,
    clean_dir,
    subject,
    sessions,
    space,
    fd_thresh,
    dummy_scans,
    desc_list,
    n_jobs,
):
    """Run denoising workflows on a given dataset."""
    # Taken from Taylor's pipeline: https://github.com/ME-ICA/ddmra
    fd_thresh = float(fd_thresh)
    dummy_scans = int(dummy_scans)
    os.system(f"export OMP_NUM_THREADS={n_jobs}")

    if sessions[0] is None:
        temp_ses = glob(op.join(clean_dir, subject, "ses-*"))
        if len(temp_ses) > 0:
            sessions = [op.basename(x) for x in temp_ses]

    for session in sessions:
        if session is not None:
            preproc_subj_func_dir = op.join(preproc_dir, subject, session, "func")
            nuis_subj_dir = op.join(clean_dir, subject, session, "func")
        else:
            preproc_subj_func_dir = op.join(preproc_dir, subject, "func")
            nuis_subj_dir = op.join(clean_dir, subject, "func")

        # Collect important files
        confounds_files = sorted(
            glob(op.join(preproc_subj_func_dir, "*task-rest*_desc-confounds_timeseries.tsv"))
        )
        preproc_files = sorted(
            glob(
                op.join(
                    preproc_subj_func_dir, f"*task-rest*_space-{space}*_desc-preproc_bold.nii.gz"
                )
            )
        )
        mask_files = sorted(
            glob(
                op.join(
                    preproc_subj_func_dir, f"*task-rest*_space-{space}*_desc-brain_mask.nii.gz"
                )
            )
        )
        assert len(preproc_files) == len(confounds_files)
        assert len(preproc_files) == len(mask_files)
        assert len(desc_list) == 2

        if len(preproc_files) > 0:
            os.makedirs(nuis_subj_dir, exist_ok=True)

        # ###################
        # Nuisance Regression
        # ###################
        for file, preproc_file in enumerate(preproc_files):
            mask_name = os.path.basename(mask_files[file])
            mask_file = op.join(nuis_subj_dir, mask_name)
            copyfile(mask_files[file], mask_file)

            print(f"\tProcessing {subject} files:", flush=True)
            print(f"\t\tDenoising: {preproc_file}", flush=True)
            print(f"\t\tMask:      {mask_file}", flush=True)
            print(f"\t\tConfound:  {confounds_files[file]}", flush=True)
            run_3dtproject(
                mriqc_dir,
                preproc_file,
                mask_file,
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
