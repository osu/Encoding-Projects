import vapoursynth as vs
core = vs.get_core()
import kagefunc as kgf
import fvsfunc as fvf
import fag3kdb as f3kdb
import insaneAA
import atomchtools as atf
import lvsfunc as lvf
from toolz import functoolz

core = vs.core
core.max_cache_size = 14000

def open_source(path: str) -> vs.VideoNode:
	return lvf.src(path)

def do_main_aa(clip: vs.VideoNode) -> vs.VideoNode:
	mainAA = insaneAA.insaneAA(clip, eedi3Mode='cpu', nnedi3Mode='nnedi3', descale_strength=1, kernel='bicubic', bicubic_b=1/3, bicubic_c=1/3, descale_height=873)
	return fvf.rfs(clip, mainAA, mappings="[0 30403], [30690 32846]")
	
def denoise_and_deband(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	db_a = core.f3kdb.Deband(clip16, range=16, y=30, cb=15, cr=15, grainy=5, grainc=0, output_depth=16)
	db_b = core.f3kdb.Deband(clip16, range=20, y=38, cb=20, cr=20, grainy=15, grainc=0, output_depth=16)
	db = fvf.rfs(db_a, db_b, mappings="[30690 30865], [32569 32697]")
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(8000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	adapt_grain = kgf.adaptive_grain(merged, strength=0.4, static=False, luma_scaling=10, show_mask=False)
	final = fvf.Depth(merged, 10)
	return final

	
@functoolz.curry
def overlay_credits_in_oped(clip: vs.VideoNode, source: vs.VideoNode) -> vs.VideoNode:
    ncop_src = open_source(r'.\wotakoi_ncop.m2ts').std.Trim(0,2156)
    ncop_processed = open_source(r'wotakoi_ncop_loss.h264').std.Trim(0,2156)

    nced_src = open_source(r'.\wotakoi_nced.m2ts').std.Trim(24,2183).std.Trim(0,2156)
    nced_processed = open_source(r'.\wotakoi_nced_loss.h264').std.Trim(0,2156)

    op = atf.ApplyCredits(source.std.Trim(3789,5945), ncop_src, ncop_processed)
    ed = atf.ApplyCredits(source.std.Trim(30690,32846), nced_src, nced_processed)

    return clip.std.Trim(0,3788) + op + clip.std.Trim(5946,30689) + ed

source_file = r'.\wotakoi12.m2ts'

src = open_source(source_file).std.Trim(0,32846)

filter_chain = functoolz.compose(denoise_and_deband, overlay_credits_in_oped(source=src), do_main_aa)
filtered = filter_chain(src)

filtered.set_output(0)


