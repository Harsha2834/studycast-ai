import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .config import UPLOADS,AUDIO,MAX_SIZE,ALLOWED
from .database import init_db,conn
from .services.document_service import extract
from .services.llm_service import generate
from .services.audio_service import generate as audio_generate

app=FastAPI(title='StudyCast AI API')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.mount('/media/audio',StaticFiles(directory=AUDIO),name='audio')
@app.on_event('startup')
def start():init_db()
class Req(BaseModel):
 document_id:str; prompt:str=''; style:str='Friends'; level:str='College'; language:str='English'; speaker_a:str='Alex'; speaker_b:str='Maya'; tone:str='Engaging'; duration:str='8'
@app.get('/api/health')
def health():return {'status':'ok'}
@app.post('/api/documents/upload')
async def upload(file:UploadFile=File(...)):
 name=file.filename or 'upload'; ext=Path(name).suffix.lower()
 if ext not in ALLOWED:raise HTTPException(400,'Supported: PDF, DOCX, PPTX, TXT')
 data=await file.read()
 if len(data)>MAX_SIZE:raise HTTPException(400,'Maximum file size is 20 MB')
 id=uuid4().hex; path=UPLOADS/f'{id}{ext}';path.write_bytes(data)
 try:text=extract(path)
 except Exception as e:path.unlink(missing_ok=True);raise HTTPException(400,str(e))
 now=datetime.now(timezone.utc).isoformat()
 with conn() as c:c.execute('INSERT INTO documents VALUES(?,?,?,?,?)',(id,name,str(path),text,now))
 return {'document_id':id,'filename':name,'characters_extracted':len(text),'text_preview':text[:1000]}
@app.post('/api/generations')
def generation(r:Req):
 with conn() as c:row=c.execute('SELECT name,text FROM documents WHERE id=?',(r.document_id,)).fetchone()
 if not row:raise HTTPException(404,'Document not found')
 prefs=r.model_dump(); dialogue,provider=generate(row['text'],prefs)
 try:audio=audio_generate(dialogue,r.speaker_a,r.speaker_b,r.language)
 except Exception as e:raise HTTPException(500,f'Audio generation failed: {e}')
 id=uuid4().hex;now=datetime.now(timezone.utc).isoformat()
 with conn() as c:c.execute('INSERT INTO generations VALUES(?,?,?,?,?,?,?)',(id,r.document_id,row['name'],json.dumps(prefs),json.dumps(dialogue),audio.name,now))
 return {'generation_id':id,'title':row['name'],'provider':provider,'transcript':dialogue,'audio_url':f'/media/audio/{audio.name}','created_at':now}
@app.get('/api/history')
def history():
 with conn() as c:rows=c.execute('SELECT * FROM generations ORDER BY created DESC LIMIT 30').fetchall()
 out=[]
 for x in rows:
  p=json.loads(x['prefs']);out.append({'generation_id':x['id'],'title':x['title'],'style':p.get('style'),'level':p.get('level'),'language':p.get('language'),'audio_url':f"/media/audio/{x['audio']}",'created_at':x['created']})
 return out
