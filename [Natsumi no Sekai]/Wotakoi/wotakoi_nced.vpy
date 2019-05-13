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

def deband(clip16: vs.VideoNode) -> vs.VideoNode:
	db_a = core.f3kdb.Deband(clip16, range=16, y=25, cb=15, cr=15, grainy=5, grainc=0, output_depth=16)
	db_b = core.f3kdb.Deband(clip16, range=18, y=35, cb=20, cr=20, grainy=15, grainc=0, output_depth=16)
	db = fvf.rfs(db_a, db_b, mappings="[0 175] [1879 2007]")
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(8000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	adapt_grain = kgf.adaptive_grain(merged, strength=0.4, static=False, luma_scaling=10, show_mask=False)
	final = fvf.Depth(adapt_grain, 10)
	return final

source_file = r'.\wotakoi_nced.m2ts'

src = open_source(source_file).std.Trim(24,2183)

filter_chain = functoolz.compose(deband, aa)
filtered = filter_chain(src)

filtered.set_output(0)


