import argparse
import os
import os.path as op
from glob import glob
from shutil import copyfile

import pandas as pd


def _get_parser():
    parser = argparse.ArgumentParser(description="Run RSFC in AFNI")
    parser.add_argument(
        "--mriqc_dir",
        dest="mriqc_dir",
        required=True,
        help="Path to MRIQC directory",
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
        default=4,
        required=False,
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


def add_outlier(mriqc_dir, prefix):

    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")

    if runs_to_exclude_df["bids_name"].str.contains(prefix).any():
        print(f"\t\t\t{prefix} already in runs_to_exclude.tsv")
    else:
        runs_exclude_df = runs_to_exclude_df.append({"bids_name": f"{prefix}"}, ignore_index=True)
        runs_exclude_df = runs_exclude_df.drop_duplicates(subset=["bids_name"])
        runs_exclude_df["bids_name"].to_csv(
            op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t", index=False
        )


def main(mriqc_dir, clean_dir, rsfc_dir, subject, sessions, space, desc_list, rois, n_jobs):
    """Run denoising workflows on a given dataset."""
    os.system(f"export OMP_NUM_THREADS={n_jobs}")
    assert len(desc_list) == 2
    if sessions[0] is None:
        temp_ses = glob(op.join(clean_dir, subject, "ses-*"))
        if len(temp_ses) > 0:
            sessions = [op.basename(x) for x in temp_ses]

    for session in sessions:
        if session is not None:
            clean_subj_dir = op.join(clean_dir, subject, session, "func")
            rsfc_subj_dir = op.join(rsfc_dir, subject, session, "func")
        else:
            clean_subj_dir = op.join(clean_dir, subject, "func")
            rsfc_subj_dir = op.join(rsfc_dir, subject, "func")

        # Collect important files
        clean_subj_files = sorted(
            glob(
                op.join(
                    clean_subj_dir, f"*task-rest*_space-{space}*_desc-{desc_list[0]}_bold.nii.gz"
                )
            )
        )

        if len(clean_subj_files) > 0:
            os.makedirs(rsfc_subj_dir, exist_ok=True)

        # ###################
        # RSFC
        # ###################
        for clean_subj_file in clean_subj_files:
            clean_subj_name = op.basename(clean_subj_file)
            prefix = clean_subj_name.split("desc-")[0].rstrip("_")

            mask_files = sorted(glob(op.join(clean_subj_dir, f"{prefix}_desc-brain_mask.nii.gz")))
            smooth_subj_files = sorted(
                glob(op.join(clean_subj_dir, f"{prefix}_desc-{desc_list[1]}_bold.nii.gz"))
            )
            reho_subj_files = sorted(
                glob(op.join(clean_subj_dir, f"{prefix}_desc-REHOnorm_REHO.nii.gz"))
            )
            falff_subj_files = sorted(
                glob(op.join(clean_subj_dir, f"{prefix}_desc-RSFCnorm_FALFF.nii.gz"))
            )
            assert len(mask_files) == 1
            assert len(smooth_subj_files) == 1
            assert len(reho_subj_files) == 1
            assert len(falff_subj_files) == 1
            smooth_subj_file = smooth_subj_files[0]
            reho_subj_file = reho_subj_files[0]
            falff_subj_file = falff_subj_files[0]

            mask_name = os.path.basename(mask_files[0])
            mask_file = op.join(rsfc_subj_dir, mask_name)
            copyfile(mask_files[0], mask_file)

            print(f"\tProcessing {subject}, {session}, {rois} files:", flush=True)
            print(f"\t\tClean:   {clean_subj_file}", flush=True)
            print(f"\t\tSmooth:  {smooth_subj_file}", flush=True)
            print(f"\t\tMask:     {mask_file}", flush=True)
            print(f"\t\tReHo:    {reho_subj_file}", flush=True)
            print(f"\t\tfALFF:   {falff_subj_file}", flush=True)

            clean_subj_name = op.basename(clean_subj_file)
            subj_prefix = clean_subj_name.split("desc-")[0].rstrip("_")

            exclude = False
            stim_info = ""
            for i, roi in enumerate(rois):
                num = i + 1
                roi_name = op.basename(roi)
                roi_prefix = roi_name.split("_")[0].split("-")[1]
                roi_res = op.join(rsfc_subj_dir, f"{prefix}_desc-{roi_prefix}_mask.nii.gz")
                if not op.exists(roi_res):
                    roi_resample(roi, roi_res, clean_subj_file)

                # Average time series of each voxel within each ROIs
                roi_subj_timeseries = op.join(
                    rsfc_subj_dir, f"{subj_prefix}_desc-{roi_prefix}_timeseries.txt"
                )
                # Average fALFF of each voxel within each ROIs
                roi_subj_falff = op.join(
                    rsfc_subj_dir, f"{subj_prefix}_desc-{roi_prefix}_FALFF.txt"
                )
                # Average ReHo of each voxel within each ROIs
                roi_subj_reho = op.join(rsfc_subj_dir, f"{subj_prefix}_desc-{roi_prefix}_REHO.txt")
                if not op.exists(roi_subj_timeseries):
                    ave_timeseries(roi_res, clean_subj_file, roi_subj_timeseries)
                if not op.exists(roi_subj_falff):
                    ave_timeseries(roi_res, falff_subj_file, roi_subj_falff)
                if not op.exists(roi_subj_reho):
                    ave_timeseries(roi_res, reho_subj_file, roi_subj_reho)

                roi_subj_timeseries_df = pd.read_csv(roi_subj_timeseries, header=None)
                non_zero = len(
                    roi_subj_timeseries_df.index[roi_subj_timeseries_df[0] != 0].tolist()
                )
                if non_zero == 0:
                    exclude = True
                    run_name = prefix.split("_space-")[0]
                    print(f"\t\tAdding run {run_name} to outliers", flush=True)
                    add_outlier(mriqc_dir, run_name)

                # Conform stim_info for 3dDeconvolve
                stim_info += f"-stim_file {num} {roi_subj_timeseries} "
                stim_info += f'-stim_label {num} "{roi_res}" '

            # Conform design matrix using 3dDeconvolve
            des_subj_matrix = op.join(rsfc_subj_dir, f"{subj_prefix}_dmatrix.1D")
            if (not op.exists(des_subj_matrix)) and (not exclude):
                design_matrix(
                    smooth_subj_file,
                    mask_file,
                    len(rois),
                    stim_info,
                    des_subj_matrix,
                    n_jobs,
                )

            # Calculate connectivity using the GLM in 3dREMLfit
            bucket_subj_reml = op.join(rsfc_subj_dir, f"{subj_prefix}_bucketREML")
            if (not op.exists(f"{bucket_subj_reml}+tlrc.BRIK")) and (op.exists(des_subj_matrix)):
                connectivity(des_subj_matrix, smooth_subj_file, mask_file, bucket_subj_reml)

            # Normalize correlations
            bucket_subj_reml_z = op.join(rsfc_subj_dir, f"{subj_prefix}_desc-norm_bucketREML")
            if (not op.exists(f"{bucket_subj_reml_z}+tlrc.BRIK")) and (
                op.exists(f"{bucket_subj_reml}+tlrc.BRIK")
            ):
                norm_conn(bucket_subj_reml, bucket_subj_reml_z)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
