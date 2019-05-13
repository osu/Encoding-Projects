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
	return fvf.ReplaceFramesSimple(clip, mainAA, mappings="[0 26420], [26493 32174], [34332 34691]")
	
def fix_edges(clip: vs.VideoNode) -> vs.VideoNode:
	fixedges = core.edgefixer.ContinuityFixer(clip, [6,0,0], [6,0,0], [6,0,0], [6,0,0])
	return fvf.ReplaceFramesSimple(clip, fixedges, mappings="[2561 32174], [34332 34691]")
	
def denoise_and_deband(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.35, sigma=2, bm3d=False)
	db = core.f3kdb.Deband(denoise, range=20, y=36, cb=18, cr=18, grainy=0, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(7000).std.Inflate().std.Inflate()
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	final = fvf.Depth(merged, 10)
	return final

source_file = r'.\irozuku01.m2ts'

src = open_source(source_file).std.Trim(0,34691)

filter_chain = functoolz.compose(denoise_and_deband, do_main_aa, fix_edges)
filtered = filter_chain(src)

filtered.set_output(0)
