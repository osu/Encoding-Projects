import vapoursynth as vs
core = vs.get_core()
import kagefunc as kgf
import fvsfunc as fvf
import fag3kdb as f3kdb
import vardefunc as vrd
import insaneAA
import atomchtools as atf
import lvsfunc as lvf
from toolz import functoolz


core = vs.core
core.max_cache_size = 14000

def open_source(path: str) -> vs.VideoNode:
	return lvf.src(path)

def do_main_aa(clip: vs.VideoNode) -> vs.VideoNode:
	mainAA = insaneAA.insaneAA(clip, eedi3Mode='opencl', eedi3Device=2, nnedi3Mode='opencl', nnedi3Device=2, descale_strength=1, kernel='bicubic', bicubic_b=0, bicubic_c=0.5, descale_height=844, alpha=0.5)
	return fvf.rfs(clip, mainAA, mappings="[0 33685], [33720 33909]")
	
def denoise_and_deband(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.25, sigma=2, bm3d=False)
	db = core.f3kdb.Deband(denoise, range=20, y=38, cb=19, cr=19, grainy=10, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(7000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	adapt_grain = kgf.adaptive_grain(merged, strength=0.3, static=False, luma_scaling=10, show_mask=False)
	final = fvf.Depth(merged, 10)
	return final
	
@functoolz.curry
def overlay_credits_in_oped(clip: vs.VideoNode, source: vs.VideoNode) -> vs.VideoNode:
	ncop_src = open_source(r'.\zombie_ncop.m2ts').std.Trim(0,1999)
	ncop_processed = open_source(r'zombie_ncop_loss.h264').std.Trim(0,1999)

	nced_src = open_source(r'.\zombie_nced.m2ts').std.Trim(0,2157)
	nced_processed = open_source(r'.\zombie_nced_loss.h264').std.Trim(0,2157)

	op_trim = source.std.Trim(3141,5298)
	op_trim1_1 = op_trim.std.Trim(0,1999)
	op = atf.ApplyCredits(op_trim1_1, ncop_src, ncop_processed)
	op = op + op_trim.std.Trim(2000)
	ed = atf.ApplyCredits(source.std.Trim(31528,33685), nced_src, nced_processed)

	return clip.std.Trim(0,3140) + op + clip.std.Trim(5299,31527) + ed + clip.std.Trim(33686)

source_file = r'.\zombie06.m2ts'

src = open_source(source_file).std.Trim(0,34045)

filter_chain = functoolz.compose(denoise_and_deband, overlay_credits_in_oped(source=src), do_main_aa)
filtered = filter_chain(src)

filtered.set_output(0)
