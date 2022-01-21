#!/usr/bin/env python3
"""
Based on
https://github.com/BIDS-Apps/example/blob/aa0d4808974d79c9fbe54d56d3b47bb2cf4e0a0d/run.py
"""
import os
import os.path as op
from glob import glob
import argparse
import nibabel as nib
import numpy as np
from nilearn import masking
from nilearn.image import smooth_img
from nipype.interfaces.fsl import Merge
import pandas as pd
import json
import sys
sys.path.append('/home/data/abcd/code/abcd_fmriprep-analysis')
from utils import fd_censoring
from utils import motion_parameters
from utils import enhance_censoring


def get_parser():
    parser = argparse.ArgumentParser(description='Run MRIQC on BIDS dataset.')
    parser.add_argument('-b', '--bidsdir', required=True, dest='bids_dir',
                        help=('Output directory for BIDS dataset and '
                              'derivatives.'))
    parser.add_argument('--sub', required=True, dest='sub',
                        help='The label of the subject to analyze.')
    parser.add_argument('--ses', required=False, dest='ses',
                        help='Session number', default=None)
    parser.add_argument('--task', required=True, dest='task',
                        help='Task ID (mid, nback, sst)', default=None)
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    fmriprep_dir = op.join(args.bids_dir, 'derivatives', 'fmriprep-20.2.1')
    output_dir = op.join(args.bids_dir, 'derivatives', 'fmriprep_post-process', args.sub, args.ses, args.task)
    os.makedirs(output_dir, exist_ok=True)

    #framewise displacement parameters
    fd_thresh = 0.9
    fd_before = 0
    fd_contig = 0
    fd_after = 0

    #get a list of tasks scans for subject/session
    scans = sorted(glob(op.join(fmriprep_dir,
                                'fmriprep',
                                args.sub,
                                args.ses,
                                'func',
                                '*{task}*bold.nii.gz'.format(task=args.task))))

    run_concat_str = 'run-'
    for i, run in enumerate(scans):
        run_concat_str += '{}+'.format(str(i+1))
    run_concat_str = run_concat_str[:-1]
    tr_concat_fname = op.join(output_dir,
                              '{sub}_{ses}_task-{task}_{run_concat_str}_desc-TRcat.1D'.format(sub=args.sub,
                                                                                      ses=args.ses,
                                                                                      task=args.task,
                                                                                      run_concat_str=run_concat_str))

    if op.isfile(tr_concat_fname):
        os.remove(tr_concat_fname)
    tr_count=0
    censor_data = None
    motion_regressors = None
    print(scans)
    for scan in scans:
        print(scan)

        scan_base = scan.split('_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz')[0]

        #here, we need to delete the first 8 TRs (Siemens/Philips) or
        # first 5 TRs (GE). GE is weird bc it actually acquires 16 TRs, where the first
        # 12 TRs are averaged into one image, and the remaining 4 are normal

        js_fname = op.join(args.bids_dir, args.sub, args.ses, 'func', '{scan_base}_bold.json'.format(scan_base=op.basename(scan_base)))
        js_fname = js_fname.replace('run-', 'run-0')
        js_data = json.load(open(js_fname))
        manufacturer = js_data['Manufacturer']
        if 'GE' in manufacturer:
            trs_to_delete = 5
        elif ('Philips' in manufacturer) or ('Siemens' in manufacturer):
            trs_to_delete = 8

        tmp_img = nib.load(scan)

        #smooth
        smoothed_img = smooth_img(tmp_img, 6)

        tmp_img_mask = masking.compute_epi_mask(tmp_img)

        tmp_img_data = masking.apply_mask(smoothed_img, tmp_img_mask)

        #delete first N TRs because they are dummy TRs from Siemens scanner
        tmp_img_data = np.delete(tmp_img_data, np.arange(trs_to_delete), axis=0)

        #normalize the data to percent signal change
        tmp_img_data_norm = 100.0*(tmp_img_data / np.mean(tmp_img_data, axis=0))

        #unmask data (put back in 4D)
        norm_img = masking.unmask(tmp_img_data_norm, tmp_img_mask)

        #save image mask
        nib.save(tmp_img_mask, op.join(output_dir,
                                       '{}_space-MNI152NLin2009cAsym_res-2_desc-mask.nii.gz'.format(op.basename(scan_base))))
        #save smoothed images
        nib.save(norm_img, op.join(output_dir,
                                   '{}_space-MNI152NLin2009cAsym_res-2_desc-smooth.nii.gz'.format(op.basename(scan_base))))
        #write TR out
        with open(tr_concat_fname, 'a+') as fo:
            fo.write('{}\n'.format(tr_count))

        tr_count = tr_count + np.shape(tmp_img_data)[0]

        # now handle FD censoring and motion parameters
        tmp_regressor_file = '{}_desc-confounds_timeseries.tsv'.format(scan_base)
        fd_cens = fd_censoring(tmp_regressor_file, fd_thresh)
        tmp_censor_data = enhance_censoring(fd_cens, n_contig=fd_contig, n_before=fd_before, n_after=fd_after)[trs_to_delete:]
        tmp_censor_out_name = op.join(output_dir,
                                '{}_motion_censoring.1D'.format(op.basename(scan_base)))
        np.savetxt(tmp_censor_out_name, tmp_censor_data, fmt='%.1d')
        if censor_data is None:
            censor_data = tmp_censor_data
        else:
            censor_data = np.append(censor_data, tmp_censor_data)

        tmp_motion_regressors = motion_parameters(tmp_regressor_file).drop(index=np.arange(trs_to_delete))
        tmp_motion_out_name = op.join(output_dir,
                                '{}_motion_parameters.1D'.format(op.basename(scan_base)))
        tmp_motion_regressors.to_csv(tmp_motion_out_name, sep=' ', header=False, index=False)
        if motion_regressors is None:
            motion_regressors = tmp_motion_regressors
        else:
            motion_regressors = motion_regressors.append(tmp_motion_regressors, ignore_index=True)

    if censor_data is not None:
        censor_out_name = op.join(output_dir,
                                '{sub}_{ses}_task-{task}_{run_concat_str}_motion_censoring.1D'.format(sub=args.sub, ses=args.ses, task=args.task, run_concat_str=run_concat_str))
        np.savetxt(censor_out_name, censor_data, fmt='%.1d')

    if motion_regressors is not None:
        motion_out_name = op.join(output_dir,
                                '{sub}_{ses}_task-{task}_{run_concat_str}_motion_parameters.1D'.format(sub=args.sub, ses=args.ses, task=args.task, run_concat_str=run_concat_str))
        motion_regressors.to_csv(motion_out_name, sep=' ', header=False, index=False)

    #merge individual runs
    smoothed_imgs = sorted(glob(op.join(output_dir,
                                        '*{task}*-smooth.nii.gz'.format(task=args.task))))
    merger = Merge()
    merger.inputs.in_files = smoothed_imgs
    merger.inputs.dimension = 't'
    merger.inputs.tr = 0.8
    merger.inputs.merged_file = op.join(output_dir,
                                        '{sub}_{ses}_task-{task}_{run_concat_str}_space-MNI152NLin2009cAsym_res-2_desc-smooth.nii.gz'.format(sub=args.sub,
                                                                                                     ses=args.ses,
                                                                                                     task=args.task,
                                                                                                     run_concat_str=run_concat_str))
    merger.run()

    #create a brain mask for the concatenated time-series
    masks = sorted(glob(op.join(output_dir,
                                '*{task}*mask.nii.gz'.format(task=args.task))))

    grp_mask = masking.intersect_masks(masks, threshold=1)
    nib.save(grp_mask, op.join(output_dir,
                               '{sub}_{ses}_task-{task}_{run_concat_str}_space-MNI152NLin2009cAsym_res-2_desc-mask.nii.gz'.format(sub=args.sub,
                                                                                          ses=args.ses,
                                                                                          task=args.task,
                                                                                          run_concat_str=run_concat_str)))


if __name__ == '__main__':
    main()
