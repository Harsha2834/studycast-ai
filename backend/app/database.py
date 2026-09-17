import sqlite3
from .config import DB
def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    with conn() as c:
        c.execute('CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,name TEXT,path TEXT,text TEXT,created TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS generations(id TEXT PRIMARY KEY,document_id TEXT,title TEXT,prefs TEXT,transcript TEXT,audio TEXT,created TEXT)')
