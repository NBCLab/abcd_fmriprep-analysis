import argparse
import os
import os.path as op
import shutil
from glob import glob

import numpy as np
import pandas as pd


def get_parser():
    parser = argparse.ArgumentParser(description='Run MRIQC on BIDS dataset.')
    parser.add_argument('-b', '--bidsdir', required=True, dest='bids_dir',
                        help=('Output directory for BIDS dataset and '
                              'derivatives.'))
    parser.add_argument('--sub', required=True, dest='sub',
                        help='The label of the subject to analyze.')
    parser.add_argument('--ses', required=False, dest='ses',
                        help='Session number', default=None)
    parser.add_argument('--task', required=False, dest='task',
                        help='Task ID (mid, nback, sst)', default=None)
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    derivatives_dir = op.join(args.bids_dir, 'derivatives', 'fmriprep_post-process')
    os.makedirs(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files'), exist_ok=True)
    #this part will be weird because the MATALB file outputs FOR EACH RUN
    #events for both runs, but they are differentiated by "scan1 and scan2"
    #in the filenames
    #so, we are going to grab the "scan1" files from "run-01" filenames,
    # and "scan2" files from "run-02" filenames

    if args.task == 'nback':
        for block in [0,2]:

            for stim in ['negface', 'neutface', 'posface', 'place']:

                dur_array = []
                onset_array = []
                for i in [1,2]:

                    block_onset_files = sorted(glob(op.join(derivatives_dir, args.sub, args.ses, args.task, 'events', '*run-0{run}*scan{run}*{block}_back_{stim}_block.txt'.format(run=i, block=block, stim=stim))))
                    block_dur_files = sorted(glob(op.join(derivatives_dir, args.sub, args.ses, args.task, 'events', '*run-0{run}*scan{run}*{block}_back_{stim}_block_dur.txt'.format(run=i, block=block, stim=stim))))

                    if block_onset_files:
                        for onset_fn in block_onset_files:
                            with open(onset_fn, 'r') as fo:
                                tmp_onset = float(fo.read())
                                onset_array.append(tmp_onset)
                            with open(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-{run}_{block}_back_{stim}.txt'.format(run=i, block=block, stim=stim)), 'a') as fo:
                                fo.write('{}\n'.format(tmp_onset))

                        for dur_fn in block_dur_files:
                            with open(dur_fn, 'r') as fo:
                                tmp_dur = float(fo.read())
                                dur_array.append(tmp_dur)
                            with open(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-{run}_{block}_back_{stim}_duration.txt'.format(run=i, block=block, stim=stim)), 'a') as fo:
                                fo.write('{}'.format(np.unique(tmp_dur)[0]))


                if len(onset_array) > 1:
                    with open(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-1+2_{block}_back_{stim}.txt'.format(block=block, stim=stim)), 'a') as fo:
                        for onset in onset_array:
                            fo.write('{}\n'.format(onset))

                if len(onset_array) > 1:
                    with open(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-1+2_{block}_back_{stim}_duration.txt'.format(block=block, stim=stim)), 'a') as fo:
                        fo.write('{}'.format(np.unique(dur_array)[0]))

    elif args.task == 'MID':
        for phase in ['antic', 'neg_feedback', 'pos_feedback']:

                for outcome in ['large_loss', 'small_loss', 'large_reward', 'small_reward', 'neutral']:

                    onset_array = []

                    for i in [1,2]:
                        event_onset_files = sorted(glob(op.join(derivatives_dir, args.sub, args.ses, args.task, 'events', '*run-0{run}*scan{run}*{outcome}*{phase}.txt'.format(run=i, outcome=outcome, phase=phase))))[0]
                        with open(event_onset_files, 'r') as fo:
                            tmp_onset = fo.read()
                            onset_array.append(tmp_onset)
                        shutil.copyfile(event_onset_files, op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-{run}_{outcome}_{phase}.txt'.format(run=i, outcome=outcome, phase=phase)))

                    with open(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-1+2_{outcome}_{phase}.txt'.format(outcome=outcome, phase=phase)), 'a') as fo:
                        for onset in onset_array:
                            fo.write(onset)

    elif args.task == 'SST':
        for correct in ['correct', 'incorrect']:

                for instruction in ['stop', 'go']:

                    onset_array = []

                    for i in [1,2]:
                        event_onset_files = sorted(glob(op.join(derivatives_dir, args.sub, args.ses, args.task, 'events', '*run-0{run}*scan{run}*{correct}*{instruction}.txt'.format(run=i, correct=correct, instruction=instruction))))[0]
                        with open(event_onset_files, 'r') as fo:
                            tmp_onset = fo.read()
                            onset_array.append(tmp_onset)
                        shutil.copyfile(event_onset_files, op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-{run}_{correct}_{instruction}.txt'.format(run=i, correct=correct, instruction=instruction)))

                    with open(op.join(derivatives_dir, args.sub, args.ses, args.task, 'timing_files', 'run-1+2_{correct}_{instruction}.txt'.format(correct=correct, instruction=instruction)), 'a') as fo:
                        for onset in onset_array:
                            fo.write(onset)


if __name__ == '__main__':
    main()
