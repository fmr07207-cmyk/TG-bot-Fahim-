import os, sqlite3
DB_PATH=os.getenv("DB_PATH","data/nexora.db")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
def connect():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c
def init_db():
    c=connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT,balance REAL DEFAULT 0,events INTEGER DEFAULT 0,earned REAL DEFAULT 0,referrer INTEGER);
    CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY);
    CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT);
    CREATE TABLE IF NOT EXISTS channels(chat_id TEXT PRIMARY KEY,title TEXT,url TEXT);
    CREATE TABLE IF NOT EXISTS withdrawals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,amount REAL,method TEXT,account TEXT,status TEXT DEFAULT 'pending',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """); c.commit(); c.close()
def ensure_user(uid,username):
    c=connect(); c.execute("INSERT OR IGNORE INTO users(user_id,username) VALUES(?,?)",(uid,username)); c.execute("UPDATE users SET username=? WHERE user_id=?",(username,uid)); c.commit(); c.close()
def user(uid):
    c=connect(); r=c.execute("SELECT * FROM users WHERE user_id=?",(uid,)).fetchone(); c.close(); return dict(r) if r else {"balance":0,"events":0,"earned":0}
def admins():
    c=connect(); r=c.execute("SELECT user_id FROM admins").fetchall(); c.close(); return [x[0] for x in r]
def is_admin(uid): return uid in admins()
def add_admin(uid):
    c=connect(); c.execute("INSERT OR IGNORE INTO admins VALUES(?)",(uid,)); c.commit(); c.close()
def remove_admin(uid):
    c=connect(); c.execute("DELETE FROM admins WHERE user_id=?",(uid,)); c.commit(); c.close()
def get_setting(k,d=""):
    c=connect(); r=c.execute("SELECT v FROM settings WHERE k=?",(k,)).fetchone(); c.close(); return r["v"] if r else d
def set_setting(k,v):
    c=connect(); c.execute("INSERT INTO settings VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",(k,v)); c.commit(); c.close()
def channels():
    c=connect(); r=c.execute("SELECT * FROM channels").fetchall(); c.close(); return [dict(x) for x in r]
def add_channel(cid,title,url):
    c=connect(); c.execute("INSERT OR REPLACE INTO channels VALUES(?,?,?)",(cid,title,url)); c.commit(); c.close()
def remove_channel(cid):
    c=connect(); c.execute("DELETE FROM channels WHERE chat_id=?",(cid,)); c.commit(); c.close()
def set_referrer(uid,ref):
    c=connect(); c.execute("UPDATE users SET referrer=? WHERE user_id=? AND referrer IS NULL",(ref,uid)); c.commit(); c.close()
def record_event(uid,amount):
    c=connect(); c.execute("UPDATE users SET balance=balance+?,earned=earned+?,events=events+1 WHERE user_id=?",(float(amount),float(amount),uid)); c.commit(); c.close()
def leaderboard():
    c=connect(); r=c.execute("SELECT user_id,username,events,earned FROM users ORDER BY events DESC,earned DESC LIMIT 20").fetchall(); c.close(); return [dict(x) for x in r]
def withdraw(uid,amount,method,account):
    c=connect(); c.execute("UPDATE users SET balance=balance-? WHERE user_id=?",(float(amount),uid)); c.execute("INSERT INTO withdrawals(user_id,amount,method,account) VALUES(?,?,?,?)",(uid,float(amount),method,account)); c.commit(); c.close()
def withdrawals():
    c=connect(); r=c.execute("SELECT * FROM withdrawals ORDER BY id DESC LIMIT 30").fetchall(); c.close(); return [dict(x) for x in r]
def withdraw_status(wid,status):
    c=connect()
    row=c.execute("SELECT user_id,amount,status FROM withdrawals WHERE id=?",(wid,)).fetchone()
    if row and row["status"]=="pending":
        if status=="rejected": c.execute("UPDATE users SET balance=balance+? WHERE user_id=?",(row["amount"],row["user_id"]))
        c.execute("UPDATE withdrawals SET status=? WHERE id=?",(status,wid))
    c.commit(); c.close()
def user_ids():
    c=connect(); r=c.execute("SELECT user_id FROM users").fetchall(); c.close(); return [x[0] for x in r]
