import os
import os.path as op
import pandas as pd
import subprocess
import time
import argparse


def get_parser():
    parser = argparse.ArgumentParser(description='Download ABCD participant data '
             'and run MRIQC and fMRIPREP singularity images. Example usage: '
             'python3 /home/data/abcd/code/abcd_fmriprep/run_workflow.py '
                      '--project_dir /home/data/abcd/abcd-hispanic-via '
                      '--work_dir /scratch/nbc/miriedel/abcd_work')
    parser.add_argument('--project_dir', required=True, dest='project_dir')
    parser.add_argument('--work_dir', required=False, dest='work_dir', default='~/abcd_workdir')
    parser.add_argument('--modalities', required=False, dest='modalities', nargs='+', type=str, default=['anat', 'func'])
    parser.add_argument('--sessions', required=False, dest='sessions', nargs='+', default=['baseline_year_1_arm_1', '2_year_follow_up_y_arm_1'])
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    modalities = "'{}'".format(' '.join(args.modalities).replace(' ', "' '"))
    sessions = "{}".format(' '.join(args.sessions))

    project_directory = args.project_dir
    bids_dir = op.join(project_directory, 'dset')
    participant_ids_fn = op.join(bids_dir, 'participants.tsv')
    participant_ids = pd.read_csv(participant_ids_fn, sep='\t')['participant_id']

    config_file = op.join(project_directory, 'code', '.config.ini')
    qc_spreadsheet = op.join(op.dirname(project_directory), 'code', 'spreadsheets', 'abcd_fastqc01.txt')
    work_dir = args.work_dir

    for pid in participant_ids:

        if not op.isdir(op.join(bids_dir, 'derivatives', 'fmriprep-20.2.1', 'fmriprep', pid)):
            cmd = 'python3 /home/data/abcd/code/abcd_fmriprep/workflow.py \
                           --bids_dir {bids_dir} \
                           --work_dir {work_dir} \
                           --config {config_file} \
                           --qc {qc_spreadsheet} \
                           --sub {sub} --sessions {sessions} \
                           --modalities {modalities}'.format(project_directory=project_directory,
                                                            bids_dir=bids_dir,
                                                            work_dir=work_dir,
                                                            config_file=config_file,
                                                            qc_spreadsheet=qc_spreadsheet,
                                                            sub=pid,
                                                            sessions=sessions,
                                                            modalities=modalities)

            getJobsN =  subprocess.Popen("squeue -u $USER | wc -l", shell=True, stdout=subprocess.PIPE).stdout
            JobsN =  getJobsN.read()
            while int(JobsN.decode("utf-8").strip('\n')) > 20:
                time.sleep(30)
                getJobsN =  subprocess.Popen("squeue -u $USER | wc -l", shell=True, stdout=subprocess.PIPE).stdout
                JobsN =  getJobsN.read()
            os.system(cmd)
            exit()

if __name__ == '__main__':
    main()
