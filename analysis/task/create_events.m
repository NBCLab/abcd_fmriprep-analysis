function create_events(bidsdir, sub, ses, task, run)

  % below needed for HPC cluster
  % create a local cluster object
  %cluster = parcluster('local')
  % start matlabpool with maximum workers set in slurm submission file
  %parpool(cluster, str2num(getenv('SLURM_CPUS_ON_NODE')))

  % add the path of the folder that contains the abcd_extract_eprime_nback
  % script

  [script_dir, ~, ~] = fileparts(mfilename('fullpath'));
  addpath(genpath([script_dir '/abcd_extract_eprime']))

  fname = [bidsdir '/sourcedata/' sub '/' ses '/func/' sub '_' ses '_task-' task '_' run '_bold_EventRelatedInformation.txt'];
  outdir = [bidsdir '/derivatives/fmriprep_post-process/' sub '/' ses '/' task '/events'];

  task
  if strcmp(task,'nback')
    [eprime_nruns,errcode,behav,errmsg] = abcd_extract_eprime_nback(fname, 'outdir', outdir)

  elseif strcmp(task,'MID')
    [eprime_nruns,errcode,behav,errmsg] = abcd_extract_eprime_mid(fname, 'outdir', outdir)

  elseif strcmp(task,'SST')
    [eprime_nruns,errcode,behav,errmsg] = abcd_extract_eprime_sst(fname, 'outdir', outdir)

  end

end
