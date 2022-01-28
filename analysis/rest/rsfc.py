import argparse
import os
import os.path as op
from glob import glob


def _get_parser():
    parser = argparse.ArgumentParser(description="Run RSFC in AFNI")
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
        help="Path to denoised data directory",
    )
    parser.add_argument(
        "--rsfc_dir",
        dest="rsfc_dir",
        required=True,
        help="Path to RSFC directory",
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
        "--desc_list",
        dest="desc_list",
        required=True,
        nargs="+",
        help="Name of the output files in the order [Clean, Clean + Smooth]",
    )
    parser.add_argument(
        "--rois",
        dest="rois",
        nargs="+",
        required=True,
        help="ROIs",
    )
    parser.add_argument(
        "--n_jobs",
        dest="n_jobs",
        required=True,
        help="CPUs",
    )
    return parser


def roi_resample(roi_in, roi_out, template):

    cmd = f"3dresample \
            -prefix {roi_out} \
            -master {template} \
            -inset {roi_in}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def ave_timeseries(mask, rs_file, rs_timeseries):
    cmd = f"3dmaskave \
            -q \
            -mask {mask} \
            {rs_file} > {rs_timeseries}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def design_matrix(rs_smooth_fn, mask_fname, num_roi, stim_info, matrix_fname, n_jobs):
    cmd = f"3dDeconvolve -input {rs_smooth_fn} \
            -x1D_stop \
            -mask {mask_fname} \
            -num_stimts {num_roi} \
            -jobs {n_jobs} \
            -svd \
            -local_times \
            -basis_normall 1 \
            {stim_info} \
            -x1D {matrix_fname}"
    print(f"\t\t{cmd}", flush=True)
    os.system(cmd)


def connectivity(matrix_fname, rs_smooth_fn, mask_fname, out_bucket):
    cmd = f"3dREMLfit \
            -matrix {matrix_fname} \
            -input {rs_smooth_fn} \
            -mask {mask_fname} \
            -fout \
            -tout \
            -Rbuck {out_bucket} \
            -verb"
    print(f"\t\t{cmd}", flush=True)
    os.system(cmd)


def norm_conn(out_bucket, out_bucket_z):
    cmd = f'3dcalc \
            -a {out_bucket}+tlrc \
            -expr "atanh(a)" \
            -prefix {out_bucket_z}'
    print(f"\t\t{cmd}", flush=True)
    os.system(cmd)


def main(preproc_dir, clean_dir, rsfc_dir, subject, session, desc_list, rois, n_jobs):
    """Run denoising workflows on a given dataset."""
    os.system(f"export OMP_NUM_THREADS={n_jobs}")
    space = "MNI152NLin2009cAsym"
    assert len(desc_list) == 2
    if session is not None:
        preproc_subj_func_dir = op.join(preproc_dir, subject, session, "func")
        clean_subj_dir = op.join(clean_dir, subject, session, "func")
        rsfc_subj_dir = op.join(rsfc_dir, subject, session, "func")
    else:
        preproc_subj_func_dir = op.join(preproc_dir, subject, "func")
        clean_subj_dir = op.join(clean_dir, subject, "func")
        rsfc_subj_dir = op.join(rsfc_dir, subject, session, "func")

    os.makedirs(rsfc_subj_dir, exist_ok=True)

    # Collect important files
    clean_subj_files = sorted(
        glob(
            op.join(clean_subj_dir, f"*task-rest*_space-{space}*_desc-{desc_list[0]}_bold.nii.gz")
        )
    )
    smooth_subj_files = sorted(
        glob(
            op.join(clean_subj_dir, f"*task-rest*_space-{space}*_desc-{desc_list[1]}_bold.nii.gz")
        )
    )
    mask_files = sorted(
        glob(op.join(preproc_subj_func_dir, f"*task-rest*_space-{space}*_desc-brain_mask.nii.gz"))
    )
    assert len(clean_subj_files) == len(smooth_subj_files)
    assert len(clean_subj_files) == len(mask_files)

    # os.makedirs(nuis_subj_dir, exist_ok=True)

    # ###################
    # RSFC
    # ###################
    for file, clean_subj_file in enumerate(clean_subj_files):
        print(f"\t Clean {clean_subj_file}", flush=True)
        print(f"\tSmooth {smooth_subj_files[file]}", flush=True)
        print(f"\t  Mask {mask_files[file]}", flush=True)

        clean_subj_name = op.basename(clean_subj_file)
        subj_prefix = clean_subj_name.split("desc-")[0].rstrip("_")

        stim_info = ""
        for i, roi in enumerate(rois):
            # Resample ROIs to MNI152NLin2009cAsym
            roi_name = op.basename(roi)
            prefix = roi_name.split(".")[0]
            roi_res = op.join(rsfc_dir, f"{prefix}_space-{space}_desc-brain_mask.nii.gz")
            if not op.exists(roi_res):
                roi_resample(roi, roi_res, clean_subj_file)

            # Average time series of each voxel within each ROIs
            roi_subj_timeseries = op.join(rsfc_subj_dir, f"{subj_prefix}_ROI{i}.txt")
            if not op.exists(roi_subj_timeseries):
                ave_timeseries(roi_res, clean_subj_file, roi_subj_timeseries)

            # Conform stim_info for 3Ddeconvolve
            num = i + 1
            stim_info += f"-stim_file {num} {roi_subj_timeseries} "
            stim_info += f'-stim_label {num} "{roi_res}" '

        # Conform design matrix using 3dTconcolve
        des_subj_matrix = op.join(rsfc_subj_dir, f"{subj_prefix}_dmatrix.1D")
        if not op.exists(des_subj_matrix):
            design_matrix(
                smooth_subj_files[file],
                mask_files[file],
                len(rois),
                stim_info,
                des_subj_matrix,
                n_jobs,
            )

        # Calculate connectivity using the GLM
        bucket_subj_reml = op.join(rsfc_subj_dir, f"{subj_prefix}_bucketREML")
        if not op.exists(bucket_subj_reml):
            connectivity(
                des_subj_matrix, smooth_subj_files[file], mask_files[file], bucket_subj_reml
            )

        # Normalize correlations
        bucket_subj_reml_z = op.join(rsfc_subj_dir, f"{subj_prefix}_desc-norm_bucketREML")
        if not op.exists(bucket_subj_reml_z):
            norm_conn(bucket_subj_reml, bucket_subj_reml_z)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
