import argparse
import math
import os
import os.path as op
import sys
from glob import glob

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
import seaborn as sns
from ddmra import analysis, plot_analysis, run_analyses, utils
from scipy.stats import ks_2samp, normaltest
from sklearn.neighbors import KernelDensity

sys.path.append("/home/data/abcd/code/abcd_fmriprep-analysis")
from utils import get_nvol

sns.set_style("white")


def _get_parser():
    parser = argparse.ArgumentParser(description="Perform QCFC analyses")
    parser.add_argument(
        "--dset",
        dest="dset",
        required=True,
        help="Path to BIDS directory",
    )
    parser.add_argument(
        "--mriqc_dir",
        dest="mriqc_dir",
        required=True,
        help="Path to MRIQC directory",
    )
    parser.add_argument(
        "--preproc_dir",
        dest="preproc_dir",
        required=True,
        help="Path to fMRIPrep directory",
    )
    parser.add_argument(
        "--clean_dir",
        dest="clean_dir",
        required=True,
        help="Path to denoised data directory",
    )
    parser.add_argument(
        "--qcfc_dir",
        dest="qcfc_dir",
        required=True,
        help="Path to QCFC directory",
    )
    parser.add_argument(
        "--sessions",
        dest="sessions",
        default=[None],
        required=False,
        nargs="+",
        help="Sessions identifier, with the ses- prefix.",
    )
    parser.add_argument(
        "--space",
        dest="space",
        default="MNI152NLin2009cAsym",
        required=False,
        help="Standard space, MNI152NLin2009cAsym",
    )
    parser.add_argument(
        "--qc_thresh",
        dest="qc_thresh",
        required=True,
        help="FD threshold",
    )
    parser.add_argument(
        "--desc_list",
        dest="desc_list",
        required=True,
        nargs="+",
        help="Name of the output files in the order [Clean, Clean + Smooth]",
    )
    parser.add_argument(
        "--n_jobs",
        dest="n_jobs",
        required=True,
        help="CPUs",
    )
    return parser


def get_kde(in_vector):
    print("\tKDE for QCFC", flush=True)
    bw_used = 0.05
    a = in_vector.reshape(-1, 1)
    kde = KernelDensity(kernel="gaussian", bandwidth=bw_used).fit(a.reshape(-1, 1))
    s = np.linspace(in_vector.min(), in_vector.max(), num=in_vector.shape[0])
    e = kde.score_samples(s.reshape(-1, 1))
    return s, e


def ks_test(x, y):
    """Kolmogorov–Smirnov test"""
    x = np.array(x)
    y = np.array(y)
    distance, pval = ks_2samp(x, y)

    return distance, pval


