import vapoursynth as vs
core = vs.get_core()
import nnedi3_resample as nresize
import kagefunc as kgf
import fvsfunc as fvf
import fag3kdb as f3kdb
import insaneAA
import lvsfunc as lvf
from toolz import functoolz

core = vs.core
core.max_cache_size = 15000

def open_source(path: str) -> vs.VideoNode:
	return lvf.src(path)

def do_main_aa(clip: vs.VideoNode) -> vs.VideoNode:
	return insaneAA.insaneAA(clip, eedi3Mode='opencl', eedi3Device=2, nnedi3Mode='opencl', nnedi3Device=2, descale_strength=1, kernel='bicubic', bicubic_b=0, bicubic_c=0.5, descale_height=844, alpha=0.5)

def denoise_and_deband(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.25, sigma=2, bm3d=False)
	db = core.f3kdb.Deband(denoise, range=18, y=30, cb=15, cr=15, grainy=10, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16, sigma=1).std.Binarize(7500).std.Inflate().std.Inflate()
	line_mask_scene = havf.mt_expand_multi(kgf.retinex_edgemask(clip16, sigma=1).std.Binarize(6000).std.Inflate().std.Inflate(), mode='ellipse', sw=2, sh=2).std.Maximum()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	merged_scene = core.std.MaskedMerge(db, clip16, line_mask_scene)
	good_merged = fvf.rfs(merged, merged_scene, mappings="[1900 1983]")
	adapt_grain = kgf.adaptive_grain(good_merged, strength=0.2, static=False, luma_scaling=10, show_mask=False)
	final = fvf.Depth(merged, 10)
	return final

source_file = r'.\zombie_ncop.m2ts'

src = open_source(source_file).std.Trim(0,2156)

filter_chain = functoolz.compose(denoise_and_deband, do_main_aa)
filtered = filter_chain(src)

src.set_output()


