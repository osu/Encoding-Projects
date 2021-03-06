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
	mainAA = insaneAA.insaneAA(clip, eedi3Mode='cpu', nnedi3Mode='nnedi3', descale_strength=1, kernel='bicubic', bicubic_b=0.2, bicubic_c=0.5, descale_height=720, alpha=0.5, beta=0.4)
	return fvf.ReplaceFramesSimple(clip, mainAA, mappings="[0 17333], [17406 34692]")
	
def fix_edges(clip: vs.VideoNode) -> vs.VideoNode:
	fixedges = core.edgefixer.ContinuityFixer(clip, [6,0,0], [6,0,0], [6,0,0], [6,0,0])
	return fixedges
	
def denoise_and_deband(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.35, sigma=2, bm3d=False)
	db = core.f3kdb.Deband(denoise, range=24, y=42, cb=21, cr=21, grainy=0, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(7000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	final = fvf.Depth(merged, 10)
	return final

	
@functoolz.curry
def overlay_credits_in_oped(clip: vs.VideoNode, source: vs.VideoNode) -> vs.VideoNode:
    ncop_src = open_source(r'.\irozuku_ncop.m2ts').std.Trim(0,2156)
    ncop_processed = core.lsmas.LWLibavSource(r'irozuku_ncop_loss.h264').std.Trim(0,2156)

    nced_src = open_source(r'.\irozuku_nced.m2ts').std.Trim(0,2156)
    nced_processed = core.lsmas.LWLibavSource(r'.\irozuku_nced_loss.h264').std.Trim(0,2156)

    op = atf.ApplyCredits(source.std.Trim(864,3020), ncop_src, ncop_processed)
    ed = atf.ApplyCredits(source.std.Trim(32176,34332), nced_src, nced_processed)

    return clip.std.Trim(0,863) + op + clip.std.Trim(3021,32175) + ed + clip.std.Trim(34333)

source_file = r'.\irozuku06.m2ts'

src = open_source(source_file).std.Trim(0,34692)

filter_chain = functoolz.compose(denoise_and_deband, overlay_credits_in_oped(source=src), do_main_aa, fix_edges)
filtered = filter_chain(src)

filtered.set_output(0)
