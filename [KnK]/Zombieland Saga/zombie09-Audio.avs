LoadPlugin("C:\Program Files (x86)\AviSynth+\plugins64\ffms2.dll")
FFAudioSource("zombie09_part1.w64") ++ FFAudioSource("zombie09_part2_nc.w64")
__film = last
__just_audio = last
__blank = BlankClip(length=34047, fps=23.976)
__film = AudioDub(__blank, __film)
__final = __film.trim(0, 34046)
__final 
AudioDubEx(__just_audio, last)
AudioBits(last)>24?ConvertAudioTo24bit(last):last 
return last