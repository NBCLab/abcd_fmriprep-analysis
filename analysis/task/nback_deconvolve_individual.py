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
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-smooth.nii.gz'.format(sub=args.sub, ses=args.ses, run=run))

        mask_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-mask.nii.gz'.format(sub=args.sub, ses=args.ses, run=run))

        if run == '1+2':
            concat_fn = op.join(args.bids_dir,
                            'derivatives',
                            'fmriprep_post-process',
                            args.sub,
                            args.ses,
                            'nback',
                            '{sub}_{ses}_task-nback_run-{run}_desc-TRcat.1D'.format(sub=args.sub, ses=args.ses, run=run))

        censor_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_motion_censoring.1D'.format(sub=args.sub, ses=args.ses, run=run))

        motion_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_motion_parameters.1D'.format(sub=args.sub, ses=args.ses, run=run))

        zero_back_negface_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_negface.txt'.format(run=run))

        zero_back_negface_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_negface_duration.txt'.format(run=run))

        with open(zero_back_negface_duration_fn, 'r') as fo:
            zero_back_negface_dur = fo.read()

        zero_back_neutface_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_neutface.txt'.format(run=run))

        zero_back_neutface_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_neutface_duration.txt'.format(run=run))

        with open(zero_back_neutface_duration_fn, 'r') as fo:
            zero_back_neutface_dur = fo.read()

        zero_back_posface_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_posface.txt'.format(run=run))

        zero_back_posface_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_posface_duration.txt'.format(run=run))

        with open(zero_back_posface_duration_fn, 'r') as fo:
            zero_back_posface_dur = fo.read()

        zero_back_place_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_place.txt'.format(run=run))

        zero_back_place_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_0_back_place_duration.txt'.format(run=run))

        with open(zero_back_place_duration_fn, 'r') as fo:
            zero_back_place_dur = fo.read()

        two_back_negface_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_negface.txt'.format(run=run))

        two_back_negface_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_negface_duration.txt'.format(run=run))

        with open(two_back_negface_duration_fn, 'r') as fo:
            two_back_negface_dur = fo.read()

        two_back_neutface_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_neutface.txt'.format(run=run))

        two_back_neutface_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_neutface_duration.txt'.format(run=run))

        with open(two_back_neutface_duration_fn, 'r') as fo:
            two_back_neutface_dur = fo.read()

        two_back_posface_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_posface.txt'.format(run=run))

        two_back_posface_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_posface_duration.txt'.format(run=run))

        with open(two_back_posface_duration_fn, 'r') as fo:
            two_back_posface_dur = fo.read()

        two_back_place_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_place.txt'.format(run=run))

        two_back_place_duration_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        'timing_files',
                        'run-{run}_2_back_place_duration.txt'.format(run=run))

        with open(two_back_place_duration_fn, 'r') as fo:
            two_back_place_dur = fo.read()

        design_jpeg_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_SPMG.jpg'.format(sub=args.sub, ses=args.ses, run=run))

        design_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_SPMG.1D'.format(sub=args.sub, ses=args.ses, run=run))

        bucket_fn = op.join(args.bids_dir,
                        'derivatives',
                        'fmriprep_post-process',
                        args.sub,
                        args.ses,
                        'nback',
                        '{sub}_{ses}_task-nback_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-REMLbucket+SPMG'.format(sub=args.sub, ses=args.ses, run=run))

        cmd='3dDeconvolve -input {in_file} \
                          -polort A \
                          -x1D_stop \
                          -mask {mask_fn} \
                          -censor {censor_fn} \
                          -num_stimts 14 \
                          -allzero_OK \
                          -jobs 6 \
                          -svd \
                          -local_times \
                          -basis_normall 1 \
                          -stim_times 1 {zero_back_negface_fn} SPMG\({zero_back_negface_dur}\)  \
                          -stim_label 1 "zeroback_negface" \
                          -stim_times 2 {zero_back_neutface_fn} SPMG\({zero_back_neutface_dur}\)  \
                          -stim_label 2 "zeroback_neutface" \
                          -stim_times 3 {zero_back_posface_fn} SPMG\({zero_back_posface_dur}\)  \
                          -stim_label 3 "zeroback_posface" \
                          -stim_times 4 {zero_back_place_fn} SPMG\({zero_back_place_dur}\)  \
                          -stim_label 4 "zeroback_place" \
                          -stim_times 5 {two_back_negface_fn} SPMG\({two_back_negface_dur}\)  \
                          -stim_label 5 "twoback_negface" \
                          -stim_times 6 {two_back_neutface_fn} SPMG\({two_back_neutface_dur}\)  \
                          -stim_label 6 "twoback_neutface" \
                          -stim_times 7 {two_back_posface_fn} SPMG\({two_back_posface_dur}\)  \
                          -stim_label 7 "twoback_posface" \
                          -stim_times 8 {two_back_place_fn} SPMG\({two_back_place_dur}\)  \
                          -stim_label 8 "twoback_place" \
                          -stim_file 9 {motion_fn}\'[3]\' \
                          -stim_label 9 "roll" \
                          -stim_base 9 \
                          -stim_file 10 {motion_fn}\'[4]\' \
                          -stim_label 10 "pitch" \
                          -stim_base 10 \
                          -stim_file 11 {motion_fn}\'[5]\' \
                          -stim_label 11 "yaw" \
                          -stim_base 11 \
                          -stim_file 12 {motion_fn}\'[0]\' \
                          -stim_label 12 "dx" \
                          -stim_base 12 \
                          -stim_file 13 {motion_fn}\'[1]\' \
                          -stim_label 13 "dy" \
                          -stim_base 13 \
                          -stim_file 14 {motion_fn}\'[2]\' \
                          -stim_label 14 "dz" \
                          -stim_base 14 \
                          -num_glt 6 \
                          -gltsym \'SYM: +zeroback_negface[0] +zeroback_neutface[0] +zeroback_posface[0] +zeroback_place[0]\' \
                          -glt_label 1 zero_back \
                          -gltsym \'SYM: +twoback_negface[0] +twoback_neutface[0] +twoback_posface[0] +twoback_place[0]\' \
                          -glt_label 2 two_back \
                          -gltsym \'SYM: +twoback_negface[0] +twoback_neutface[0] +twoback_posface[0] +twoback_place[0] -zeroback_negface[0] -zeroback_neutface[0] -zeroback_posface[0] -zeroback_place[0]\' \
                          -glt_label 3 two_back_gt_zero_back \
                          -gltsym \'SYM: +twoback_negface[0] +twoback_neutface[0] +twoback_posface[0] +zeroback_negface[0] +zeroback_neutface[0] +zeroback_posface[0] -twoback_place[0] -zeroback_place[0]\' \
                          -glt_label 4 faces_gt_places \
                          -gltsym \'SYM: +twoback_negface[0] +zeroback_negface[0] -twoback_neutface[0] -zeroback_neutface[0]\' \
                          -glt_label 5 negative_faces_gt_neutral_faces \
                          -gltsym \'SYM: +twoback_posface[0] +zeroback_posface[0] -twoback_neutface[0] -zeroback_neutface[0]\' \
                          -glt_label 6 positive_faces_gt_neutral_faces \
                          -xjpeg {design_jpeg_fn} \
                          -x1D {design_fn}'.format(in_file=in_file,
                                                   mask_fn=mask_fn,
                                                   censor_fn=censor_fn,
                                                   zero_back_negface_fn=zero_back_negface_fn,
                                                   zero_back_negface_dur=zero_back_negface_dur,
                                                   zero_back_neutface_fn=zero_back_neutface_fn,
                                                   zero_back_neutface_dur=zero_back_neutface_dur,
                                                   zero_back_posface_fn=zero_back_posface_fn,
                                                   zero_back_posface_dur=zero_back_posface_dur,
                                                   zero_back_place_fn=zero_back_place_fn,
                                                   zero_back_place_dur=zero_back_place_dur,
                                                   two_back_negface_fn=two_back_negface_fn,
                                                   two_back_negface_dur=two_back_negface_dur,
                                                   two_back_neutface_fn=two_back_neutface_fn,
                                                   two_back_neutface_dur=two_back_neutface_dur,
                                                   two_back_posface_fn=two_back_posface_fn,
                                                   two_back_posface_dur=two_back_posface_dur,
                                                   two_back_place_fn=two_back_place_fn,
                                                   two_back_place_dur=two_back_place_dur,
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
