#!/usr/bin/env python3
"""
Based on
https://github.com/BIDS-Apps/example/blob/aa0d4808974d79c9fbe54d56d3b47bb2cf4e0a0d/run.py
"""
import os
import os.path as op
import argparse


def get_parser():
    parser = argparse.ArgumentParser(description='Run MRIQC on BIDS dataset.')
    parser.add_argument('-b', '--bidsdir', required=True, dest='bids_dir',
                        help=('Output directory for BIDS dataset and '
                              'derivatives.'))
    parser.add_argument('--sub', required=True, dest='sub',
                        help='The label of the subject to analyze.')
    parser.add_argument('--ses', required=False, dest='ses',
                        help='Session number', default=None)
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    for run in ['1', '2', '1+2']:
        in_file = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_space-MNI152NLin2009cAsym_desc-smooth.nii.gz'.format(sub=args.sub, ses=args.ses, run=run))

        mask_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_space-MNI152NLin2009cAsym_desc-mask.nii.gz'.format(sub=args.sub, ses=args.ses, run=run))

        if run == '1+2':
            concat_fn = op.join(args.bids_dir,
                            'derivatives',
                            'fmriprep_post-process',
                            args.sub,
                            args.ses,
                            'SST',
                            '{sub}_{ses}_task-SST_run-{run}_desc-TRcat.1D'.format(sub=args.sub, ses=args.ses, run=run))

        censor_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_motion_censoring.1D'.format(sub=args.sub, ses=args.ses, run=run))

        motion_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_motion_parameters.1D'.format(sub=args.sub, ses=args.ses, run=run))

        correct_go_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        'timing_files',
                        'run-{run}_correct_go.txt'.format(run=run))

        correct_stop_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        'timing_files',
                        'run-{run}_correct_stop.txt'.format(run=run))

        incorrect_go_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        'timing_files',
                        'run-{run}_incorrect_go.txt'.format(run=run))

        incorrect_stop_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        'timing_files',
                        'run-{run}_incorrect_stop.txt'.format(run=run))

        design_jpeg_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_SPMG.jpg'.format(sub=args.sub, ses=args.ses, run=run))

        design_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_SPMG.1D'.format(sub=args.sub, ses=args.ses, run=run))

        bucket_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'SST',
                        '{sub}_{ses}_task-SST_run-{run}_space-MNI152NLin2009cAsym_desc-REMLbucket+SPMG'.format(sub=args.sub, ses=args.ses, run=run))

        cmd='3dDeconvolve -input {in_file} \
                          -polort A \
                          -x1D_stop \
                          -mask {mask_fn} \
                          -censor {censor_fn} \
                          -num_stimts 10 \
                          -allzero_OK \
                          -jobs 6 \
                          -svd \
                          -local_times \
                          -basis_normall 1 \
                          -stim_times 1 {correct_go_fn} SPMG  \
                          -stim_label 1 "correct_go" \
                          -stim_times 2 {correct_stop_fn} SPMG  \
                          -stim_label 2 "correct_stop" \
                          -stim_times 3 {incorrect_go_fn} SPMG  \
                          -stim_label 3 "incorrect_go" \
                          -stim_times 4 {incorrect_stop_fn} SPMG  \
                          -stim_label 4 "incorrect_stop" \
                          -stim_file 5 {motion_fn}\'[3]\' \
                          -stim_label 5 "roll" \
                          -stim_base 5 \
                          -stim_file 6 {motion_fn}\'[4]\' \
                          -stim_label 6 "pitch" \
                          -stim_base 6 \
                          -stim_file 7 {motion_fn}\'[5]\' \
                          -stim_label 7 "yaw" \
                          -stim_base 7 \
                          -stim_file 8 {motion_fn}\'[0]\' \
                          -stim_label 8 "dx" \
                          -stim_base 8 \
                          -stim_file 9 {motion_fn}\'[1]\' \
                          -stim_label 9 "dy" \
                          -stim_base 9 \
                          -stim_file 10 {motion_fn}\'[2]\' \
                          -stim_label 10 "dz" \
                          -stim_base 10 \
                          -num_glt 3 \
                          -gltsym \'SYM: +correct_stop[0] -correct_go[0]\' \
                          -glt_label 1 correct_stop_gt_correct_go \
                          -gltsym \'SYM: +incorrect_stop[0] -correct_go[0]\' \
                          -glt_label 2 incorrect_stop_gt_correct_go \
                          -gltsym \'SYM: +correct_stop[0] -incorrect_stop[0]\' \
                          -glt_label 3 correct_stop_gt_incorrect_stop \
                          -xjpeg {design_jpeg_fn} \
                          -x1D {design_fn}'.format(in_file=in_file,
                                                   mask_fn=mask_fn,
                                                   censor_fn=censor_fn,
                                                   correct_go_fn=correct_go_fn,
                                                   correct_stop_fn=correct_stop_fn,
                                                   incorrect_go_fn=incorrect_go_fn,
                                                   incorrect_stop_fn=incorrect_stop_fn,
                                                   motion_fn=motion_fn,
                                                   design_jpeg_fn=design_jpeg_fn,
                                                   design_fn=design_fn)

        if run == '1+2':
            cmd+=' -concat {concat_fn}'.format(concat_fn=concat_fn)
        os.system(cmd)

        cmd='3dREMLfit -matrix {design_fn} \
                       -input {in_file} \
                       -mask {mask_fn} \
                       -fout \
                       -tout \
                       -Rbuck {bucket_fn} \
                       -verb'.format(design_fn=design_fn,
                                     in_file=in_file,
                                     mask_fn=mask_fn,
                                     bucket_fn=bucket_fn)
        os.system(cmd)


if __name__ == '__main__':
    main()
