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
import lvsfunc as lvf
import vsutil
import havsfunc as havf
import adjust
from toolz import functoolz
from nnedi3_rpow2 import nnedi3_rpow2

core = vs.core
core.max_cache_size = 14000

src = lvf.src(r'.\bdmenu03.m2ts')

src16 = fvf.Depth(src, 16)

Y, U, V = kgf.split(src16)

U_scaled = nnedi3_rpow2(U).resize.Spline36(1920, 1080, format=vs.GRAY16)
V_scaled = nnedi3_rpow2(V).resize.Spline36(1920, 1080, format=vs.GRAY16)

scaled = kgf.join([Y, U_scaled, V_scaled])

aa = taa.TAAmbk(scaled, aatype='Nnedi3', opencl=True, opencl_device=2)

out = aa
final = fvf.Depth(out, 10)
final.set_output(0)

