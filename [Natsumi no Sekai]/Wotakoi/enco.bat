@echo off
set vs="C:\Program Files (x86)\VapourSynth\core64\vspipe.exe"
set binary="C:\Encode Stuff\x264-x64-2901-aMod-avx2.exe"
set as="C:\Encode Stuff\avs2pipemod64.exe"
set merge="C:\Program Files\MKVToolNix\mkvmerge.exe"
set qaac="D:\Programmes\MeGUI-2808-32\tools\qaac\qaac.exe"
set eac3to="D:\Programmes\MeGUI-2808-32\tools\eac3to\eac3to.exe"

:loop
echo Vapoursynth script : "%~nf1"
echo Output directory: "%~1.mkv"
echo.
echo ----------------
echo Encodage Video avec VapourSynth...
%vs% "%~nf1" --y4m - | %binary% --demuxer y4m -o "%~n1.h264" - --input-depth 10 --output-depth 10 --colormatrix bt709 --ref 12 --deblock -2:-2 --me umh --subme 10 --fade-compensate 0.00 --psy-rd 1.0:0.00 --merange 24 --trellis 2 --no-dct-decimate --bframes 8 --b-adapt 2 --direct auto --keyint 240 --min-keyint 23 --rc-lookahead 48 --crf 15 --qcomp 0.7 --aq-mode 3 --aq-strength 0.85

echo .
echo ----------------
echo Extraction audio du m2ts...
%eac3to% "%~n1.m2ts" 2:"%~n1.w64" -log=nul

echo .
echo ----------------
echo Decoupage de l'audio avec AviSynth...
%as% -wav "%~n1-Audio.avs" > "%~n1-cut.w64"

echo .
echo ----------------
echo Encodage Audio en AAC...
%qaac% "%~n1-cut.w64" --threading -V 127 --no-delay --no-optimize --verbose -o "%~n1-cut.m4a"

echo .
echo ----------------
echo Mux final avec chapitres...
%merge% --ui-language fr --priority higher --output "%~n1.mkv" --language 0:jpn --default-track 0:yes "%~n1.h264" --language 0:jpn "%~n1-cut.m4a" --chapter-language fre --chapters "%~n1.txt" --track-order 0:0,1:0,2:0

echo .
echo ----------------
echo Fini !
echo.
shift
if not "%~1"=="" goto :loop

pause
