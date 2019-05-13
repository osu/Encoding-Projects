import vapoursynth as vs
core = vs.get_core()
import kagefunc as kgf
import fvsfunc as fvf
import fag3kdb as f3kdb
import atomchtools as atf
import lvsfunc as lvf
import vsTAAmbk as taa
from toolz import functoolz

core = vs.core
core.max_cache_size = 15000

def open_source(path: str) -> vs.VideoNode:
	return lvf.src(path)

def aa(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	aa_p = taa.TAAmbk(clip16, aatype='Nnedi3', opencl=True, opencl_device=2)
	mask = kgf.retinex_edgemask(clip16, 1)
	return core.std.MaskedMerge(clip16, aa_p, mask)

def denoise_and_deband(clip16: vs.VideoNode) -> vs.VideoNode:
	denoise = lvf.qden(clip16, h=0.1, sigma=2, bm3d=False)
	db = core.f3kdb.Deband(denoise, range=18, y=25, cb=10, cr=10, grainy=0, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(8000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	adapt_grain = kgf.adaptive_grain(merged, strength=0.2, static=True, luma_scaling=10, show_mask=False)
	final = fvf.Depth(adapt_grain, 10)
	return final

source_file = r'.\wotakoi_ncop.m2ts'

src = open_source(source_file).std.Trim(0,2159)

filter_chain = functoolz.compose(denoise_and_deband, aa)
filtered = filter_chain(src)

filtered.set_output(0)


