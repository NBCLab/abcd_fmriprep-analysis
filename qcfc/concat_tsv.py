import os.path as op

import pandas as pd

mriqc_dir = "/home/data/abcd/abcd-hispanic-via/dset/derivatives/mriqc-0.16.1"
runs_to_exclude_qcfc_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude_qcfc.tsv"), sep="\t")
runs_to_exclude_qcfc = runs_to_exclude_qcfc_df["bids_name"].tolist()

runs_to_exclude_FD_df = pd.read_csv(op.join(mriqc_dir, "runs_to_exclude.tsv"), sep="\t")
runs_to_exclude_FD = runs_to_exclude_FD_df["bids_name"].tolist()

new_list = runs_to_exclude_qcfc + runs_to_exclude_FD
new_list = list(set(new_list))

new_df = pd.DataFrame()
new_df["bids_name"] = new_list

new_df.to_csv(op.join(mriqc_dir, "runs_to_exclude_qcfc.tsv"), sep="\t", index=False)
