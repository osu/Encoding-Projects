import vapoursynth as vs
core = vs.get_core()
import nnedi3_resample as nresize
import muvsfunc as muvf
import mvsfunc as mvf
import vsTAAmbk as taa
import kagefunc as kgf
import fvsfunc as fvf
import fag3kdb as f3kdb
import vardefunc as vrd
import insaneAA
import atomchtools as atf
import lvsfunc as lvf
import vsutil
import havsfunc as havf
import adjust
from toolz import functoolz
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 14000

def open_source(path: str) -> vs.VideoNode:
	return lvf.src(path)

def invert_scale(clip: vs.VideoNode) -> vs.VideoNode:
	scaled = kgf.inverse_scale(clip, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=True, masking_areas=[[2230, 4386], [17430, 17501],[31888,34045]]) #OP et ED mask area + eyecatch
	return scaled

def aa(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	aa_p = taa.TAAmbk(clip16, aatype='Nnedi3', opencl=True, opencl_device=2)
	aa_final = fvf.rfs(aa_p, clip16, mappings="[2230 4386] [31888 34045]") #épisode sauf OP et ED
	mask = kgf.retinex_edgemask(clip16, 1)
	return core.std.MaskedMerge(clip16, aa_final, mask)
	
def denoise_and_deband(clip16: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip16, 16)
	denoise_a = lvf.qden(clip16, h=0.25, bm3d=False)
	denoise_b = lvf.qden(clip16, h=0.7, bm3d=False)
	denoise_c = lvf.qden(clip16, h=1.1, bm3d=False)
	
	db_a = core.f3kdb.Deband(denoise_a, range=20, y=36, cb=28, cr=28, grainy=12, grainc=0, output_depth=16)
	db_b = core.f3kdb.Deband(denoise_b, range=25, y=50, cb=39, cr=39, grainy=21, grainc=0, output_depth=16)
	db_c = core.f3kdb.Deband(denoise_c, range=31, y=80, cb=60, cr=60, grainy=25, grainc=0, output_depth=16)
	deband_1 = fvf.rfs(db_a, db_b, mappings="[6489 6709] [7531 7571] [7731 7782] [8579 8691] [9597 9700] [9891 10138] [10340 10552] [12148 12498] [12576 12726] [13511 13636] [13835 13882] [16926 16970] [17430 17501] [24956 25072] [25499 25884] [26182 26521] [26845 26950] [27045 27458] [29473 29644] [29796 29877] [30019 30330] [30617 31198] [31569 31887] [34118 34205] [34813 35172]")
	deband = fvf.rfs(deband_1, db_c, mappings="[0 29] [10701 10803]")

#	deband = db_a #Test
	
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(8000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(deband, clip16, line_mask)
	
	adapt_grain_a = kgf.adaptive_grain(merged, strength=0.35, static=False, luma_scaling=10, show_mask=False)
	adapt_grain_b = kgf.adaptive_grain(merged, strength=0.50, static=False, luma_scaling=10, show_mask=False)
	adapt_grain = fvf.rfs(adapt_grain_a, adapt_grain_b, mappings="[0 29] [9346 9700] [10701 10803] [12148 12498] [17430 17501] [34813 35172]")
#	adapt_grain = adapt_grain_a #Test
	
	final = fvf.Depth(adapt_grain, 10)
	return final

@functoolz.curry
def overlay_credits_in_oped(clip: vs.VideoNode, source: vs.VideoNode) -> vs.VideoNode:
	ncop_src = open_source(r'.\sugar_ncop.m2ts').std.Trim(0,2156) #longueur du ncop à modifier
	ncop_src = kgf.inverse_scale(ncop_src, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=False)
	
	ncop_processed = open_source(r'sugar_ncop_720p_loss.h264').std.Trim(0,2156) #longueur du ncop à modifier
	ncop_processed = fvf.Depth(ncop_processed, 32)
	ncop_processed_y, ncop_processed_u, ncop_processed_v = kgf.split(ncop_processed)
	ncop_processed_u = fvf.Resize(ncop_processed_u, w=1280, h=720, kernel='blackman', sx=0.25)
	ncop_processed_v = fvf.Resize(ncop_processed_v, w=1280, h=720, kernel='blackman', sx=0.25)
	ncop_processed = kgf.join([ncop_processed_y, ncop_processed_u, ncop_processed_v])
	ncop_processed = fvf.Depth(ncop_processed, 32)
	
	nced_src = open_source(r'.\sugar_nced.m2ts').std.Trim(0,2157) #longueur du nced à modifier
	nced_src = kgf.inverse_scale(nced_src, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=False)
	
	nced_processed = open_source(r'sugar_nced_720p_loss.h264').std.Trim(0,2157) #longueur du nced à modifier
	nced_processed = fvf.Depth(nced_processed, 32)
	nced_processed_y, nced_processed_u, nced_processed_v = kgf.split(nced_processed)
	nced_processed_u = fvf.Resize(nced_processed_u, w=1280, h=720, kernel='blackman', sx=0.25)
	nced_processed_v = fvf.Resize(nced_processed_v, w=1280, h=720, kernel='blackman', sx=0.25)
	nced_processed = kgf.join([nced_processed_y, nced_processed_u, nced_processed_v])
	nced_processed = fvf.Depth(nced_processed, 32)

	op_credit = kgf.inverse_scale(source, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=True, masking_areas=[[2230,4386]]).std.Trim(2230,4386) #récup de l'op crédit
	ed_credit = kgf.inverse_scale(source, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=True, masking_areas=[[31888,34045]]).std.Trim(31888,34045) #récup de l'ed crédit
	
	op = atf.ApplyCredits(op_credit, ncop_src, ncop_processed)
	ed = atf.ApplyCredits(ed_credit, nced_src, nced_processed)
	
	op = fvf.Depth(op, 16)
	ed = fvf.Depth(ed, 16)

	return clip.std.Trim(0,2229) + op + clip.std.Trim(4387,31887) + ed + clip.std.Trim(34046) #À Modifier

source_file = r'.\sugar04.m2ts'

src = open_source(source_file).std.Trim(0,35172)

filter_chain = functoolz.compose(denoise_and_deband, overlay_credits_in_oped(source=src), aa, invert_scale)
#filter_chain = functoolz.compose(denoise_and_deband)
filtered = filter_chain(src)

#filtered = src#.std.Trim(31888,34045)
filtered.set_output(0)

