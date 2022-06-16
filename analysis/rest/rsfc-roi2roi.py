import argparse
import os
import os.path as op
from glob import glob
from shutil import copyfile

import pandas as pd


def _get_parser():
    parser = argparse.ArgumentParser(description="Run RSFC in AFNI")
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
        "--atlas_dir",
        dest="atlas_dir",
        required=True,
        help="Path to atlas directory",
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


def make_label_table(lab_file, lab_table, atlas_img):
    cmd = f"@MakeLabelTable \
            -lab_file {lab_file} 1 0   \
            -labeltable {lab_table} \
            -dset {atlas_img}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def roi2roi_conn(clean_subj_fn, mask_file, atlas_img, rsfc_atlas_subj):
    cmd = f"3dNetCorr \
            -inset {clean_subj_fn} \
            -mask {mask_file} \
            -in_rois {atlas_img} \
            -fish_z \
            -ts_out \
            -ts_label \
            -prefix {rsfc_atlas_subj}"
    print(f"\t\t\t{cmd}", flush=True)
    os.system(cmd)


def main(clean_dir, rsfc_dir, atlas_dir, subject, sessions, space, desc_list, n_jobs):
    """Run denoising workflows on a given dataset."""
    os.system(f"export OMP_NUM_THREADS={n_jobs}")
    assert len(desc_list) == 2
    atlases = sorted(glob(op.join(atlas_dir, "*")))

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
            assert len(mask_files) == 1

            mask_name = os.path.basename(mask_files[0])
            mask_file = op.join(rsfc_subj_dir, mask_name)
            copyfile(mask_files[0], mask_file)

            print(f"\tProcessing {subject}, {session} files:", flush=True)
            print(f"\t\tClean:  {clean_subj_file}", flush=True)
            print(f"\t\tMask:   {mask_file}", flush=True)

            for atlas in atlases:
                atlas_name = op.basename(atlas)
                atlas_imgs = sorted(glob(op.join(atlas, "*.nii.gz")))
                assert len(atlas_imgs) == 1
                atlas_img = atlas_imgs[0]

                lab_files = sorted(glob(op.join(atlas, "*.txt")))
                if len(lab_files) == 0:
                    # Do not create label table file
                    make_table = False
                else:
                    assert len(lab_files) == 1
                    lab_file = lab_files[0]
                    make_table = True

                # Resample atlas
                atlas_img_res = op.join(rsfc_subj_dir, f"{prefix}_desc-{atlas_name}_atlas.nii.gz")
                if not op.exists(atlas_img_res):
                    roi_resample(atlas_img, atlas_img_res, clean_subj_file)

                # Create label table
                lab_table = op.join(rsfc_subj_dir, f"{prefix}_desc-{atlas_name}_labtable.niml.lt")
                if (not op.exists(lab_table)) and (make_table):
                    make_label_table(lab_file, lab_table, atlas_img_res)

                # Calculate RSFC
                rsfc_atlas_subj = op.join(rsfc_subj_dir, f"{prefix}_desc-{atlas_name}")
                if not op.exists(f"{rsfc_atlas_subj}_000.netcc"):
                    roi2roi_conn(clean_subj_file, mask_file, atlas_img_res, rsfc_atlas_subj)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
