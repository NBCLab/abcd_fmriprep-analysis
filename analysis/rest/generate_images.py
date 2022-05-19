import argparse
import json
import os
import os.path as op
import sys
from glob import glob
from shutil import copyfile

import matplotlib.image as mpimg
import nibabel as nib
import numpy as np
import pandas as pd
from matplotlib import pyplot
from nilearn import image, masking, plotting


def _get_parser():
    parser = argparse.ArgumentParser(description="Plot result image")
    parser.add_argument(
        "--result_3dttest",
        dest="result_3dttest",
        required=True,
        help="Path to result_3dttest",
    )
    parser.add_argument(
        "--template_img",
        dest="template_img",
        required=True,
        help="Path to template_img",
    )
    parser.add_argument(
        "--out_3dttest",
        dest="out_3dttest",
        required=True,
        help="Path to out_3dttest",
    )
    return parser

def trim_image(img=None, tol=1, fix=True):
    if fix:
        mask = img != tol
    else:
        mask = img <= tol
    if img.ndim == 3:
        mask = mask.any(2)
    mask0, mask1 = mask.any(0), mask.any(1)
    return img[np.ix_(mask1, mask0)]


def main(result_3dttest, template_img, out_3dttest):
    
    in_images = [result_3dttest]
    out_images = [out_3dttest]

    for i, in_image in enumerate(in_images):
        img = nib.load(in_image)

        if np.all((img.get_fdata() == 0)):
            print("\t\tNo significant clusters", flush=True)
            quit()
        else:
            min = np.min(np.abs(img.get_fdata()[np.nonzero(img.get_fdata())]))
            if min < 1:
                min = 1
            print(f"\t\t{min}", flush=True)

        bg_img_obj = image.load_img(template_img)
        affine, shape = bg_img_obj.affine, bg_img_obj.shape
        img_obj = image.load_img(img)
        img_res_obj = image.resample_img(img_obj, affine, shape[:3])
        # cmap=color_dict[analysis],
        plotting.plot_stat_map(
            img_res_obj,
            bg_img=template_img,
            output_file=out_images[i],
            colorbar=True,
            threshold=min,
            annotate=True,
            draw_cross=False,
            black_bg=False,
            symmetric_cbar="auto",
            dim=-0.35,
            display_mode="ortho",
            vmax=None,
            resampling_interpolation="continuous",
        )

        # img1 = mpimg.imread(out_img)
        # img1 = trim_image(img=img1, tol=1, fix=True)
        # pyplot.imsave(out_img, img1)


def _main(argv=None):
    option = _get_parser().parse_args(argv)
    kwargs = vars(option)
    main(**kwargs)


if __name__ == "__main__":
    _main()
