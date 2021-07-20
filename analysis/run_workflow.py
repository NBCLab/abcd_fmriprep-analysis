import os
import os.path as op
import pandas as pd
import subprocess
import time
import argparse


def submit_job(job_name, cores, partition, output_file, error_file, queue, account, command):

    os.makedirs(op.dirname(output_file), exist_ok=True)
    os.makedirs(op.dirname(error_file), exist_ok=True)

    cmd = 'sbatch -J {job_name} \
                  -c {cores} \
                  -p {partition} \
                  -o {output_file} \
                  -e {error_file} \
                  --qos {queue} \
                  --account {account} \
                  --wrap="{command}"'.format(job_name=job_name,
                                           cores=cores,
                                           partition=partition,
                                           output_file=output_file,
                                           error_file=error_file,
                                           queue=queue,
                                           account=account,
                                           command=command)
    print(cmd)
    os.system(cmd)

def get_parser():
    parser = argparse.ArgumentParser(description='Perform whole-brain task '
             'task analysis on fMRIPREPed ABCD data. Example usage: '
             'python3 /home/data/abcd/code/abcd_task-analysis/run_workflow.py '
                      '--bids_dir /home/data/abcd/abcd-hispanic-via ')
    parser.add_argument('--bids_dir', required=True, dest='bids_dir')
    parser.add_argument('--tasks', required=False, dest='tasks', nargs='+', type=str, default=['MID', 'nback', 'SST'])
    parser.add_argument('--sessions', required=False, dest='sessions', nargs='+', default=['ses-baselineYear1Arm1', 'ses-2yearfollowupyarm1'])
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    #tasks = "'{}'".format(' '.join(args.tasks).replace(' ', "' '"))
    #sessions = "{}".format(' '.join(args.sessions))
    tasks = args.tasks
    sessions = args.sessions
    print(tasks)
    print(sessions)

    bids_dir = args.bids_dir
    participant_ids_fn = op.join(bids_dir, 'participants.tsv')
    participant_ids = pd.read_csv(participant_ids_fn, sep='\t')['participant_id']

    for pid in participant_ids:
        for ses in sessions:
            for task in tasks:

                cmd = 'python3 /home/data/abcd/code/abcd_task-analysis/workflow.py \
                               --b {bids_dir} \
                               --sub {sub} --ses {ses} \
                               --task {task}'.format(bids_dir=bids_dir,
                                                     sub=pid,
                                                     ses=ses,
                                                     task=task)

                getJobsN =  subprocess.Popen("squeue -u $USER | wc -l", shell=True, stdout=subprocess.PIPE).stdout
                JobsN =  getJobsN.read()
                while int(JobsN.decode("utf-8").strip('\n')) > 20:
                    time.sleep(30)
                    getJobsN =  subprocess.Popen("squeue -u $USER | wc -l", shell=True, stdout=subprocess.PIPE).stdout
                    JobsN =  getJobsN.read()

                submit_job('analysis-{sub}-{ses}-{task}'.format(sub=pid, ses=ses, task=task),
                            cores=6,
                            partition='investor',
                            output_file=op.join(op.dirname(bids_dir), 'code', task, 'out', '{}-{}'.format(pid, ses)),
                            error_file=op.join(op.dirname(bids_dir), 'code', task, 'err', '{}-{}'.format(pid, ses)),
                            queue='pq_nbc',
                            account='iacc_nbc',
                            command=cmd)
                exit()

if __name__ == '__main__':
    main()
