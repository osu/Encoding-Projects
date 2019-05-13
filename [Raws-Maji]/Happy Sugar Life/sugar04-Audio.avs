LoadPlugin("C:\Program Files (x86)\AviSynth+\plugins64\ffms2.dll")
FFAudioSource("sugar04.w64")
__film = last
__just_audio = last
__blank = BlankClip(length=35173, fps=23.976)
__film = AudioDub(__blank, __film)
__final = __film.trim(0, 35172)
__final 
AudioDubEx(__just_audio, last)
AudioBits(last)>24?ConvertAudioTo24bit(last):last 
return last