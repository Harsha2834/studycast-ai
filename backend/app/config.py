from pathlib import Path
import os
BASE=Path(__file__).resolve().parent.parent
DATA=BASE/'data'; UPLOADS=DATA/'uploads'; AUDIO=DATA/'audio'; TEMP=DATA/'temp'; DB=DATA/'studycast.db'
for p in [DATA,UPLOADS,AUDIO,TEMP]: p.mkdir(parents=True,exist_ok=True)
OLLAMA_URL=os.getenv('OLLAMA_URL','http://localhost:11434/api/chat')
OLLAMA_MODEL=os.getenv('OLLAMA_MODEL','llama3.2:3b')
MAX_SIZE=20*1024*1024
ALLOWED={'.pdf','.docx','.pptx','.txt'}
