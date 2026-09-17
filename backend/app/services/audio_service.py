import asyncio,subprocess
from uuid import uuid4
from pathlib import Path
import edge_tts
from ..config import AUDIO,TEMP
VOICES={'English':('en-US-AndrewMultilingualNeural','en-US-AvaMultilingualNeural'),'Hindi':('hi-IN-MadhurNeural','hi-IN-SwaraNeural'),'Telugu':('te-IN-MohanNeural','te-IN-ShrutiNeural')}
async def save(text,voice,path): await edge_tts.Communicate(text,voice).save(str(path))
def generate(dialogue,a,b,lang):
    job=uuid4().hex; folder=TEMP/job; folder.mkdir(); voices=VOICES.get(lang,VOICES['English']); seg=[]
    async def build():
        for i,t in enumerate(dialogue):
            p=folder/f'{i:03d}.mp3'; await save(t['text'],voices[0] if t['speaker']==a else voices[1],p); seg.append(p)
    asyncio.run(build())
    listing=folder/'list.txt'; listing.write_text('\n'.join("file '"+str(x.resolve()).replace('\\','/')+"'" for x in seg),encoding='utf-8')
    out=AUDIO/f'{job}.mp3'
    try: subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(out)],check=True,capture_output=True)
    except FileNotFoundError: raise RuntimeError('FFmpeg is missing. Install FFmpeg and restart the terminal.')
    for x in folder.glob('*'): x.unlink()
    folder.rmdir()
    return out
