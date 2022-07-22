# abcd_fmriprep-analysis
Download ABCD MRI data convert the DICOM data to BIDS format, preprocess the BIDS data with fMRIPrep, and denoise it with 3dTproject.  

## Download
`download/` contains scripts to download ABCD magnetic resonance imaging (MRI) data and convert the DICOM data organization to fit the Brain Imaging Data Structure (BIDS) specification. 
The main scripts contit of (1) `abcddownload_job.sh`, which downloads the DICOM data, and (2) `abcd2bids_job.sbatch`, which unpack the downloaded data, and converts it to BIDS format. 

These scripts made use of a modified version of the [abcd-dicom2bids](https://github.com/DCAN-Labs/abcd-dicom2bids) repository. We generated a [Docker image](https://hub.docker.com/repository/docker/julioaperaza/abcddicom2bids) of our [modified version](https://github.com/JulioAPeraza/abcd-dicom2bids), which was then converted to a Singularity image on FIU’s High Performance Cluster (HPC).

## MRI Quality Control
`mriqc/` contains scripts to run MRIQC 0.16.1 (Esteban et al., 2017), a BIDS-App that computes quality control (QC) measures.
After calculating the participant's level QC measures the `mriqc-participants_job.sbatch`, `mriqc-group_job.sh` is used to generate the group level reports and distributions. QC metrics that were less than the 1st percentile or greater than the 99th percentile, depending on the metric, were included in `runs_to_exclude.tsv` and excluded from further analysis. We focused on 6 measures: signal-to-noise ratio (SNR), temporal SNR, mean framewise displacement (FD), and ghost-to-signal ratio in the x- and y-directions, and entropy focus criterion.

## Preprocessing
`fmriprep/` contains a script to process MRI data using fMRIPrep 21.0.0, a BIDS-App that automatically adapts a best-in-breed workflow, ensuring high-quality preprocessing with minimal manual intervention (Esteban et al., 2020, 2019).

## RSFC Analysis and Denoising
`analysis/rest` contains scripts to perform fMRIPrep-compatible denoising, seed-to-voxel connectivity analysis, and ROI-to-ROI connectivity analysis. 

## Task-Based fMRI Analysis (Work In Progress)
`analysis/rest` contains scripts to perform task-based fMRI analysis.

## QC-RSFC
`qcfc/` contains scripts that calculates a set of QC-FC (quality control - functional connectivity) benchmarks.
