import os.path as op
from glob import glob

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import image

output_dir = "/home/data/abcd/abcd-hispanic-via/atlas"
template = "/home/data/cis/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_desc-brain_T1w.nii.gz"
template_img = image.load_img(template)
template_data = template_img.get_fdata()
affine, shape, header = template_img.affine, template_img.shape, template_img.header

new_data = np.zeros_like(template_data)
new_df = pd.DataFrame(columns=["roi_idx", "roi_name"])

seed_regions_path = "/home/data/abcd/abcd-hispanic-via/seed-regions"
seed_regions = ["insulaDlh", "insulaDrh", "TPJplh", "TPJprh", "vmPFC3"]
for idx, seed_region in enumerate(seed_regions):
    seed_region_files = sorted(glob(op.join(seed_regions_path,"*",f"*{seed_region}*")))
    assert len(seed_region_files) == 1
    seed_region_file = seed_region_files[0]

    seed_region_img = image.load_img(seed_region_file)

    if seed_region_img.shape != template_img.shape:
        seed_region_img_res = image.resample_img(
                    seed_region_img, affine, shape[:3], interpolation="nearest"
                )
    else:
        seed_region_img_res = seed_region_img
    
    data = seed_region_img_res.get_fdata().astype(bool)

    roi_value = idx + 1
    new_data[data] = roi_value

    roi_df = {"roi_idx": roi_value, "roi_name": seed_region}
    new_df = new_df.append(roi_df, ignore_index = True)

print(new_data.min(), new_data.max())
new_img = nib.Nifti1Image(new_data, affine, header)
new_img.to_filename(op.join(output_dir,"MAseeds.nii.gz"))

new_df.to_csv(op.join(output_dir,"MAseeds.txt"), header=None, index=None, sep='\t')

