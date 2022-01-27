import argparse
import os.path as op
import subprocess
import sys
import time

import pandas as pd

sys.path.append("/home/data/abcd/code/abcd_fmriprep-analysis")
from utils import submit_job


def get_parser():
    parser = argparse.ArgumentParser(
        description="Perform whole-brain task "
        "task analysis on fMRIPREPed ABCD data. Example usage: "
        "python3 /home/data/abcd/code/abcd_task-analysis/run_workflow.py "
        "--bids_dir /home/data/abcd/abcd-hispanic-via "
    )
    parser.add_argument("--bids_dir", required=True, dest="bids_dir")
    parser.add_argument(
        "--tasks",
        required=False,
        dest="tasks",
        nargs="+",
        type=str,
        default=["MID", "nback", "SST", "rest"],
    )
    parser.add_argument(
        "--sessions",
        required=False,
        dest="sessions",
        nargs="+",
        default=["ses-baselineYear1Arm1", "ses-2yearfollowupyarm1"],
    )
    parser.add_argument("--rois", required=False, dest="rois", nargs="+", type=str)
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    # tasks = "'{}'".format(' '.join(args.tasks).replace(' ', "' '"))
    # sessions = "{}".format(' '.join(args.sessions))
    tasks = args.tasks
    sessions = args.sessions
    print(tasks)
    print(sessions)

    bids_dir = args.bids_dir
    participant_ids_fn = op.join(bids_dir, "participants.tsv")
    participant_ids = pd.read_csv(participant_ids_fn, sep="\t")["participant_id"]

    for pid in participant_ids:
        print(pid)
        for ses in sessions:
            print(ses)
            for task in tasks:
                print(task)

                if not args.rois:
                    cmd = "python3 /home/data/abcd/code/abcd_fmriprep-analysis/analysis/workflow.py \
                                   --b {bids_dir} \
                                   --sub {sub} --ses {ses} \
                                   --task {task}".format(
                        bids_dir=bids_dir, sub=pid, ses=ses, task=task
                    )

                else:
                    rois = "{}".format(" ".join(args.rois))
                    print(rois)
                    cmd = "python3 /home/data/abcd/code/abcd_fmriprep-analysis/analysis/workflow.py \
                                   --b {bids_dir} \
                                   --sub {sub} --ses {ses} \
                                   --task {task} --roi {roi}".format(
                        bids_dir=bids_dir, sub=pid, ses=ses, task=task, roi=rois
                    )

                getJobsN = subprocess.Popen(
                    "squeue -u $USER | wc -l", shell=True, stdout=subprocess.PIPE
                ).stdout
                JobsN = getJobsN.read()
                while int(JobsN.decode("utf-8").strip("\n")) > 20:
                    time.sleep(30)
                    getJobsN = subprocess.Popen(
                        "squeue -u $USER | wc -l", shell=True, stdout=subprocess.PIPE
                    ).stdout
                    JobsN = getJobsN.read()

                submit_job(
                    "analysis-{sub}-{ses}-{task}".format(sub=pid, ses=ses, task=task),
                    cores=4,
                    partition="investor",
                    output_file=op.join(
                        op.dirname(bids_dir), "code", "log", task, "out", "{}-{}".format(pid, ses)
                    ),
                    error_file=op.join(
                        op.dirname(bids_dir), "code", "log", task, "err", "{}-{}".format(pid, ses)
                    ),
                    queue="pq_nbc",
                    account="iacc_nbc",
                    command=cmd,
                )


if __name__ == "__main__":
    main()
