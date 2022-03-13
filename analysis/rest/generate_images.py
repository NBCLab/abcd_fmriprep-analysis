import argparse
import json
import os
import os.path as op
import sys
from glob import glob
from shutil import copyfile

import nibabel as nib
import numpy as np
import pandas as pd
from nilearn import image, masking, plotting


def _get_parser():
    parser = argparse.ArgumentParser(description="Plot result image")
    parser.add_argument(
        "--result_img",
        dest="result_img",
        required=True,
        help="Path to result_img",
    )
    parser.add_argument(
        "--template_img",
        dest="template_img",
        required=True,
        help="Path to template_img",
    )
    return parser


def main(result_img, template_img, out_img):

    img = nib.load(result_img)
    if np.all((img.get_fdata() == 0)):
        print("\t\tNo significant clusters", flush=True)
        quit()
    else:
        min = np.min(np.abs(img.get_fdata()[np.nonzero(img.get_fdata())]))
        print(f"\t\t{min}", flush=True)

    bg_img_obj = image.load_img(template_img)
    affine, shape = bg_img_obj.affine, bg_img_obj.shape
    img_obj = image.load_img(img)
    img_res_obj = image.resample_img(img_obj, affine, shape[:3])
    # cmap=color_dict[analysis],
    plotting.plot_stat_map(
        img_res_obj,
        bg_img=template_img,
        cut_coords=None,
        output_file=out_img,
        display_mode="ortho",
        colorbar=True,
        threshold=min,
        annotate=False,
        draw_cross=False,
        black_bg=False,
        symmetric_cbar="auto",
        dim=-0.35,
        vmax=None,
        resampling_interpolation="continuous",
    )


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
