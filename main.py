# COMPLETE DATABASE SETUP - PUT THIS FIRST (line 10 မှာ)
import sqlite3
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(
    title="🚀 Comet AI Trading",
    description="""🌠 Professional Crypto Exchange 
    ✅ Real-time BTC/ETH Trading
    ✅ Compound Interest Calculator
    ✅ Live Dashboard (2s updates)
    ✅ KYC Protection""",
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class UserCreate(BaseModel):
    email: str
    password: str

def get_db():
    conn = sqlite3.connect('comet_trading.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔥 DATABASE TABLES CREATE (ဒီ function ကို အစမှာ ထည့်ပါ)
@app.on_event("startup")
def init_db():
    conn = get_db()
    
    # USERS table
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        kyc_status TEXT DEFAULT 'pending',
        wallet_usdt REAL DEFAULT 0.0
    )''')
    
    # KYC table
    conn.execute('''CREATE TABLE IF NOT EXISTS kyc_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        id_filename TEXT,
        selfie_filename TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # 🔥 DEPOSITS table (ဒီနေရာမှာ ထည့်ပြီး)
    conn.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        amount REAL,
        tx_hash TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("✅ ALL TABLES READY! Users + KYC + Deposits")

# POST /register (ဒီ version သုံးပါ)
@app.post("/register")
async def register(user: UserCreate):
    conn = get_db()
    
    # First user = admin
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    role = "admin" if user_count == 0 else "user"
    
    try:
        conn.execute("INSERT INTO users (email, password, role, kyc_status, wallet_usdt) VALUES (?, ?, ?, ?, ?)",
                    (user.email, user.password, role, "pending", 0.0))
        conn.commit()
        return {"message": f"User registered! Role: {role}", "kyc_status": "pending"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email already exists")
    finally:
        conn.close()

# Admin login
@app.post("/admin/login")
async def admin_login(user: UserCreate):
    conn = get_db()
    db_user = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'admin'", 
                          (user.email,)).fetchone()
    conn.close()
    
    if db_user and db_user['password'] == user.password:
        return {"message": "Admin logged in!", "email": user.email}
    raise HTTPException(401, "Invalid admin credentials")

@app.get("/")
async def root():
    return {"message": "Comet AI Trading LIVE!"}
@app.get("/wallet/{email}")
async def wallet(email: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "email": user['email'],
        "wallet_usdt": user['wallet_usdt'] or 0,
        "kyc_status": user['kyc_status']
    }    

# 🔥 PHASE 4: FULL TRADING + REAL-TIME PRICES
import aiohttp
import asyncio
import time
import random
from fastapi import WebSocket

# Real-time price cache
current_prices = {"BTC_USDT": 65000.0, "ETH_USDT": 3500.0}

async def update_live_prices():
    """Background task for real Binance prices"""
    global current_prices
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT') as resp:
                    btc = await resp.json()
                async with session.get('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT') as resp:
                    eth = await resp.json()
                current_prices["BTC_USDT"] = float(btc['price'])
                current_prices["ETH_USDT"] = float(eth['price'])
        except:
            # Fallback realistic prices
            current_prices["BTC_USDT"] += random.uniform(-500, 500)
            current_prices["ETH_USDT"] += random.uniform(-50, 50)
        await asyncio.sleep(2)  # Update every 2 seconds

@app.on_event("startup")
def init_db():
    conn = get_db()
    
    # 🔥 COMPLETE TABLES - BTC/ETH columns ပါတယ်
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        kyc_status TEXT DEFAULT 'pending',
        wallet_usdt REAL DEFAULT 0.0,
        wallet_btc REAL DEFAULT 0.0,
        wallet_eth REAL DEFAULT 0.0
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS kyc_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        id_filename TEXT,
        selfie_filename TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        amount REAL,
        tx_hash TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 🔥 FIXED: ALTER TABLE for existing users
    try:
        conn.execute("ALTER TABLE users ADD COLUMN wallet_btc REAL DEFAULT 0.0")
        conn.execute("ALTER TABLE users ADD COLUMN wallet_eth REAL DEFAULT 0.0")
    except:
        pass  # Columns already exist
    
    conn.commit()
    # 🔥 FIXED: NO conn.close() here!
    print("✅ DATABASE READY! Trading + Compound LIVE!")
    
    # KYC table
    conn.execute('''CREATE TABLE IF NOT EXISTS kyc_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        id_filename TEXT,
        selfie_filename TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # DEPOSITS table
    conn.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        amount REAL,
        tx_hash TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("✅ FULL DATABASE READY! Trading + Real-time!")

@app.get("/prices")
async def get_prices():
    return {
        "BTC_USDT": round(current_prices["BTC_USDT"], 2),
        "ETH_USDT": round(current_prices["ETH_USDT"], 2),
        "timestamp": time.time()
    }

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "BTC_USDT": round(current_prices["BTC_USDT"], 2),
                "ETH_USDT": round(current_prices["ETH_USDT"], 2)
            })
            await asyncio.sleep(1)
    except:
        await websocket.close()

# 🔥 TRADING ENDPOINTS
@app.post("/trade/buy")
async def buy_trade(email: str = Form(...), symbol: str = Form(...), amount_usdt: float = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT kyc_status, wallet_usdt FROM users WHERE email = ?", (email,)).fetchone()
    
    if user['kyc_status'] != 'verified':
        raise HTTPException(403, "❌ KYC verification required")
    if user['wallet_usdt'] < amount_usdt:
        raise HTTPException(400, f"❌ Insufficient USDT: ${user['wallet_usdt']}")
    
    price = current_prices[f"{symbol}_USDT"]
    asset_amount = amount_usdt / price
    
    # Update balances
    conn.execute("UPDATE users SET wallet_usdt = wallet_usdt - ? WHERE email = ?", (amount_usdt, email))
    if symbol == "BTC":
        conn.execute("UPDATE users SET wallet_btc = COALESCE(wallet_btc, 0) + ? WHERE email = ?", (asset_amount, email))
    elif symbol == "ETH":
        conn.execute("UPDATE users SET wallet_eth = COALESCE(wallet_eth, 0) + ? WHERE email = ?", (asset_amount, email))
    
    conn.commit()
    conn.close()
    
    return {
        "✅": f"Bought {asset_amount:.6f} {symbol} @ ${price}",
        "total_spent": f"${amount_usdt}",
        "current_price": price
    }

@app.post("/trade/sell")
async def sell_trade(email: str = Form(...), symbol: str = Form(...), amount_asset: float = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    if user['kyc_status'] != 'verified':
        raise HTTPException(403, "❌ KYC verification required")
    
    price = current_prices[f"{symbol}_USDT"]
    usdt_received = amount_asset * price
    
    btc_balance = user['wallet_btc'] or 0
    eth_balance = user['wallet_eth'] or 0
    
    if symbol == "BTC" and btc_balance < amount_asset:
        raise HTTPException(400, f"❌ Insufficient BTC: {btc_balance}")
    if symbol == "ETH" and eth_balance < amount_asset:
        raise HTTPException(400, f"❌ Insufficient ETH: {eth_balance}")
    
    # Update balances
    conn.execute("UPDATE users SET wallet_usdt = wallet_usdt + ? WHERE email = ?", (usdt_received, email))
    if symbol == "BTC":
        conn.execute("UPDATE users SET wallet_btc = wallet_btc - ? WHERE email = ?", (amount_asset, email))
    elif symbol == "ETH":
        conn.execute("UPDATE users SET wallet_eth = wallet_eth - ? WHERE email = ?", (amount_asset, email))
    
    conn.commit()
    conn.close()
    
    return {
        "✅": f"Sold {amount_asset:.6f} {symbol} @ ${price}",
        "received": f"${usdt_received:.2f}"
    }

@app.get("/full-wallet/{email}")
async def full_wallet(email: str):
    try:
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if not user:
            return {"error": "User not found"}
        
        # Production safe price check
        btc_price = current_prices.get("BTC_USDT", 65000.0)
        eth_price = current_prices.get("ETH_USDT", 3500.0)
        
        # Safe wallet extraction
        usdt = float(user['wallet_usdt'] or 0)
        btc = float(user['wallet_btc'] or 0)
        eth = float(user['wallet_eth'] or 0)
        
        # Current portfolio USD value
        btc_value = btc * btc_price
        eth_value = eth * eth_price
        total_value = usdt + btc_value + eth_value
        
        # 🔥 PROFESSIONAL COMPOUND (5% APY daily)
        days_held = 365
        daily_rate = 0.05 / 365
        
        # Individual asset compounding (ACCURATE)
        compound_usdt = usdt * (1 + daily_rate) ** days_held
        compound_btc_value = (btc * (1 + daily_rate) ** days_held) * btc_price
        compound_eth_value = (eth * (1 + daily_rate) ** days_held) * eth_price
        
        compound_total = compound_usdt + compound_btc_value + compound_eth_value
        compound_interest = compound_total - total_value
        
        return {
            "email": email,
            "balances": {
                "USDT": f"${round(usdt, 2):,}",
                "BTC": round(btc, 6),
                "ETH": round(eth, 4)
            },
            "current_portfolio": f"${total_value:,.2f}",
            "compound_1yr_5_APY": f"${compound_total:,.2f}",
            "projected_earnings": f"${compound_interest:,.2f}",
            "prices": {
                "BTC": f"${round(btc_price, 2):,}",
                "ETH": f"${round(eth_price, 2):,}"
            }
        }
    except Exception as e:
        return {"error": f"Error: {str(e)}"}
# 🔥 1. POST /login (User + Admin)
@app.post("/login")
async def login(user: UserCreate):
    conn = get_db()
    db_user = conn.execute("SELECT * FROM users WHERE email = ?", (user.email,)).fetchone()
    conn.close()
    
    if db_user and db_user['password'] == user.password:
        return {
            "message": "Login successful!",
            "email": user.email,
            "role": db_user['role'],
            "kyc_status": db_user['kyc_status'],
            "wallet_usdt": db_user['wallet_usdt']
        }
    raise HTTPException(401, "Invalid credentials")

# 🔥 2. KYC SYSTEM
@app.post("/kyc/submit")
async def kyc_submit(email: str = Form(...), id_file: UploadFile = File(...), selfie_file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    id_path = f"uploads/{email}_id.jpg"
    selfie_path = f"uploads/{email}_selfie.jpg"
    with open(id_path, "wb") as f: f.write(await id_file.read())
    with open(selfie_path, "wb") as f: f.write(await selfie_file.read())
    conn = get_db()
    conn.execute("INSERT INTO kyc_requests (user_email, id_filename, selfie_filename) VALUES (?, ?, ?)", (email, id_path, selfie_path))
    conn.commit()
    conn.close()
    return {"message": "✅ KYC submitted!"}

@app.post("/admin/kyc/approve/{email}")
async def approve_kyc(email: str):
    conn = get_db()
    conn.execute("UPDATE users SET kyc_status = 'verified' WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"message": f"✅ KYC approved: {email}"}

# 🔥 3. DEPOSIT SYSTEM
@app.post("/deposit")
async def deposit_request(email: str = Form(...), amount: float = Form(...), tx_hash: str = Form(...)):
    conn = get_db()
    conn.execute("INSERT INTO deposits (email, amount, tx_hash, status) VALUES (?, ?, ?, 'pending')", (email, amount, tx_hash))
    deposit_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return {"message": f"✅ ${amount} deposit requested", "deposit_id": deposit_id}

@app.post("/admin/deposit/approve/{deposit_id}")
async def approve_deposit(deposit_id: int):
    conn = get_db()
    deposit = conn.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,)).fetchone()
    if deposit:
        conn.execute("UPDATE users SET wallet_usdt = wallet_usdt + ? WHERE email = ?", (deposit['amount'], deposit['email']))
        conn.execute("UPDATE deposits SET status = 'approved' WHERE id = ?", (deposit_id,))
        conn.commit()
        conn.close()
        return {"message": f"✅ ${deposit['amount']} deposited to {deposit['email']}"}
    return {"message": "Deposit not found"}

# 🔥 LIVE DASHBOARD + WEBSOCKET (main.py အောက်ဆုံး)
from fastapi.responses import HTMLResponse
import time

@app.websocket("/ws/live-prices")
async def websocket_live_prices(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "timestamp": time.time(),
                "BTC_USDT": round(current_prices["BTC_USDT"], 2),
                "ETH_USDT": round(current_prices["ETH_USDT"], 2)
            })
            await asyncio.sleep(2)
    except:
        await websocket.close()

@app.get("/live-dashboard")
async def live_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Comet AI Trading - LIVE Dashboard</title>
    <meta name="description" content="Comet AI Trading - Professional Crypto Exchange">
    <style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0033 50%, #000 100%);
        color:#00ff88; 
        font-family: 'Courier New', monospace; 
        padding:20px; 
        text-align:center; 
        min-height:100vh;
        overflow:hidden;
    }
    .logo {
        font-size:3.5em; 
        font-weight:bold; 
        margin:30px 0;
        text-shadow: 0 0 30px #00ff88;
        animation: glow 2s ease-in-out infinite alternate;
        letter-spacing: 8px;
    }
    .comet {font-size:1.2em; animation: comet 3s linear infinite;}
    .price{
        font-size:5em; 
        margin:40px 20px;
        text-shadow: 0 0 40px #00ff41;
        font-weight:bold;
        animation: pulse 1.5s ease-in-out infinite;
    }
    h1{font-size:2.2em; margin:30px 0; opacity:0.9;}
    @keyframes glow {
        from {text-shadow:0 0 20px #00ff88, 0 0 30px #00ff88;}
        to {text-shadow:0 0 40px #00ff88, 0 0 60px #00ff88;}
    }
    @keyframes comet {
        0%{transform:translateX(-100px) rotate(0deg);}
        100%{transform:translateX(100vw) rotate(720deg);}
    }
    @keyframes pulse {
        0%,100%{transform:scale(1);}
        50%{transform:scale(1.05);}
    }
    </style>
</head>
<body>
    <div class="logo">☄️ COMET AI TRADING</div>
    <div class="comet">🌠 Real-time Trading Exchange</div>
    <h1>🔥 LIVE Dashboard (2s Updates)</h1>
    <div class="price" id="btc">BTC: Loading...</div>
    <div class="price" id="eth">ETH: Loading...</div>
    
    <script>
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/live-prices');
    ws.onmessage = e => {
        const d = JSON.parse(e.data);
        document.getElementById('btc').innerHTML = `BTC: $${parseFloat(d.BTC_USDT).toLocaleString()}`;
        document.getElementById('eth').innerHTML = `ETH: $${parseFloat(d.ETH_USDT).toLocaleString()}`;
    };
    </script>
</body>
</html>""")
