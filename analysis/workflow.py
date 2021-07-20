#!/usr/bin/env python3
"""
Based on
https://github.com/BIDS-Apps/example/blob/aa0d4808974d79c9fbe54d56d3b47bb2cf4e0a0d/run.py
"""
import os
import os.path as op
from glob import glob
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
    parser.add_argument('--task', required=True, dest='task',
                        help='Task ID (mid, nback, sst)', default=None)
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    code_dir = op.dirname(op.realpath(__file__))

    if args.task is not 'rest':
        cmd = 'python3 {code_dir}/post_process_task.py -b {bids_dir} \
                       --sub {sub} \
                       --ses {ses} \
                       --task {task}'.format(code_dir=code_dir,
                                             bids_dir=args.bids_dir,
                                             sub=args.sub,
                                             ses=args.ses,
                                             task=args.task)
        os.system(cmd)

        eventsfn = sorted(glob(op.join(args.bids_dir, 'sourcedata', args.sub, args.ses, 'func', '*{task}*'.format(task=args.task))))
        for eventfn in eventsfn:
            run = op.basename(eventfn).split('{}_'.format(args.task))[1].split('_bold')[0]

            cmd = 'matlab -nodisplay -r "create_events {bids_dir} {sub} {ses} {task} {run}"; exit'.format(bids_dir=args.bids_dir,
                                                                                                          sub=args.sub,
                                                                                                          ses=args.ses,
                                                                                                          task=args.task,
                                                                                                          run=run)
            os.system(cmd)

        cmd='python3 {code_dir}/merge-events.py -b {bids_dir} \
                                               --sub {sub} \
                                               --ses {ses} \
                                               --task {task}'.format(code_dir=code_dir,
                                                                     bids_dir=args.bids_dir,
                                                                     sub=args.sub,
                                                                     ses=args.ses,
                                                                     task=args.task)
        os.system(cmd)

        #now run the deconvolution
        cmd='python3 {code_dir}/{task}_deconvolve_individual.py -b {bids_dir} \
                                                                --sub {sub} \
                                                                --ses {ses}'.format(code_dir=code_dir,
                                                                                    bids_dir=args.bids_dir,
                                                                                    sub=args.sub,
                                                                                    ses=args.ses,
                                                                                    task=args.task)
        os.system(cmd)

    elif args.task is 'rest':

        cmd='python3 {code_dir}/3dTproject_denoise.py -b {bids_dir} \
                                                      --sub {sub} \
                                                      --ses {ses}'.format(code_dir=code_dir,
                                                                          bids_dir=bids_dir,
                                                                          sub=args.sub,
                                                                          ses=args.ses)

if __name__ == '__main__':
    main()
