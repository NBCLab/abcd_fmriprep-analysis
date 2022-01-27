import argparse
import os
import os.path as op
import shutil
import sys
from glob import glob

sys.path.append("/home/data/abcd/code/abcd_fmriprep-analysis/")
from utils import submit_job


def get_parser():
    parser = argparse.ArgumentParser(
        description="Download ABCD participant data " "and run MRIQC and fMRIPREP docker images"
    )
    parser.add_argument("--bids_dir", required=True, dest="bids_dir")
    parser.add_argument("--work_dir", required=False, dest="work_dir")
    parser.add_argument("--config", required=True, dest="config_file")
    parser.add_argument("--filter", required=True, dest="bids_filter")
    parser.add_argument("--qc", required=True, dest="qc_spreadsheet")
    parser.add_argument("--sub", required=True, dest="sub")
    parser.add_argument(
        "--sessions",
        required=False,
        dest="sessions",
        nargs="+",
        default=["baseline_year_1_arm_1", "2_year_follow_up_y_arm_1"],
    )
    parser.add_argument(
        "--modalities",
        required=False,
        dest="modalities",
        nargs="+",
        type=str,
        default=["anat", "func"],
    )
    return parser


def main(argv=None):

    args = get_parser().parse_args(argv)

    mriqc_version = "0.15.1"
    fmriprep_version = "21.0.0"

    modalities = "'{}'".format(" ".join(args.modalities).replace(" ", "' '"))
    sessions = "{}".format(" ".join(args.sessions))

    abcddicom2bids_image = "/home/data/abcd/code/singularity-images/abcddicom2bids-21.07.12.simg"
    singularity_images_home = "/home/data/cis/singularity-images"
    mriqc_image = op.join(
        singularity_images_home,
        "poldracklab_mriqc_{mriqc_version}.sif".format(mriqc_version=mriqc_version),
    )
    fmriprep_image = op.join(
        singularity_images_home,
        "poldracklab-fmriprep_{fmriprep_version}.sif".format(fmriprep_version=fmriprep_version),
    )
    fs_license_file = op.join(
        op.dirname(singularity_images_home), "cis-processing", "fs_license.txt"
    )
    templateflowdir = "/home/data/cis/templateflow"

    derivative_dir = op.join(args.bids_dir, "derivatives")
    os.makedirs(derivative_dir, exist_ok=True)
    dicom2bids_output_dir = op.join(args.bids_dir)
    dicom2bids_raw_dir = op.join(op.dirname(args.bids_dir), "raw")
    os.makedirs(dicom2bids_raw_dir, exist_ok=True)
    # mriqc_output_dir = op.join(derivative_dir, 'mriqc-{}'.format(mriqc_version))
    # os.makedirs(mriqc_output_dir, exist_ok=True)
    # fmriprep_output_dir = op.join(derivative_dir, 'fmriprep-{}'.format(fmriprep_version))
    # os.makedirs(fmriprep_output_dir, exist_ok=True)

    dicom2bids_work_dir = op.join(args.work_dir, "dicom2bids-{}".format(args.sub))
    os.makedirs(dicom2bids_work_dir, exist_ok=True)
    os.makedirs(op.join(dicom2bids_work_dir, "spreadsheets"), exist_ok=True)
    # mriqc_work_dir = op.join(args.work_dir, 'mriqc-{}'.format(args.sub))
    # os.makedirs(mriqc_work_dir, exist_ok=True)
    # fmriprep_work_dir = op.join(args.work_dir, 'fmriprep-{}'.format(args.sub))
    # os.makedirs(fmriprep_work_dir, exist_ok=True)

    # run the abcd dicom2bids docker image
    if not op.isdir(op.join(dicom2bids_output_dir, args.sub)):
        cmd = "singularity run --cleanenv \
            -B {dicom2bids_output_dir}:/out \
            -B {dicom2bids_work_dir}:/work \
            -B {dicom2bids_raw_dir}:/raw \
            -B {config}:/data/config_file.ini \
            -B {qc_spreadsheet}:/data/qc_spreadsheet.txt \
            -B {dicom2bids_work_dir}/spreadsheets:/opt/abcd-dicom2bids/spreadsheets \
            {abcddicom2bids_image} \
            --subjects {sub} --sessions {sessions} \
            --modalities {modalities} > {output_file}; \
            rm -rf {dicom2bids_work_dir}".format(
            sub=args.sub,
            dicom2bids_work_dir=dicom2bids_work_dir,
            dicom2bids_raw_dir=dicom2bids_raw_dir,
            qc_spreadsheet=args.qc_spreadsheet,
            config=args.config_file,
            abcddicom2bids_image=abcddicom2bids_image,
            dicom2bids_output_dir=dicom2bids_output_dir,
            sessions=sessions,
            modalities=modalities,
            output_file="{}.txt".format(
                op.join(op.dirname(args.bids_dir), "code", "dicom2bids", args.sub)
            ),
        )

        os.system(cmd)
    os.system(f"rm -rf {dicom2bids_work_dir}")
    """
    #create the mriqc singularity command
    if not op.isdir(op.join(mriqc_output_dir, args.sub)):
        cmd='singularity run --cleanenv \
             {mriqc_image} \
             {bids_dir}/ {mriqc_output_dir} participant \
             -w {mriqc_work_dir} --no-sub --float32 \
             --participant_label {sub}; \
             rm -rf {mriqc_work_dir}'.format(mriqc_image=mriqc_image,
                                             bids_dir=args.bids_dir,
                                             mriqc_output_dir=mriqc_output_dir,
                                             mriqc_work_dir=mriqc_work_dir,
                                             sub=args.sub.split('sub-')[1])

        #submit mriqc job to slurm
        submit_job('mriqc-{sub}'.format(sub=args.sub),
                    cores=8,
                    mem='4gb',
                    partition='investor',
                    output_file=op.join(op.dirname(args.bids_dir), 'code', 'mriqc', 'out', args.sub),
                    error_file=op.join(op.dirname(args.bids_dir), 'code', 'mriqc', 'err', args.sub),
                    queue='pq_nbc',
                    account='iacc_nbc',
                    command=cmd)


    if not op.isfile(op.join(fmriprep_output_dir, 'fmriprep', '{}.html'.format(args.sub))):
        #create the fmriprep singularity command
        cmd='singularity run --cleanenv \
            -B {templateflowdir}:$HOME/.cache/templateflow \
            {fmriprep_image} \
            {bids_dir} {fmriprep_output_dir}/ participant \
            -w {fmriprep_work_dir} \
            -vv \
            --participant-label {sub} \
            --output-spaces MNI152NLin2009cAsym:native fsaverage5 \
            --verbose \
            --skull-strip-template OASIS30ANTs:res-1 \
            --omp-nthreads ${SLURM_CPUS_PER_TASK} \
            --nprocs ${SLURM_CPUS_PER_TASK} \
            --mem_mb `echo "${SLURM_MEM_PER_CPU} * ${SLURM_CPUS_PER_TASK}" | bc -l` \
            --bids-filter-file {bids_filter} \
            --fs-license-file {fs_license_file} \
            --debug compcor \
            --notrack; \
            rm -rf {fmriprep_work_dir}'.format(fmriprep_image=fmriprep_image,
                                               bids_dir=args.bids_dir,
                                               fmriprep_output_dir=fmriprep_output_dir,
                                               fmriprep_work_dir=fmriprep_work_dir,
                                               templateflowdir=templateflowdir,
                                               fmriprep_version=fmriprep_version,
                                               sub=args.sub,
                                               bids_filter=args.bids_filter,
                                               fs_license_file=fs_license_file)

        #submit fmriprep job to slurm
        submit_job('fmriprep-{sub}'.format(sub=args.sub),
                    cores=8,
                    mem='4gb',
                    partition='IB_16C_96G',
                    output_file=op.join(op.dirname(args.bids_dir), 'code', 'fmriprep', 'out', args.sub),
                    error_file=op.join(op.dirname(args.bids_dir), 'code', 'fmriprep', 'err', args.sub),
                    queue='pq_nbc',
                    account='iacc_nbc',
                    command=cmd)
    """


if __name__ == "__main__":
    main()
