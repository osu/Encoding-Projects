import vapoursynth as vs
core = vs.get_core()
import nnedi3_resample as nresize
import hysteria as hys
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
from toolz import functoolz

core = vs.core
core.max_cache_size = 15000

def open_source(path: str) -> vs.VideoNode:
	return lvf.src(path)

def do_main_aa(clip: vs.VideoNode) -> vs.VideoNode:
	return insaneAA.insaneAA(clip, eedi3Mode='cpu', nnedi3Mode='nnedi3', descale_strength=0.5, kernel='bicubic', bicubic_b=0.2, bicubic_c=0.5, descale_height=720, alpha=0.5, beta=0.4)

def denoise_and_deband(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.1, sigma=2, bm3d=False)
	db = core.f3kdb.Deband(denoise, range=18, y=30, cb=15, cr=15, grainy=0, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(7000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
#	adapt_grain = kgf.adaptive_grain(merged, strength=0.25, static=False, luma_scaling=10, show_mask=False)
	final = fvf.Depth(merged, 10)
	return final

source_file = r'.\irozuku_ncop.m2ts'

src = open_source(source_file).std.Trim(0,2159)

filter_chain = functoolz.compose(denoise_and_deband, do_main_aa)
filtered = filter_chain(src)

#src.set_output()
filtered.set_output(0)


