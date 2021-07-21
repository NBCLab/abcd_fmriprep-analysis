import os
import os.path as op
import pandas as pd
import json as js
import numpy as np


def get_acompcor(regressfile, out_file):
    df_in = pd.read_csv(regressfile, sep='\t')
    with open('{0}.json'.format(regressfile.replace('.tsv', ''))) as json_file:
        data = js.load(json_file)
        acompcors = sorted([x for x in data.keys() if 'a_comp_cor' in x])
        # for muschelli 2014
        acompcor_list_CSF = [x for x in acompcors if data[x]['Mask'] == 'CSF']
        acompcor_list_CSF = acompcor_list_CSF[0:3]
        acompcor_list_WM = [x for x in acompcors if data[x]['Mask'] == 'WM']
        acompcor_list_WM = acompcor_list_WM[0:3]
        acompcor_list = []
        acompcor_list.extend(acompcor_list_CSF)
        acompcor_list.extend(acompcor_list_WM)

    df_out = df_in[acompcor_list]
    df_out = df_out.replace('n/a', 0)
    df_out = df_out.drop([i for i in range(8)])
    df_out.to_csv(out_file, sep='\t', header=False, index=False)


def fd_censoring(tmp_file, fd_thresh):
    df_in = pd.read_csv(tmp_file, sep='\t')
    fd = df_in['framewise_displacement']
    fd = fd[1:,]
    fd_cens = np.ones(len(fd.index)+1)
    fd_list = []
    for i, tmp_fd in enumerate(fd):
        if float(tmp_fd) > fd_thresh:
            fd_list.append(i+1)
    fd_cens[fd_list] = 0
    return fd_cens


def enhance_censoring(censor_data, n_contig=2, n_before=1, n_after=2):
    """
    Censor non-contiguous TRs based on outlier file.
    """

    censor_vec = 1 - censor_data.astype(int)

    out_vec = np.zeros(censor_vec.shape, int)
    cens_vols = np.where(censor_vec)[0]

    # Flag volumes before each outlier
    temp = np.copy(cens_vols)
    for trs_before in range(1, n_before+1):
        temp = np.hstack((temp, cens_vols-trs_before))
    cens_vols = np.unique(temp)
    all_vols = np.arange(len(censor_vec))

    # Remove censored index outside range
    # Unnecessary here but keeps everything interpretable
    cens_vols = np.intersect1d(all_vols, cens_vols)

    # Flag volumes after each outlier
    temp = np.copy(cens_vols)
    for trs_after in range(1, n_after+1):
        temp = np.hstack((temp, cens_vols+trs_after))
    cens_vols = np.unique(temp)
    all_vols = np.arange(len(censor_vec))

    # Remove censored index outside range
    cens_vols = np.intersect1d(all_vols, cens_vols)

    # Flag orphan volumes (unflagged volumes between flagged ones)
    temp = np.copy(cens_vols)
    contig_idx = np.where(np.diff(cens_vols) < n_contig)[0]
    for idx in contig_idx:
        start = cens_vols[idx]
        end = cens_vols[idx+1]
        temp = np.hstack((temp, np.arange(start, end)))
    cens_vols = np.unique(temp)

    # Create improved censor vector
    out_vec[cens_vols] = 1

    out_data = 1 - out_vec

    return out_data


def motion_parameters(tmp_file, derivatives=None):
    df_in = pd.read_csv(tmp_file, sep='\t')
    if derivatives:
        motion_labels = ['trans_x', 'trans_x_derivative1', 'trans_y', 'trans_y_derivative1', 'trans_z', 'trans_z_derivative1', 'rot_x', 'rot_x_derivative1', 'rot_y', 'rot_y_derivative1', 'rot_z', 'rot_z_derivative1']
    else:
        motion_labels = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    motion_regressors = df_in[motion_labels]
    return motion_regressors

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
