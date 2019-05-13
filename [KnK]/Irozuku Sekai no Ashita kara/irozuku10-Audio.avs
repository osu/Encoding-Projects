LoadPlugin("C:\Program Files (x86)\AviSynth+\plugins64\ffms2.dll")
FFAudioSource("irozuku10.w64")
__film = last
__just_audio = last
__blank = BlankClip(length=34335, fps=23.976)
__film = AudioDub(__blank, __film)
__final = __film.trim(0, 34334)
__final 
AudioDubEx(__just_audio, last)
AudioBits(last)>24?ConvertAudioTo24bit(last):last 
return last