def qcfc_plot(in_dir, n_images, qc):
    # Adapted from https://github.com/ME-ICA/ddmra/blob/main/ddmra/plotting.py
    """Plot the results for all three analyses from a workflow run and save to a file.

    This function leverages the output file structure of :func:`workflows.run_analyses`.
    It writes out an image (analysis_results.png) to the output directory.

    Parameters
    ----------
    in_dir : str
        Path to the output directory of a ``run_analyses`` run.
    """
    METRIC_LABELS = {
        "rsfc": "RSFC distributions",
        "qcrsfcD": "QC:RSFC distribution",
        "qcrsfc": r"QC:RSFC $z_{r}$" + "\n(QC = mean FD)",
        "highlow": "High-low motion\n" + r"${\Delta}z_{r}$",
    }
    YLIMS = {
        "rsfc": (-1.5, 1.5),
        "qcrsfcD": (-1.0, 1.0),
        "qcrsfc": (-1.0, 1.0),
        "highlow": (-1.0, 1.0),
    }
    analysis_values = pd.read_table(op.join(in_dir, "analysis_values.tsv.gz"))
    smoothing_curves = pd.read_table(op.join(in_dir, "smoothing_curves.tsv.gz"))
    null_curves = np.load(op.join(in_dir, "null_smoothing_curves.npz"))
    sub_matrices = np.load(op.join(in_dir, "rsfc.npz"))
    corr_mats = sub_matrices["rsfc"]

    fig, axes = plt.subplots(figsize=(32, 8), ncols=len(METRIC_LABELS))

    for i_analysis, (analysis_type, label) in enumerate(METRIC_LABELS.items()):
        if analysis_type == "rsfc":
            xmax = 0
            xmin = 0
            for subject in range(n_images):
                values = corr_mats[subject]
                ax = sns.kdeplot(values, bw_method=0.1, fill=True, ax=axes[i_analysis])
                # print(f"Subject {subject}: {values.mean()}", flush=True)
                xmax = max(xmax, values.max())
                xmin = min(xmin, values.min())
            if xmax > 1:
                xlim_up = math.ceil(xmax * 100) / 100
            else:
                xlim_up = 1
            if xmin < -1:
                xlim_bot = math.ceil(xmin * 100) / 100
            else:
                xlim_bot = -1
            xlim = (xlim_bot, xlim_up)
            ax.set_xlabel(label, fontsize=32, labelpad=-30)
            ax.set_xticks(xlim)
            ax.set_xticklabels(xlim, fontsize=32)
            ax.set_xlim(xlim)

            ax.set_ylabel("")
            ax.set_yticklabels("")
            ymin, ymax = ax.get_ylim()
            ax.vlines(x=0, ymin=ymin, ymax=ymax + 0.1, colors="k", ls="-", lw=5)

        elif analysis_type == "qcrsfcD":
            values = analysis_values["qcrsfc"].values
            smoothing_curve = smoothing_curves["qcrsfc"].values
            # null_curve = null_curves["qcrsfc"][0]

            ax = sns.kdeplot(values, bw_method=0.1, fill=True, color="gray", ax=axes[i_analysis])

            # Create unsmoothed null_curve
            mean_qcs = np.array([np.mean(subj_qc) for subj_qc in qc])
            perm_mean_qcs = np.random.RandomState(seed=0).permutation(mean_qcs)
            perm_qcrsfc_zs = analysis.qcrsfc_analysis(perm_mean_qcs, corr_mats)
            distan, pval = ks_test(values, perm_qcrsfc_zs)
            print(f"\tSimilarity {round((1-distan)*100,1)}%", flush=True)
            sns.kdeplot(
                perm_qcrsfc_zs, bw_method=0.1, color="red", ls="--", lw=5, ax=axes[i_analysis]
            )
            ymin, ymax = ax.get_ylim()
            ax.vlines(x=0, ymin=ymin, ymax=ymax + 0.1, colors="k", ls="-", lw=5)

            ax.annotate(
                f"{round(np.mean(values),2)}"
                + r"$\pm$"
                + f"{round(np.std(values),2)}"
                + f"\n{round((1-distan)*100,1)}% match",
                xy=(1, 1),
                xycoords="axes fraction",
                horizontalalignment="right",
                verticalalignment="top",
                fontsize=32,
            )
            ax.set_xlabel(label, fontsize=32, labelpad=-30)
            ax.set_xticks(YLIMS[analysis_type])
            ax.set_xticklabels(YLIMS[analysis_type], fontsize=32)
            ax.set_xlim(YLIMS[analysis_type])
            ax.set_ylabel("")
            ax.set_yticklabels("")
        else:
            values = analysis_values[analysis_type].values
            smoothing_curve = smoothing_curves[analysis_type].values

            fig, axes[i_analysis] = plot_analysis(
                values,
                analysis_values["distance"],
                smoothing_curve,
                smoothing_curves["distance"],
                null_curves[analysis_type],
                n_lines=50,
                ylim=YLIMS[analysis_type],
                metric_name=label,
                fig=fig,
                ax=axes[i_analysis],
            )

    fig.savefig(op.join(in_dir, "analysis_results.png"), dpi=100)


