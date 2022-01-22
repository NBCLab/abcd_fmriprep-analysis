#!/usr/bin/env python3
"""
Based on
https://github.com/BIDS-Apps/example/blob/aa0d4808974d79c9fbe54d56d3b47bb2cf4e0a0d/run.py
"""
import argparse
import os
import os.path as op


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
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_space-MNI152NLin2009cAsym_desc-smooth.nii.gz'.format(sub=args.sub, ses=args.ses, run=run))

        mask_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_space-MNI152NLin2009cAsym_desc-mask.nii.gz'.format(sub=args.sub, ses=args.ses, run=run))

        if run == '1+2':
            concat_fn = op.join(args.bids_dir,
                            'derivatives',
                            'fmriprep_post-process',
                            args.sub,
                            args.ses,
                            'MID',
                            '{sub}_{ses}_task-MID_run-{run}_desc-TRcat.1D'.format(sub=args.sub, ses=args.ses, run=run))

        censor_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_motion_censoring.1D'.format(sub=args.sub, ses=args.ses, run=run))

        motion_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_motion_parameters.1D'.format(sub=args.sub, ses=args.ses, run=run))

        large_loss_antic_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_large_loss_antic.txt'.format(run=run))

        large_reward_antic_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_large_reward_antic.txt'.format(run=run))

        small_loss_antic_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_small_loss_antic.txt'.format(run=run))

        small_reward_antic_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_small_reward_antic.txt'.format(run=run))

        neutral_antic_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_neutral_antic.txt'.format(run=run))

        large_loss_neg_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_large_loss_neg_feedback.txt'.format(run=run))

        large_reward_neg_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_large_reward_neg_feedback.txt'.format(run=run))

        small_loss_neg_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_small_loss_neg_feedback.txt'.format(run=run))

        small_reward_neg_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_small_reward_neg_feedback.txt'.format(run=run))

        neutral_neg_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_neutral_neg_feedback.txt'.format(run=run))

        large_loss_pos_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_large_loss_pos_feedback.txt'.format(run=run))

        large_reward_pos_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_large_reward_pos_feedback.txt'.format(run=run))

        small_loss_pos_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_small_loss_pos_feedback.txt'.format(run=run))

        small_reward_pos_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_small_reward_pos_feedback.txt'.format(run=run))

        neutral_pos_feedback_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        'timing_files',
                        'run-{run}_neutral_pos_feedback.txt'.format(run=run))

        design_jpeg_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_SPMG.jpg'.format(sub=args.sub, ses=args.ses, run=run))

        design_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_SPMG.1D'.format(sub=args.sub, ses=args.ses, run=run))

        bucket_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'MID',
                        '{sub}_{ses}_task-MID_run-{run}_space-MNI152NLin2009cAsym_desc-REMLbucket+SPMG'.format(sub=args.sub, ses=args.ses, run=run))

        cmd='3dDeconvolve -input {in_file} \
                          -polort A \
                          -x1D_stop \
                          -mask {mask_fn} \
                          -censor {censor_fn} \
                          -num_stimts 21 \
                          -allzero_OK \
                          -jobs 6 \
                          -svd \
                          -local_times \
                          -basis_normall 1 \
                          -stim_times 1 {large_loss_antic_fn} SPMG  \
                          -stim_label 1 "large_loss_antic" \
                          -stim_times 2 {large_reward_antic_fn} SPMG  \
                          -stim_label 2 "large_reward_antic" \
                          -stim_times 3 {small_loss_antic_fn} SPMG  \
                          -stim_label 3 "small_loss_antic" \
                          -stim_times 4 {small_reward_antic_fn} SPMG  \
                          -stim_label 4 "small_reward_antic" \
                          -stim_times 5 {neutral_antic_fn} SPMG  \
                          -stim_label 5 "neutral_antic" \
                          -stim_times 6 {large_loss_pos_feedback_fn} SPMG  \
                          -stim_label 6 "large_loss_pos_feedback" \
                          -stim_times 7 {large_reward_pos_feedback_fn} SPMG  \
                          -stim_label 7 "large_reward_pos_feedback" \
                          -stim_times 8 {small_loss_pos_feedback_fn} SPMG \
                          -stim_label 8 "small_loss_pos_feedback" \
                          -stim_times 9 {small_reward_pos_feedback_fn} SPMG  \
                          -stim_label 9 "small_reward_pos_feedback" \
                          -stim_times 10 {neutral_pos_feedback_fn} SPMG  \
                          -stim_label 10 "neutral_pos_feedback" \
                          -stim_times 11 {large_loss_neg_feedback_fn} SPMG  \
                          -stim_label 11 "large_loss_neg_feedback" \
                          -stim_times 12 {large_reward_neg_feedback_fn} SPMG  \
                          -stim_label 12 "large_reward_neg_feedback" \
                          -stim_times 13 {small_loss_neg_feedback_fn} SPMG \
                          -stim_label 13 "small_loss_neg_feedback" \
                          -stim_times 14 {small_reward_neg_feedback_fn} SPMG  \
                          -stim_label 14 "small_reward_neg_feedback" \
                          -stim_times 15 {neutral_neg_feedback_fn} SPMG  \
                          -stim_label 15 "neutral_neg_feedback" \
                          -stim_file 16 {motion_fn}\'[3]\' \
                          -stim_label 16 "roll" \
                          -stim_base 16 \
                          -stim_file 17 {motion_fn}\'[4]\' \
                          -stim_label 17 "pitch" \
                          -stim_base 17 \
                          -stim_file 18 {motion_fn}\'[5]\' \
                          -stim_label 18 "yaw" \
                          -stim_base 18 \
                          -stim_file 19 {motion_fn}\'[0]\' \
                          -stim_label 19 "dx" \
                          -stim_base 19 \
                          -stim_file 20 {motion_fn}\'[1]\' \
                          -stim_label 20 "dy" \
                          -stim_base 20 \
                          -stim_file 21 {motion_fn}\'[2]\' \
                          -stim_label 21 "dz" \
                          -stim_base 21 \
                          -num_glt 6 \
                          -gltsym \'SYM: +large_reward_pos_feedback[0] +large_reward_neg_feedback[0] -neutral_antic[0]\' \
                          -glt_label 1 large_reward_gt_neutral_antic \
                          -gltsym \'SYM: +small_reward_pos_feedback[0] +small_reward_neg_feedback[0] -neutral_antic[0]\' \
                          -glt_label 2 small_reward_gt_neutral_antic \
                          -gltsym \'SYM: +large_loss_pos_feedback[0] +large_loss_neg_feedback[0] -neutral_antic[0]\' \
                          -glt_label 3 large_loss_gt_neutral_antic \
                          -gltsym \'SYM: +small_loss_pos_feedback[0] +small_loss_neg_feedback[0] -neutral_antic[0]\' \
                          -glt_label 4 small_loss_gt_neutral_antic \
                          -gltsym \'SYM: +large_reward_pos_feedback[0] +small_reward_pos_feedback[0] -large_reward_neg_feedback[0] -small_reward_neg_feedback[0]\' \
                          -glt_label 5 reward_pos_feedback_gt_reward_neg_feedback \
                          -gltsym \'SYM: +large_loss_pos_feedback[0] +small_loss_pos_feedback[0] -large_loss_neg_feedback[0] -small_loss_neg_feedback[0]\' \
                          -glt_label 6 loss_pos_feedback_gt_loss_neg_feedback \
                          -xjpeg {design_jpeg_fn} \
                          -x1D {design_fn}'.format(in_file=in_file,
                                                   mask_fn=mask_fn,
                                                   censor_fn=censor_fn,
                                                   large_loss_antic_fn=large_loss_antic_fn,
                                                   large_reward_antic_fn=large_reward_antic_fn,
                                                   small_loss_antic_fn=small_loss_antic_fn,
                                                   small_reward_antic_fn=small_reward_antic_fn,
                                                   neutral_antic_fn=neutral_antic_fn,
                                                   large_loss_pos_feedback_fn=large_loss_pos_feedback_fn,
                                                   large_reward_pos_feedback_fn=large_reward_pos_feedback_fn,
                                                   small_loss_pos_feedback_fn=small_loss_pos_feedback_fn,
                                                   small_reward_pos_feedback_fn=small_reward_pos_feedback_fn,
                                                   neutral_pos_feedback_fn=neutral_pos_feedback_fn,
                                                   large_loss_neg_feedback_fn=large_loss_neg_feedback_fn,
                                                   large_reward_neg_feedback_fn=large_reward_neg_feedback_fn,
                                                   small_loss_neg_feedback_fn=small_loss_neg_feedback_fn,
                                                   small_reward_neg_feedback_fn=small_reward_neg_feedback_fn,
                                                   neutral_neg_feedback_fn=neutral_neg_feedback_fn,
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
