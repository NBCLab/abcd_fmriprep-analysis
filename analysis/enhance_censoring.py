"""
Update a file denoting censored volumes (e.g., high-motion volumes) to censor
volumes before, after, and between.
"""
import argparse
from os.path import splitext, join, basename, dirname

import numpy as np


def _to_vec(arr):
    """
    Convert bool-like 2D array to 1D vector.
    Assumes TRxCensored-Vol format.
    """
    if len(arr.shape) > 2:
        raise Exception('Not a 2D array.')
    elif len(arr.shape) == 1:
        return arr
    else:
        vec = np.sum(arr, axis=1)
        if np.any(vec > 1):
            raise Exception('Boolean censoring array does not appear to be properly formatted.')
        return vec


def _to_arr(vec):
    """
    Convert bool-like 1D vector to 2D array.
    """
    # I think this is the ugliest way of doing this, but...
    if len(vec.shape) != 1:
        raise Exception('Not a 1D vector.')

    n_trs = vec.size
    n_cens = np.sum(vec)

    arr = np.zeros((n_trs, int(n_cens)), int)

    cols = range(int(n_cens))
    rows = np.where(vec)[0]
    arr[rows, cols] = 1
    return arr


def main(censor_data, n_contig=2, n_before=1, n_after=2):
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


def _get_parser():
    """
    Argument parser for enhance_censoring
    """
    parser = argparse.ArgumentParser(description='Enhance censoring.')
    # Required arguments
    parser.add_argument('in_file',
                        type=str,
                        help='1D or txt file containing censoring index')
    parser.add_argument('out_file',
                        type=str,
                        help='Output file')

    # Optional arguments
    parser.add_argument('--between',
                        dest='n_contig',
                        action='store',
                        type=int,
                        help=('Number of volumes between outliers to censor'),
                        default=2)
    parser.add_argument('--pre',
                        dest='n_before',
                        action='store',
                        type=int,
                        help=('Number of volumes before outliers to censor'),
                        default=1)
    parser.add_argument('--post',
                        dest='n_after',
                        action='store',
                        type=int,
                        help=('Number of volumes after outliers to censor'),
                        default=2)
    return parser


def _main(argv=None):
    """
    Compile arguments for showxcorrx workflow.
    """
    args = vars(_get_parser().parse_args(argv))

    censor_data = np.loadtxt(args.in_file)

    out_data = main(censor_data, args.n_contig, args.n_before, args.n_after)

    np.savetxt(args.out_file, out_data, fmt='%i', delimiter='\t')


if __name__ == '__main__':
    _main()
