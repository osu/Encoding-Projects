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
	scaled = kgf.inverse_scale(clip, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=True, masking_areas=[[0,2157], [21674, 21745],[32657,34813]]) #OP et ED mask area + eyecatch
	return scaled

def aa(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	aa_p = taa.TAAmbk(clip16, aatype='Nnedi3', opencl=True, opencl_device=2)
	aa_final = fvf.rfs(aa_p, clip16, mappings="[0 2157] [32657 34813]") #épisode sauf OP et ED
	mask = kgf.retinex_edgemask(clip16, 1)
	return core.std.MaskedMerge(clip16, aa_final, mask)
	
def denoise_and_deband(clip16: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip16, 16)
	denoise_a = lvf.qden(clip16, h=0.25, sigma=3, bm3d=False)
	denoise_b = lvf.qden(clip16, h=0.7, sigma=6, bm3d=False)
	
	db_a = core.f3kdb.Deband(denoise_a, range=18, y=34, cb=22, cr=22, grainy=15, grainc=0, output_depth=16)
	db_b = core.f3kdb.Deband(denoise_b, range=22, y=48, cb=37, cr=37, grainy=25, grainc=0, output_depth=16)
	db_c = core.f3kdb.Deband(denoise_b, range=31, y=80, cb=60, cr=60, grainy=25, grainc=0, output_depth=16)
	deband_1 = fvf.rfs(db_a, db_b, mappings="[8759 8822] [9967 10021] [10306 10627] [10917 11052] [11374 11501] [11797 12103] [12151 12245] [12336 12592] [14458 14529] [18668 18839] [23208 23325] [23430 23529] [23931 24166] [26282 26447] [30476 30776] [32420 32494] [34814 35173]")
	deband = fvf.rfs(deband_1, db_c, mappings="[18601 18667]")

#	deband = db_a #Test
	
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(8000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(deband, clip16, line_mask)
	
	adapt_grain_a = kgf.adaptive_grain(merged, strength=0.35, static=False, luma_scaling=10, show_mask=False)
	adapt_grain_b = kgf.adaptive_grain(merged, strength=0.50, static=False, luma_scaling=10, show_mask=False)
	adapt_grain = fvf.rfs(adapt_grain_a, adapt_grain_b, mappings="[8759 8822] [9967 10021] [13805 13949] [14458 14529] [18601 18667] [34814 35173]")
#	adapt_grain = adapt_grain_a #Test
	
	final = fvf.Depth(adapt_grain, 10)
	return final

@functoolz.curry
def overlay_credits_in_oped(clip: vs.VideoNode, source: vs.VideoNode) -> vs.VideoNode:
	ncop_src = open_source(r'.\sugar_ncop.m2ts').std.Trim(0,2157) #longueur du ncop à modifier
	ncop_src = kgf.inverse_scale(ncop_src, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=False)
	
	ncop_processed = open_source(r'sugar_ncop_720p_loss.h264').std.Trim(0,2157) #longueur du ncop à modifier
	ncop_processed = fvf.Depth(ncop_processed, 32)
	ncop_processed_y, ncop_processed_u, ncop_processed_v = kgf.split(ncop_processed)
	ncop_processed_u = fvf.Resize(ncop_processed_u, w=1280, h=720, kernel='blackman', sx=0.25)
	ncop_processed_v = fvf.Resize(ncop_processed_v, w=1280, h=720, kernel='blackman', sx=0.25)
	ncop_processed = kgf.join([ncop_processed_y, ncop_processed_u, ncop_processed_v])
	ncop_processed = fvf.Depth(ncop_processed, 32)
	
	nced_src = open_source(r'.\sugar_nced.m2ts').std.Trim(0,2156) #longueur du nced à modifier
	nced_src = kgf.inverse_scale(nced_src, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=False)
	
	nced_processed = open_source(r'sugar_nced_720p_loss.h264').std.Trim(0,2156) #longueur du nced à modifier
	nced_processed = fvf.Depth(nced_processed, 32)
	nced_processed_y, nced_processed_u, nced_processed_v = kgf.split(nced_processed)
	nced_processed_u = fvf.Resize(nced_processed_u, w=1280, h=720, kernel='blackman', sx=0.25)
	nced_processed_v = fvf.Resize(nced_processed_v, w=1280, h=720, kernel='blackman', sx=0.25)
	nced_processed = kgf.join([nced_processed_y, nced_processed_u, nced_processed_v])
	nced_processed = fvf.Depth(nced_processed, 32)

	op_credit = kgf.inverse_scale(source, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=True, masking_areas=[[0,2157]]).std.Trim(0,2157) #récup de l'op crédit
	ed_credit = kgf.inverse_scale(source, height=720, kernel='bicubic', kerneluv='blackman', a1=1/3, a2=1/3, mask_detail=True, masking_areas=[[32657,34813]]).std.Trim(32657,34813) #récup de l'ed crédit
	
	op = atf.ApplyCredits(op_credit, ncop_src, ncop_processed)
	ed = atf.ApplyCredits(ed_credit, nced_src, nced_processed)
	
	op = fvf.Depth(op, 16)
	ed = fvf.Depth(ed, 16)

	return op + clip.std.Trim(2158,32656) + ed + clip.std.Trim(34814) #À Modifier

source_file = r'.\sugar02.m2ts'

src = open_source(source_file).std.Trim(0,35173)

filter_chain = functoolz.compose(denoise_and_deband, overlay_credits_in_oped(source=src), aa, invert_scale)
#filter_chain = functoolz.compose(denoise_and_deband)
filtered = filter_chain(src)

#filtered = src#.std.Trim(32657,34813)
filtered.set_output(0)

