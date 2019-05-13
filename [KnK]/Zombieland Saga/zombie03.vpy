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
	return fvf.rfs(clip, mainAA, mappings="[0 33688], [33718 34048]")
	
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
	ncop_processed = core.lsmas.LWLibavSource(r'zombie_ncop_loss.h264').std.Trim(0,1999)

	op_trim = source.std.Trim(5011,7169)
	op_trim1_1 = op_trim.std.Trim(0,1999)
	op = atf.ApplyCredits(op_trim1_1, ncop_src, ncop_processed)
	op = op_trim1_1 + op_trim.std.Trim(2000)
	
	ed = core.std.MaskedMerge(clip.std.Trim(31493,33688), source.std.Trim(31493,33688), atf.DiffRescaleMask(source.std.Trim(31493,33688), descale_h=844, kernel='Spline16', mthr=50).std.Maximum().std.Maximum().std.Inflate(), planes=[0], first_plane=True)

	return clip.std.Trim(0,5010) + op + clip.std.Trim(7170,31492) + ed + clip.std.Trim(33689)

@functoolz.curry
def overlay_credits_in_preview(clip: vs.VideoNode, source: vs.VideoNode) -> vs.VideoNode:
	mask = havf.mt_expand_multi(atf.DiffRescaleMask(core.std.Trim(source, 34048,34048), descale_h=844, kernel='bicubic', b=0, c=0.5, mthr=50), sw=4, sh=4).std.Binarize()
	return vrd.rfs(clip, core.std.MaskedMerge(clip, source, mask, planes=[0], first_plane=True), debut=33946, fin=34048)

source_file = r'.\zombie03.m2ts'

src = open_source(source_file).std.Trim(0,34048)

filter_chain = functoolz.compose(denoise_and_deband, overlay_credits_in_preview(source=src), overlay_credits_in_oped(source=src), do_main_aa)
filtered = filter_chain(src)

filtered.set_output(0)
