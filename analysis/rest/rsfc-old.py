import argparse
import os
import os.path as op
from glob import glob


def get_parser():
    parser = argparse.ArgumentParser(
        description="Download ABCD participant data " "and run MRIQC and fMRIPREP docker images"
    )
    parser.add_argument("--bids_dir", required=True, dest="bids_dir")
    parser.add_argument("--sub", required=True, dest="sub")
    parser.add_argument("--ses", required=False, dest="ses")
    parser.add_argument("--roi", required=False, nargs="+", dest="roi")
    return parser


def main(argv=None):

    script_dir = op.dirname(op.realpath(__file__))

    args = get_parser().parse_args(argv)

    rois = args.roi
    roi_out_dirname = "+".join([op.basename(i).split(".")[0] for i in rois])

    rs_files = sorted(
        glob(
            op.join(
                args.bids_dir,
                "derivatives",
                "fmriprep_post-process",
                args.sub,
                args.ses,
                "rest",
                "*-clean.nii.gz",
            )
        )
    )
    for rs_file in rs_files:

        out_dir = op.join(
            args.bids_dir,
            "derivatives",
            "fmriprep_post-process_{}".format(roi_out_dirname),
            args.sub,
            args.ses,
            op.basename(rs_file).split(".")[0],
        )

        if not op.isfile(op.join(out_dir, "{}_bucket-REML_z+tlrc.HEAD".format(roi_out_dirname))):

            os.makedirs(out_dir, exist_ok=True)

            smooth_file = "{}-smooth+clean.nii.gz".format(rs_file.rstrip("-clean.nii.gz"))
            mask_fname = "{}-brain_mask.nii.gz".format(
                rs_file.split("-preproc_bold-clean.nii.gz")[0]
            )

            stim_info = ""
            for i, roi in enumerate(rois):

                roi_name = op.basename(roi).split(".")[0]

                cmd = "3dresample -prefix {out_fname} \
                                  -master {rs_file} \
                                  -inset {roi}".format(
                    out_fname=op.join(out_dir, "{}.nii".format(roi_name)), rs_file=rs_file, roi=roi
                )
                os.system(cmd)

                cmd = "3dmaskave -q \
                               -mask {mask} \
                               {rs_file} > {rs_timeseries}".format(
                    mask=op.join(out_dir, "{}.nii".format(roi_name)),
                    rs_file=rs_file,
                    rs_timeseries=op.join(out_dir, "{}.txt".format(roi_name)),
                )
                os.system(cmd)

                stim_info += "-stim_file {num} {rs_timeseries} ".format(
                    num=i + 1, rs_timeseries=op.join(out_dir, "{}.txt".format(roi_name))
                )
                stim_info += '-stim_label {num} "{roi_name}" '.format(num=i + 1, roi_name=roi_name)

            matrix_fname = "{}.1D".format(roi_out_dirname)
            cmd = "3dDeconvolve -input {rs_smooth_fn} \
                    -x1D_stop \
                    -mask {mask_fname} \
                    -num_stimts {num_roi} \
                    -jobs 6 \
                    -svd \
                    -local_times \
                    -basis_normall 1 \
                    {stim_info} \
                    -x1D {matrix_fname}".format(
                rs_smooth_fn=smooth_file,
                mask_fname=mask_fname,
                num_roi=len(rois),
                stim_info=stim_info,
                matrix_fname=matrix_fname,
            )
            os.chdir(out_dir)
            print(cmd)
            os.system(cmd)

            out_bucket = op.join(out_dir, "{}_bucket-REML".format(roi_out_dirname))
            cmd = "3dREMLfit -matrix {matrix_fname} \
                    -input {rs_smooth_fn} \
                    -mask {mask_fname} \
                    -fout \
                    -tout \
                    -Rbuck {out_bucket} \
                    -verb".format(
                matrix_fname=matrix_fname,
                rs_smooth_fn=smooth_file,
                mask_fname=mask_fname,
                out_bucket=out_bucket,
            )
            os.system(cmd)
            os.chdir(script_dir)

            out_bucket_z = op.join(out_dir, "{}_bucket-REML_z".format(roi_out_dirname))
            cmd = '3dcalc -a {out_bucket}+tlrc \
                        -expr "atanh(a)" \
                        -prefix {out_bucket_z}'.format(
                out_bucket=out_bucket, out_bucket_z=out_bucket_z
            )
            os.system(cmd)


if __name__ == "__main__":
    main()
