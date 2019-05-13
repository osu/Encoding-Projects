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

def invert_scale(clip: vs.VideoNode) -> vs.VideoNode:
	gray_clip = core.std.ShufflePlanes(clip, 0, colorfamily=vs.GRAY)
	y = insaneAA.revert_upscale(gray_clip, descale_strength=1, kernel='bicubic', descale_height=720, bicubic_b=1/3, bicubic_c=1/3)
	u = core.std.ShufflePlanes(clip, planes=1, colorfamily=vs.GRAY)
	v = core.std.ShufflePlanes(clip, planes=2, colorfamily=vs.GRAY)
	u = fvf.Resize(u, w=1280, h=720, kernel='blackman', sx=0.25)
	v = fvf.Resize(v, w=1280, h=720, kernel='blackman', sx=0.25)
	descale_clip = core.std.ShufflePlanes(clips=[y,u,v], planes=[0,0,0], colorfamily=vs.YUV)
	return descale_clip
	
def do_main_aa(clip: vs.VideoNode) -> vs.VideoNode:
	clip16 = fvf.Depth(clip, 16)
	return taa.TAAmbk(clip16, aatype='Nnedi3', opencl=True, opencl_device=2)

def denoise_and_deband(clip16: vs.VideoNode) -> vs.VideoNode:
#	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.4, sigma=2, bm3d=False)
	
	db = core.f3kdb.Deband(denoise, range=15, y=28, cb=14, cr=14, grainy=30, grainc=0, output_depth=16)
	db_medium = core.f3kdb.Deband(denoise, range=24, y=50, cb=40, cr=40, grainy=30, grainc=0, output_depth=16)
	line_mask = kgf.retinex_edgemask(clip16).std.Binarize(7500).std.Inflate().std.Inflate()
	db_scene_filter = fvf.rfs(db, db_medium, mappings="[915 937]")
	merged = core.std.MaskedMerge(db, clip16, line_mask)
	
	adapt_grain = kgf.adaptive_grain(merged, strength=0.6, static=False, luma_scaling=8, show_mask=False)
	final = fvf.Depth(adapt_grain, 10)
	return final

source_file = r'.\sugar_nced.m2ts'

src = open_source(source_file).std.Trim(0,2159)

filter_chain = functoolz.compose(denoise_and_deband, do_main_aa, invert_scale)
filtered = filter_chain(src)

#filtered = src#.std.Trim(31526,33683)
filtered.set_output(0)

