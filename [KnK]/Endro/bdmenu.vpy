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
	return taa.TAAmbk(clip, aatype='Eedi3')
	
source_file = r'.\bdmenu.m2ts'

src = open_source(source_file)#.std.Trim(24,2181)

filter_chain = functoolz.compose(do_main_aa)
filtered = filter_chain(src)
filtered = fvf.Depth(filtered, 10)
#src.set_output()
filtered.set_output(0)


