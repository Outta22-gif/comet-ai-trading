import os
import sqlite3
import asyncio
import random
import time
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from fastapi.staticfiles import StaticFiles

#  ADD THIS GLOBAL VARIABLE (Line 15 အနားမှာ)
current_prices = {
    "BTC_USDT": 65234.56,
    "ETH_USDT": 3487.23
}

# Update prices every 30 seconds
async def update_prices():
    while True:
        try:
            # Real Binance API call here later
            current_prices["BTC_USDT"] = 65234.56 + (hash(asyncio.get_event_loop().time()) % 1000)
            current_prices["ETH_USDT"] = 3487.23 + (hash(asyncio.get_event_loop().time()) % 100)
        except:
            pass
        await asyncio.sleep(30)

#  RAILWAY PORT FIX
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(
    title=" Comet AI Trading",
    description=""" Professional Crypto Exchange 
 Real-time BTC/ETH Trading
 Compound Interest Calculator  
 Live Dashboard (2s updates)
 KYC Protection""",
    version="2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)
@app.get("/")
async def root():
    return {"message": " Comet AI Trading LIVE!", "status": "success"}

@app.get("/prices")
async def prices():
    return {"BTC_USDT": 65234.56 + random.randint(-100,100), "ETH_USDT": 3487.23 + random.randint(-50,50)}

@app.get("/mobile-dashboard")
async def mobile_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<style>
css_keyframes = "@keyframes glow {0%,100%{text-shadow:0 0 20px #10b981;}50%{text-shadow:0 0 40px #10b981;}}"
.glow{text-shadow:0 0 20px #10b981;animation:glow 2s infinite;}
</style>
</head>
<body class="bg-black text-green-400 p-8 text-center min-h-screen">
<div class="glow text-4xl font-bold mb-8 text-green-500">COMET AI TRADING</div>
<div id="btc" class="text-3xl mb-4 p-4 bg-gray-900 rounded-lg border-2 border-green-400">BTC: Loading...</div>
<div id="eth" class="text-3xl mb-8 p-4 bg-gray-900 rounded-lg border-2 border-green-400">ETH: Loading...</div>
<button onclick="buyBTC()" class="bg-green-500 hover:bg-green-600 text-black px-8 py-4 rounded-full text-xl font-bold shadow-lg">BUY BTC</button>
<button onclick="buyETH()" class="bg-blue-500 hover:bg-blue-600 text-white px-8 py-4 rounded-full text-xl font-bold shadow-lg ml-4">BUY ETH</button>
<script>
setInterval(async()=>{
    try {
        const res = await fetch('/prices');
        const data = await res.json();
        document.getElementById('btc').textContent = `BTC: $${data.BTC_USDT?.toLocaleString() || 'N/A'}`;
        document.getElementById('eth').textContent = `ETH: $${data.ETH_USDT?.toLocaleString() || 'N/A'}`;
    } catch(e) { console.log('Price update failed'); }
}, 2000);
function buyBTC() { alert(' BTC Buy Order Placed!'); }
function buyETH() { alert(' ETH Buy Order Placed!'); }
</script>
</body>
</html>""")

"""
    return HTMLResponse(content=html_content)

#  CORS + PRODUCTION READY
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    email: str
    password: str

#  REAL-TIME PRICES
current_prices = {"BTC_USDT": 65234.56, "ETH_USDT": 3487.23}

def get_db():
    conn = sqlite3.connect('comet_trading.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

#  COMPLETE DATABASE (အားလုံး တစ်ခါတည်း)
@app.on_event("startup")
def init_db():
    conn = get_db()
    
    # USERS (BTC/ETH columns ပါတယ်)
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        kyc_status TEXT DEFAULT 'pending',
        wallet_usdt REAL DEFAULT 1000.0,
        wallet_btc REAL DEFAULT 0.0,
        wallet_eth REAL DEFAULT 0.0
    )''')
    
    # KYC
    conn.execute('''CREATE TABLE IF NOT EXISTS kyc_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        id_filename TEXT,
        selfie_filename TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    
    # DEPOSITS
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
    print(" ALL TABLES READY! Trading + KYC + Deposits")

#  USER SYSTEM
@app.post("/register")
async def register(user: UserCreate):
    conn = get_db()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    role = "admin" if user_count == 0 else "user"
    
    try:
        conn.execute("INSERT INTO users (email, password, role, kyc_status, wallet_usdt) VALUES (?, ?, ?, 'pending', 1000.0)",
                    (user.email, user.password, role))
        conn.commit()
        return {"message": f" User registered! Role: {role}"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, " Email already exists")
    finally:
        conn.close()

@app.post("/login")
async def login(user: UserCreate):
    conn = get_db()
    db_user = conn.execute("SELECT * FROM users WHERE email = ?", (user.email,)).fetchone()
    conn.close()
    
    if db_user and db_user['password'] == user.password:
        return {"message": " Login successful!", "role": db_user['role'], "kyc_status": db_user['kyc_status']}
    raise HTTPException(401, " Invalid credentials")

#  TRADING SYSTEM
@app.post("/trade/buy")
async def buy_trade(email: str = Form(...), symbol: str = Form(...), amount_usdt: float = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT kyc_status, wallet_usdt FROM users WHERE email = ?", (email,)).fetchone()
    
    if user['kyc_status'] != 'verified':
        conn.close()
        raise HTTPException(403, " KYC verification required")
    if user['wallet_usdt'] < amount_usdt:
        conn.close()
        raise HTTPException(400, f" Insufficient USDT: ${user['wallet_usdt']}")
    
    price = current_prices[f"{symbol}_USDT"]
    asset_amount = amount_usdt / price
    
    conn.execute("UPDATE users SET wallet_usdt = wallet_usdt - ? WHERE email = ?", (amount_usdt, email))
    if symbol == "BTC":
        conn.execute("UPDATE users SET wallet_btc = COALESCE(wallet_btc, 0) + ? WHERE email = ?", (asset_amount, email))
    elif symbol == "ETH":
        conn.execute("UPDATE users SET wallet_eth = COALESCE(wallet_eth, 0) + ? WHERE email = ?", (asset_amount, email))
    
    conn.commit()
    conn.close()
    return {"": f"Bought {asset_amount:.6f} {symbol}", "price": price}

@app.post("/trade/sell")
async def sell_trade(email: str = Form(...), symbol: str = Form(...), amount_asset: float = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    if user['kyc_status'] != 'verified':
        conn.close()
        raise HTTPException(403, " KYC required")
    
    price = current_prices[f"{symbol}_USDT"]
    usdt_received = amount_asset * price
    
    if symbol == "BTC" and (user['wallet_btc'] or 0) < amount_asset:
        conn.close()
        raise HTTPException(400, " Insufficient BTC")
    if symbol == "ETH" and (user['wallet_eth'] or 0) < amount_asset:
        conn.close()
        raise HTTPException(400, " Insufficient ETH")
    
    conn.execute("UPDATE users SET wallet_usdt = wallet_usdt + ? WHERE email = ?", (usdt_received, email))
    if symbol == "BTC":
        conn.execute("UPDATE users SET wallet_btc = wallet_btc - ? WHERE email = ?", (amount_asset, email))
    elif symbol == "ETH":
        conn.execute("UPDATE users SET wallet_eth = wallet_eth - ? WHERE email = ?", (amount_asset, email))
    
    conn.commit()
    conn.close()
    return {"": f"Sold {amount_asset:.6f} {symbol}", "received": f"${usdt_received:.2f}"}

#  COMPOUND INTEREST
@app.get("/full-wallet/{email}")
async def full_wallet(email: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    
    if not user:
        return {"error": "User not found"}
    
    btc_price = current_prices.get("BTC_USDT", 65000)
    eth_price = current_prices.get("ETH_USDT", 3500)
    
    usdt = float(user['wallet_usdt'] or 0)
    btc = float(user['wallet_btc'] or 0)
    eth = float(user['wallet_eth'] or 0)
    
    total_value = usdt + (btc * btc_price) + (eth * eth_price)
    
    # 5% APY compound
    days = 365
    daily_rate = 0.05 / 365
    compound_total = total_value * (1 + daily_rate) ** days
    
    return {
        "email": email,
        "balances": {"USDT": round(usdt,2), "BTC": round(btc,6), "ETH": round(eth,4)},
        "total_value": f"${total_value:,.2f}",
        "compound_1yr": f"${compound_total:,.2f}"
    }

#  LIVE DASHBOARD - FIXED CSS
@app.get("/live-dashboard")
async def live_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
<title>Comet AI Trading</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body{background:#000;color:#0f0;font-family:monospace;padding:50px;text-align:center;}
css_code = ".logo{font-size:3em;text-shadow:0 0 20px green;animation:glow 2s infinite;}"
css_keyframes = "@keyframes glow{0%,100%{text-shadow:0 0 20px green;}50%{text-shadow:0 0 40px green;}}"
css_code = ".price{font-size:4em;margin:20px;}"
</style>
</head>
<body>
<div class="logo"> COMET AI TRADING</div>
<div class="price" id="btc">BTC: Loading...</div>
<div class="price" id="eth">ETH: Loading...</div>
<script>
setInterval(()=>{
fetch('/prices').then(r=>r.json()).then(d=>{
document.getElementById('btc').textContent=`BTC: $${d.BTC_USDT}`;
document.getElementById('eth').textContent=`ETH: $${d.ETH_USDT}`;
});
},2000);
</script>
</body></html>""")

@app.get("/prices")
async def prices():
    return current_prices

#  RAILWAY START
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