def main(
    dset,
    mriqc_dir,
    preproc_dir,
    clean_dir,
    qcfc_dir,
    sessions,
    space,
    qc_thresh,
    desc_list,
    n_jobs,
):
    """Run QCFC workflow on a given dataset."""
    # Taken from Taylor's pipeline
    qc_thresh = float(qc_thresh)
    n_jobs = int(n_jobs)
    assert len(desc_list) == 2

    participant_ids_fn = op.join(dset, "participants.tsv")
    participant_ids_df = pd.read_csv(participant_ids_fn, sep="\t")

    if sessions[0] is None:
        temp_ses = glob(op.join(clean_dir, "*", "ses-*"))
        temp_ses = list(set(temp_ses))
        if len(temp_ses) > 0:
            sessions = [op.basename(x) for x in temp_ses]
    if sessions[0] is None:
        img_files = sorted(
            glob(
                op.join(
                    clean_dir, "*", "func", f"*_space-{space}*_desc-{desc_list[0]}_bold.nii.gz"
                )
            )
        )
    else:
        img_files = sorted(
            [
                x
                for session in sessions
                for x in glob(
                    op.join(
                        clean_dir,
                        "*",
                        session,
                        "func",
                        f"*_space-{space}*_desc-{desc_list[0]}_bold.nii.gz",
                    )
                )
            ]
        )

    # TODO: Use the exlcue from MRIQC here !!!!!!!!!!!!!!!!!!!!!!!!!!
    # runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude_qcfc.tsv"), sep="\t")
    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude_qcfc.tsv"), sep="\t")
    runs_to_exclude = runs_to_exclude_df["bids_name"].tolist()
    prefixes_tpl = tuple(runs_to_exclude)
    img_clean_files = [x for x in img_files if not op.basename(x).startswith(prefixes_tpl)]

    censored_qcs = []
    for img_clean_file in img_clean_files:
        # print(op.basename(img_clean_file), flush=True)
        img_clean_name = op.basename(img_clean_file)
        prefix = img_clean_name.split("space-")[0].rstrip("_")
        subject = img_clean_name.split("_")[0]
        temp_session = img_clean_name.split("_")[1]
        if temp_session.startswith("ses-"):
            preproc_subj_func_dir = op.join(preproc_dir, subject, temp_session, "func")
            nuis_subj_dir = op.join(clean_dir, subject, temp_session, "func")
        else:
            preproc_subj_func_dir = op.join(preproc_dir, subject, "func")
            nuis_subj_dir = op.join(clean_dir, subject, "func")

        # Collect important files
        confounds_files = glob(
            op.join(preproc_subj_func_dir, f"{prefix}*_desc-confounds_timeseries.tsv")
        )
        assert len(confounds_files) == 1
        confounds_file = confounds_files[0]

        censor_files = glob(
            op.join(nuis_subj_dir, f"{prefix}*_space-{space}*_censoring{qc_thresh}.1D")
        )
        assert len(censor_files) == 1
        tr_censor = pd.read_csv(censor_files[0], header=None)
        tr_censor_idx = tr_censor.index[tr_censor[0] == 0].tolist()

        confounds_df = pd.read_csv(confounds_file, sep="\t")
        qc = confounds_df["framewise_displacement"].values
        qc = np.nan_to_num(qc, 0)

        # Get dummy_scans from paticipants.tsv
        manufacturer = participant_ids_df.loc[
            participant_ids_df["participant_id"] == subject, "Manufacturer"
        ].values[0]
        if manufacturer == "GE":
            dummy_scans = 5
        elif (manufacturer == "Siemens") or (manufacturer == "Philips"):
            dummy_scans = 8
        censored_qc = np.delete(qc[dummy_scans:], tr_censor_idx)
        assert get_nvol(img_clean_file) == len(censored_qc)

        censored_qcs.append(censored_qc)

    # ###################
    # QCFC analyses
    # ###################
    assert len(img_clean_files) == len(censored_qcs)
    os.makedirs(qcfc_dir, exist_ok=True)
    analysis_results = op.join(qcfc_dir, "new_analysis_results.png")
    if not op.exists(op.join(qcfc_dir, "null_smoothing_curves.npz")):
        print(f"\tRun QCFC workflow on {len(img_clean_files)} subjects", flush=True)
        print(f"\tUse {len(censored_qcs)} fd vectors", flush=True)
        run_analyses(
            img_clean_files,
            censored_qcs,
            out_dir=qcfc_dir,
            n_iters=10000,
            n_jobs=n_jobs,
            qc_thresh=qc_thresh,
        )
    # Create QC plots
    if not op.exists(analysis_results):
        qcfc_plot(qcfc_dir, len(img_clean_files), censored_qcs)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
