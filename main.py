import os
import sqlite3
import asyncio
import random
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# ------------------ GLOBAL PRICE ------------------
current_prices = {
    "BTC_USDT": 65234.56,
    "ETH_USDT": 3487.23
}

# ------------------ PRICE UPDATER ------------------
async def update_prices():
    while True:
        current_prices["BTC_USDT"] += random.randint(-100, 100)
        current_prices["ETH_USDT"] += random.randint(-50, 50)
        await asyncio.sleep(5)

# ------------------ APP ------------------
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="Comet AI Trading")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# static folder (optional use)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------ DATABASE ------------------
def get_db():
    conn = sqlite3.connect("comet_trading.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
async def startup():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        kyc_status TEXT DEFAULT 'pending',
        wallet_usdt REAL DEFAULT 1000,
        wallet_btc REAL DEFAULT 0,
        wallet_eth REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

    asyncio.create_task(update_prices())

# ------------------ MODEL ------------------
class UserCreate(BaseModel):
    email: str
    password: str

# ------------------ BASIC ------------------
@app.get("/")
async def root():
    return {"message": "Comet AI Trading running"}

@app.get("/prices")
async def prices():
    return current_prices

# ------------------ MOBILE DASHBOARD ------------------
@app.get("/mobile-dashboard")
async def mobile_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.tailwindcss.com"></script>
<style>
@keyframes glow {
  0%,100% { text-shadow:0 0 20px #10b981; }
  50% { text-shadow:0 0 40px #10b981; }
}
.glow {
  animation: glow 2s infinite;
}
</style>
</head>
<body class="bg-black text-green-400 p-6 text-center">

<div class="glow text-3xl font-bold mb-6">COMET AI TRADING</div>

<div id="btc" class="text-xl mb-3 p-3 bg-gray-900 rounded border border-green-400">
BTC: Loading...
</div>

<div id="eth" class="text-xl mb-6 p-3 bg-gray-900 rounded border border-green-400">
ETH: Loading...
</div>

<button onclick="buy('BTC')" class="bg-green-500 px-5 py-2 rounded text-black">BUY BTC</button>
<button onclick="buy('ETH')" class="bg-blue-500 px-5 py-2 rounded text-white ml-2">BUY ETH</button>

<script>
setInterval(async ()=>{
    const res = await fetch('/prices');
    const data = await res.json();
    document.getElementById('btc').innerText = "BTC: $" + data.BTC_USDT;
    document.getElementById('eth').innerText = "ETH: $" + data.ETH_USDT;
},2000);

function buy(symbol){
    alert(symbol + " order placed");
}
</script>

</body>
</html>
""")

# ------------------ DESKTOP DASHBOARD ------------------
@app.get("/live-dashboard")
async def live_dashboard():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
<title>Comet AI Trading</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
body {
    background:#000;
    color:#0f0;
    text-align:center;
    padding:50px;
    font-family:monospace;
}
@keyframes glow {
  0%,100% { text-shadow:0 0 20px green; }
  50% { text-shadow:0 0 40px green; }
}
.logo {
    font-size:40px;
    animation: glow 2s infinite;
}
.price {
    font-size:30px;
    margin:20px;
}
</style>
</head>
<body>

<div class="logo">COMET AI TRADING</div>

<div id="btc" class="price">BTC: Loading...</div>
<div id="eth" class="price">ETH: Loading...</div>

<script>
setInterval(async ()=>{
    const r = await fetch('/prices');
    const d = await r.json();
    document.getElementById('btc').innerText = "BTC: $" + d.BTC_USDT;
    document.getElementById('eth').innerText = "ETH: $" + d.ETH_USDT;
},2000);
</script>

</body>
</html>
""")

# ------------------ AUTH ------------------
@app.post("/register")
async def register(user: UserCreate):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (user.email, user.password)
        )
        conn.commit()
        return {"message": "User registered"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email exists")
    finally:
        conn.close()

@app.post("/login")
async def login(user: UserCreate):
    conn = get_db()
    db_user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (user.email,)
    ).fetchone()
    conn.close()

    if db_user and db_user["password"] == user.password:
        return {"message": "Login success"}
    raise HTTPException(401, "Invalid credentials")

# ------------------ TRADING ------------------
@app.post("/trade/buy")
async def buy_trade(email: str = Form(...), symbol: str = Form(...), amount: float = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    if not user:
        raise HTTPException(404, "User not found")

    if user["wallet_usdt"] < amount:
        raise HTTPException(400, "Insufficient USDT")

    price = current_prices[f"{symbol}_USDT"]
    asset = amount / price

    conn.execute("UPDATE users SET wallet_usdt = wallet_usdt - ? WHERE email=?", (amount, email))

    if symbol == "BTC":
        conn.execute("UPDATE users SET wallet_btc = wallet_btc + ? WHERE email=?", (asset, email))
    elif symbol == "ETH":
        conn.execute("UPDATE users SET wallet_eth = wallet_eth + ? WHERE email=?", (asset, email))

    conn.commit()
    conn.close()

    return {"message": f"Bought {asset:.6f} {symbol}"}

@app.post("/trade/sell")
async def sell_trade(email: str = Form(...), symbol: str = Form(...), amount: float = Form(...)):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    if not user:
        raise HTTPException(404, "User not found")

    price = current_prices[f"{symbol}_USDT"]
    usdt = amount * price

    if symbol == "BTC" and user["wallet_btc"] < amount:
        raise HTTPException(400, "Insufficient BTC")
    if symbol == "ETH" and user["wallet_eth"] < amount:
        raise HTTPException(400, "Insufficient ETH")

    conn.execute("UPDATE users SET wallet_usdt = wallet_usdt + ? WHERE email=?", (usdt, email))

    if symbol == "BTC":
        conn.execute("UPDATE users SET wallet_btc = wallet_btc - ? WHERE email=?", (amount, email))
    elif symbol == "ETH":
        conn.execute("UPDATE users SET wallet_eth = wallet_eth - ? WHERE email=?", (amount, email))

    conn.commit()
    conn.close()

    return {"message": f"Sold {amount} {symbol}"}

# ------------------ RUN ------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
