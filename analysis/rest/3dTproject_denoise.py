#!/usr/bin/env python3
"""
Based on
https://github.com/BIDS-Apps/example/blob/aa0d4808974d79c9fbe54d56d3b47bb2cf4e0a0d/run.py
"""
import os
import os.path as op
import shutil
from glob import glob
import argparse
import pandas as pd
import json as js
import numpy as np
import sys
sys.path.append('/home/data/abcd/code/abcd_fmriprep-analysis')
from utils import fd_censoring
from utils import motion_parameters
from utils import get_acompcor
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

    return parser


def main(argv=None):
    args = get_parser().parse_args(argv)

    #framewise displacement parameters
    fd_thresh = 0.35
    fd_before = 1
    fd_contig = 0
    fd_after = 1

    in_dir = op.join(args.bids_dir, 'derivatives/fmriprep-20.2.1', 'fmriprep', args.sub, args.ses)
    out_dir = op.join(args.bids_dir, 'derivatives/fmriprep_post-process', args.sub, args.ses, 'rest')
    os.makedirs(out_dir, exist_ok=True)

    rest_files = sorted(glob(op.join(in_dir, 'func',  '*task-rest*confounds_timeseries.tsv')))
    for tmp_rs_file in rest_files:
        acompcor_regressors=op.splitext(op.basename(tmp_rs_file))[0]
        acompcor_regressors=op.join(out_dir, '{0}_acompcor.1D'.format(acompcor_regressors))

        get_acompcor(tmp_rs_file, acompcor_regressors)

        niifile=op.basename(tmp_rs_file).rstrip('_desc-confounds_timeseries.tsv')
        nii_fn=op.join(in_dir, 'func', '{}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'.format(niifile))
        mask_fn=op.join(in_dir, 'func', '{}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'.format(niifile))

        out_fn='{0}-clean.nii'.format(op.basename(nii_fn).split('.')[0])

        #remove first 8 TRs
        #cmd="3dcalc -a '{input}[8..$]' -expr 'a' -prefix {output} ".format(input=nii_fn, output=op.join(out_dir, 'tmp.nii'))
        #print(cmd)
        #os.system(cmd)

        js_fname = op.join(args.bids_dir, args.sub, args.ses, 'func', '{}_bold.json'.format(niifile))
        js_fname = js_fname.replace('run-', 'run-0')
        js_data = js.load(open(js_fname))
        manufacturer = js_data['Manufacturer']
        if 'GE' in manufacturer:
            trs_to_delete = 5
        elif ('Philips' in manufacturer) or ('Siemens' in manufacturer):
            trs_to_delete = 8

        #get trs to remove
        fd_cens = fd_censoring(tmp_rs_file, fd_thresh)
        censor_data = enhance_censoring(fd_cens, n_contig=fd_contig, n_before=fd_before, n_after=fd_after)[trs_to_delete:]
        censor_out_name = op.join(out_dir,
                                '{}_motion_censoring.1D'.format(niifile))
        np.savetxt(censor_out_name, censor_data, fmt='%.1d')
        tr_censor = pd.read_csv(op.join(out_dir, '{0}_motion_censoring.1D'.format(niifile)), header=None)
        tr_keep = tr_censor.index[tr_censor[0] == 1].tolist()

        motion_regressors = motion_parameters(tmp_rs_file, derivatives=True).drop(index=np.arange(trs_to_delete))
        motion_out_name = op.join(out_dir,
                                '{}_motion_parameters.1D'.format(niifile))
        motion_regressors.to_csv(motion_out_name, sep=' ', header=False, index=False)

        cmd='3dTproject \
             -input {input_file}[{trs_to_delete}..$] \
             -polort 1 \
             -prefix {output_file} \
             -ort {regressor_file} \
             -ort {motion_parameters} \
             -passband 0.01 0.10 \
             -mask {mask_file}'.format(input_file=nii_fn,
                                       trs_to_delete=trs_to_delete,
                                       output_file=op.join(out_dir, 'tmp.nii'),
                                       regressor_file=op.join(out_dir, acompcor_regressors),
                                       motion_parameters=motion_out_name,
                                       mask_file=mask_fn)
        os.system(cmd)
        cmd = "3dTcat -prefix {out_file} {in_file}'{tr_keep}'".format(in_file=op.join(out_dir, 'tmp.nii'),
                                                                      tr_keep=tr_keep,
                                                                      out_file=op.join(out_dir, out_fn))
        os.system(cmd)
        cmd='gzip {}'.format(op.join(out_dir, out_fn))
        os.system(cmd)
        os.remove(op.join(out_dir, 'tmp.nii'))

        #do the same thing, but blur it with 6mm FWHM
        out_fn = op.basename(nii_fn)
        out_fn='{0}-smooth+clean.nii'.format(out_fn.split('.')[0])
        cmd='3dTproject \
             -input {input_file}[{trs_to_delete}..$] \
             -polort 1 \
             -blur 6\
             -prefix {output_file} \
             -ort {regressor_file} \
             -ort {motion_parameters} \
             -passband 0.01 0.10 \
             -mask {mask_file}'.format(input_file=nii_fn,
                                       trs_to_delete=trs_to_delete,
                                       output_file=op.join(out_dir, 'tmp.nii'),
                                       regressor_file=op.join(out_dir, acompcor_regressors),
                                       motion_parameters=motion_out_name,
                                       mask_file=mask_fn)
        os.system(cmd)
        cmd = "3dTcat -prefix {out_file} {in_file}'{tr_keep}'".format(in_file=op.join(out_dir, 'tmp.nii'),
                                                                      tr_keep=tr_keep,
                                                                      out_file=op.join(out_dir, out_fn))
        os.system(cmd)
        cmd='gzip {}'.format(op.join(out_dir, out_fn))
        os.system(cmd)
        os.remove(op.join(out_dir, 'tmp.nii'))

        shutil.copyfile(mask_fn, op.join(out_dir, op.basename(mask_fn)))


if __name__ == '__main__':
    main()
