import argparse
import json
import os.path as op
from glob import glob

import matplotlib.pyplot as plt
import pandas as pd
import ptitprince as pt
import seaborn as sns
from kneed import KneeLocator
from numpy import mean


def _get_parser():
    parser = argparse.ArgumentParser(description="Perform QCFC analyses")
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
        "--sessions",
        dest="sessions",
        default=[None],
        required=False,
        nargs="+",
        help="Sessions identifier, with the ses- prefix.",
    )
    return parser


def violin_plot(new_df, avg_CSF, avg_WM, avg_comb, mriqc_dir):
    sns.set(style="whitegrid", font_scale=1.5)
    _, ax = plt.subplots(figsize=(8, 5))

    ort = "v"
    pal = ["#0066ff", "#00cc66", "#ff6600"]
    dx = "Group"
    dy = "Scores"
    hue_order = ["CSF", "WM", "CSF+WM"]
    pt.half_violinplot(
        x=dx,
        y=dy,
        data=new_df,
        hue_order=hue_order,
        palette=pal,
        bw=0.5,
        cut=0.0,
        scale="area",
        width=0.6,
        dodge=False,
        inner=None,
        orient=ort,
    )
    sns.stripplot(
        x=dx,
        y=dy,
        data=new_df,
        hue_order=hue_order,
        palette=pal,
        edgecolor="white",
        dodge=False,
        size=3,
        jitter=1,
        zorder=0,
        orient=ort,
    )
    sns.boxplot(
        x=dx,
        y=dy,
        data=new_df,
        hue_order=hue_order,
        palette=pal,
        width=0.15,
        zorder=10,
        dodge=True,
        showcaps=True,
        boxprops={"alpha": 0.6, "zorder": 10},
        showfliers=True,
        whiskerprops={"linewidth": 2, "zorder": 10},
        saturation=1,
        orient=ort,
    )

    ax.text(
        0.02,
        0.98,
        f"CSF: {avg_CSF}\nWM: {avg_WM}\nCSF+WM: {avg_comb}",
        ha="left",
        va="top",
        transform=ax.transAxes,
    )
    ax.set_xlabel("aCompCor Mask")
    ax.set_ylabel("Number of components")
    plt.savefig(
        op.join(mriqc_dir, "..", "acompcor.png"),
        bbox_inches="tight",
    )


def main(
    mriqc_dir,
    preproc_dir,
    sessions,
):
    """Run QCFC workflow on a given dataset."""
    if sessions[0] is None:
        temp_ses = glob(op.join(preproc_dir, "*", "ses-*"))
        temp_ses = list(set(temp_ses))
        if len(temp_ses) > 0:
            sessions = [op.basename(x) for x in temp_ses]
    if sessions[0] is None:
        confounds_files = sorted(
            glob(op.join(preproc_dir, "*", "func", "*task-rest*_desc-confounds_timeseries.tsv"))
        )
    else:
        confounds_files = sorted(
            [
                x
                for session in sessions
                for x in glob(
                    op.join(
                        preproc_dir,
                        "*",
                        session,
                        "func",
                        "*task-rest*_desc-confounds_timeseries.tsv",
                    )
                )
            ]
        )

    runs_to_exclude_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")
    runs_to_exclude = runs_to_exclude_df["bids_name"].tolist()
    prefixes_tpl = tuple(runs_to_exclude)
    confounds_clean_files = [
        x for x in confounds_files if not op.basename(x).startswith(prefixes_tpl)
    ]

    kn_CSF_lst = []
    kn_WM_lst = []
    kn_comb_lst = []
    for confounds_clean_file in confounds_clean_files:
        confounds_json_file = confounds_clean_file.replace(".tsv", ".json")
        with open(confounds_json_file) as json_file:
            data = json.load(json_file)

        ccompcors = sorted([x for x in data.keys() if "c_comp_cor" in x])
        ccompcors = ccompcors[:25]
        wcompcors = sorted([x for x in data.keys() if "w_comp_cor" in x])
        wcompcors = wcompcors[:25]
        acompcors = sorted([x for x in data.keys() if "a_comp_cor" in x])
        acompcors = acompcors[:25]
        variance_list_CSF = [
            data[x]["VarianceExplained"] for x in ccompcors if data[x]["Mask"] == "CSF"
        ]
        variance_list_WM = [
            data[x]["VarianceExplained"] for x in wcompcors if data[x]["Mask"] == "WM"
        ]
        variance_list_comb = [
            data[x]["VarianceExplained"] for x in acompcors if data[x]["Mask"] == "combined"
        ]

        lst_CSF = list(range(1, len(variance_list_CSF) + 1))
        lst_WM = list(range(1, len(variance_list_WM) + 1))
        lst_comb = list(range(1, len(variance_list_comb) + 1))
        # print(f"\t{lst_CSF}\n\t{variance_list_CSF}", flush=True)

        kn_CSF = KneeLocator(lst_CSF, variance_list_CSF, curve="convex", direction="decreasing")
        kn_WM = KneeLocator(lst_WM, variance_list_WM, curve="convex", direction="decreasing")
        kn_comb = KneeLocator(lst_comb, variance_list_comb, curve="convex", direction="decreasing")

        if kn_CSF.knee is None:
            kn_CSF_lst.append(0)
        else:
            kn_CSF_lst.append(kn_CSF.knee)

        if kn_WM.knee is None:
            kn_WM_lst.append(0)
        else:
            kn_WM_lst.append(kn_WM.knee)

        if kn_comb.knee is None:
            kn_comb_lst.append(0)
        else:
            kn_comb_lst.append(kn_comb.knee)

    avg_CSF = round(mean(kn_CSF_lst))
    avg_WM = round(mean(kn_WM_lst))
    avg_comb = round(mean(kn_comb_lst))
    print(f"\tMean number of CSF components: {avg_CSF}", flush=True)
    print(f"\tMean number of WM components: {avg_WM}", flush=True)
    print(f"\tMean number of combined components: {avg_comb}", flush=True)

    label_CSF_lst = ["CSF"] * len(kn_CSF_lst)
    label_WM_lst = ["WM"] * len(kn_WM_lst)
    label_comb_lst = ["CSF+WM"] * len(kn_WM_lst)

    kn_lst = kn_CSF_lst + kn_WM_lst + kn_comb_lst
    label_lst = label_CSF_lst + label_WM_lst + label_comb_lst

    new_df = pd.DataFrame()
    new_df["Group"] = label_lst
    new_df["Scores"] = kn_lst
    new_df.to_csv(op.join(mriqc_dir, "..", "acompcor.tsv"), sep="\t", index=False)

    violin_plot(new_df, avg_CSF, avg_WM, avg_comb, mriqc_dir)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
