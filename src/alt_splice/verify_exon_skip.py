def verify_exon_skip(event, fn_bam, CFG):
# [verified, info] = verify_exon_skip(event, fn_bam, CFG)

verified = [0, 0, 0, 0]

info['exon_cov'] = 0
info['exon_pre_cov'] = 0
info['exon_aft_cov'] = 0 
info['exon_pre_exon_conf'] = 0 
info['exon_exon_aft_conf'] = 0 
info['exon_pre_exon_aft_conf'] = 0 
info['valid'] = True

### check validity of exon coordinates (>=0)
if sp.any(event.exons1 < 0) or sp.any(event.exons2 < 0):
    info['valid'] = False
    return (verified, info)
### check validity of exon coordinates (start < stop && non-overlapping)
elif sp.any(event.exons1[:, 1] - event.exons1[:, 0] < 1) or sp.any(event.exons2[:, 1] - event.exons2[:, 0] < 1):
    info['valid'] = False
    return (verified, info)

gg = Gene()
gg.strand = event.strand
gg.chr = event.chr
gg.chr_num = event.chr_num
gg.start = event.exons1[0, 0]
gg.stop = event.exon1[-1, -1]
assert(event.exons1[0, 0] == event.exons2[0, 0])
assert(event.exons1[-1, -1] == event.exons2[-1, -1])

### add RNA-seq evidence to the gene structure
(tracks, intron_list) = add_reads_from_bam(gg, fn_bam, ['exon_track','intron_list'], CFG['read_filter'], CFG['var_aware']);

### compute exon coverages as mean of position wise coverage
idx = sp.arange(exons2[0, 0], exons2[0, 1]) - gg.start
exon_coverage_pre = sp.mean(sp.sum(tracks[:, idx], axis=0))

idx = sp.arange(exons2[2, 0], exons2[2, 1]) - gg.start
exon_coverage_aft = sp.mean(sp.sum(tracks[:, idx], axis=0))

idx = sp.arange(exons2[1, 0], exons2[1, 1]) - gg.start
exon_coverage = sp.mean(sp.sum(tracks[:, idx], axis=0))

info['exon_pre_cov'] = exon_coverage_pre
info['exon_aft_cov'] = exon_coverage_aft
info['exon_cov'] = exon_coverage

### check if coverage of skipped exon is >= than FACTOR times average of pre and after
if exon_coverage >= CFG['exon_skip']['min_skip_rel_cov'] * (exon_coverage_pre + exon_coverage_aft)/2 
    verified[0] = 1

### check intron confirmation as sum of valid intron scores
### intron score is the number of reads confirming this intron
idx = sp.where((sp.absolute(intron_list[:, 0] - event.exons2[0, 1]) <= CFG['exon_skip']['intron_tolerance']) & (sp.absolute(intron_list[:, 1] - event.exons2[1, 0]) <= CFG['exon_skip']['intron_tolerance']))[0]
if idx.shape[0] > 0:
    info['exon_pre_exon_conf'] = sp.sum(intron_list[idx, 2])
idx = sp.where((sp.absolute(intron_list[:, 0] - event.exons2[1, 1]) <= CFG['exon_skip']['intron_tolerance']) & (sp.absolute(intron_list[:, 1] - event.exons2[2, 0]) <= CFG['exon_skip']['intron_tolerance']))[0]
if idx.shape[0] > 0:
    info['exon_exon_aft_conf'] = sp.sum(intron_list[idx, 2])
idx = sp.where((sp.absolute(intron_list[:, 0] - event.exons2[0, 1]) <= CFG['exon_skip']['intron_tolerance']) & (sp.absolute(intron_list[:, 1] - event.exons2[2, 0]) <= CFG['exon_skip']['intron_tolerance'])))[0]
if idx.shape[0] > 0:
    info['exon_pre_exon_aft_conf'] = sp.sum(intron_list[idx, 2])
if info['exon_pre_exon_conf'] >= CFG['exon_skip']['min_non_skip_count']:
    verified[1] = 1
if info['exon_exon_aft_conf'] >= CFG['exon_skip']['min_non_skip_count']:
    verified[2] = 1
if info['exon_pre_exon_aft_conf'] >= CFG['exon_skip']['min_skip_count']:
    verified[3] = 1