const BASE='http://127.0.0.1:8000';
async function req(path,opt={}){const r=await fetch(BASE+path,opt);const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.detail||'Request failed');return d}
export async function upload(file){const f=new FormData();f.append('file',file);return req('/api/documents/upload',{method:'POST',body:f})}
export async function generate(p){return req('/api/generations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)})}
export async function history(){return req('/api/history')}
export {BASE}
