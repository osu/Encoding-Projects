import vapoursynth as vs
core = vs.get_core()
import nnedi3_resample as nresize
import muvsfunc as muvf
import mvsfunc as mvf
import vsTAAmbk as taa
import kagefunc as kgf
import fvsfunc as fvf
import fag3kdb as f3kdb
import vardefunc as vrd
import insaneAA
import atomchtools as atf
import havsfunc as havf
import lvsfunc as lvf
import vsutil
import HardAAp2
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
	#Denoise/degrain
#	clip16 = fvf.Depth(clip, 16)
	denoise = lvf.qden(clip16, h=0.2, sigma=2, bm3d=False)
	denoise_high = lvf.qden(clip16, h=1.2, sigma=2, bm3d=False)
	denoise_filter_final = fvf.rfs(denoise, denoise_high, mappings="[565 625], [640 686]")
	
	#Deband
	db = core.f3kdb.Deband(denoise_filter_final, range=20, y=40, cb=20, cr=20, grainy=20, grainc=0, output_depth=16)
	db_medium = core.f3kdb.Deband(denoise_filter_final, range=24, y=60, cb=35, cr=35, grainy=20, grainc=0, output_depth=16)
	db_high = core.f3kdb.Deband(denoise_filter_final, range=31, y=80, cb=50, cr=50, grainy=20, grainc=0, output_depth=16)
	clip16_y = vsutil.get_y(denoise_filter_final)
	line_mask = kgf.retinex_edgemask(clip16_y, sigma=2).std.Binarize(8500).std.Inflate().std.Inflate()
#	return line_mask
	db_scene_filter = fvf.rfs(db, db_medium, mappings="[731 760], [820 823], [1112 1130], [1442 1453], [1615 1672], [2084 2085]")
	db_scene_filter_final = fvf.rfs(db_scene_filter, db_high, mappings="[565 625], [640 686], [1328 1432], [2086 2159]")
	merged = core.std.MaskedMerge(db_scene_filter_final, clip16, line_mask)
	
	#Addgrain
	adapt_grain = kgf.adaptive_grain(merged, strength=0.6, static=False, luma_scaling=10, show_mask=False)
	
	final = fvf.Depth(adapt_grain, 10)
	return final

source_file = r'.\sugar_ncop.m2ts'

src = open_source(source_file).std.Trim(0,2159)

filter_chain = functoolz.compose(denoise_and_deband, do_main_aa, invert_scale)
filtered = filter_chain(src)

filtered.set_output(0)
#src.set_output()