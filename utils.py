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


def motion_parameters(tmp_file, derivatives=None):
    df_in = pd.read_csv(tmp_file, sep='\t')
    if derivatives:
        motion_labels = ['trans_x', 'trans_x_derivative1', 'trans_y', 'trans_y_derivative1', 'trans_z', 'trans_z_derivative1', 'rot_x', 'rot_x_derivative1', 'rot_y', 'rot_y_derivative1', 'rot_z', 'rot_z_derivative1']
    else:
        motion_labels = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    motion_regressors = df_in[motion_labels]
    return motion_regressors
