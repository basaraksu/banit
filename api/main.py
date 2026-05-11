from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
import sqlite3
import os

load_dotenv() # .env dosyasını oku

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ADMIN_USER = os.getenv("ADMIN_USERNAME")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD")

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "dashboard", "static")
DB_PATH = os.path.join(BASE_DIR, "database", "banit_logs.db")

templates = Jinja2Templates(directory=BASE_DIR + "/dashboard/templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- HELPER FONKSİYONLAR ---

def get_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ssh_logs ORDER BY timestamp DESC LIMIT 50")
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_attack_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ip_address, COUNT(*) as c FROM ssh_logs GROUP BY ip_address ORDER BY c DESC LIMIT 1")
    top_ip = cursor.fetchone() or ("Yok", 0)
    cursor.execute("SELECT username, COUNT(*) as c FROM ssh_logs GROUP BY username ORDER BY c DESC LIMIT 1")
    top_user = cursor.fetchone() or ("Yok", 0)
    conn.close()
    return {
        "top_ip": top_ip[0], "top_ip_count": top_ip[1],
        "top_user": top_user[0], "top_user_count": top_user[1]
    }

# --- GÜVENLİK (JWT) FONKSİYONLARI ---

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440)))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# API'leri koruyacak güvenlik kontrolcüsü
async def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Yetkisiz erişim")
    try:
        # Token'ın bizim belirlediğimiz SECRET_KEY ile üretildiğini doğrula
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Geçersiz token")

# --- ENDPOINTS (SAYFALAR VE API) ---

# GİRİŞ SAYFASI (Eksikti, ekledim)
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/api/login")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    
    if username == ADMIN_USER and password == ADMIN_PASS:
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre")

# ANA SAYFA (Korunan Sayfa)
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    token = request.cookies.get("access_token")
    # Sayfa yüklenirken token yoksa veya geçersizse login'e şutla
    if not token:
        return RedirectResponse(url="/login")
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return RedirectResponse(url="/login")
        
    return templates.TemplateResponse(request=request, name="index.html", context={"logs": get_logs()})

# KORUNAN API'LER (Depends kullandık)
@app.get("/api/logs")
async def get_logs_json(user: dict = Depends(verify_token)):
    logs = get_logs() 
    return [
        {
            "id": l[0], "time": l[1], "ip": l[2], "user": l[3], "pwd": l[4], 
            "status": l[5], "country": l[6], "risk": l[7]
        } 
        for l in logs
    ]

@app.get("/api/stats")
async def api_stats(user: dict = Depends(verify_token)):
    return get_attack_stats()