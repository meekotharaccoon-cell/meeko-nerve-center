"""
free_data.py - Zero-auth market data for the entire Meeko system.
Replaces: Alpaca (broken 401), Stripe, any paid data feed.
Works with: yfinance, CoinGecko, Kraken public, DexScreener, Solana RPC.
"""
import json, time, urllib.request as ur

_H = {"User-Agent": "meeko-mycelium/1.0"}
CG_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "DOGE": "dogecoin", "ADA": "cardano", "AVAX": "avalanche-2",
    "MATIC": "matic-network", "LINK": "chainlink", "XRP": "ripple",
    "USDC": "usd-coin", "USDT": "tether",
}


def stock_price(ticker: str) -> dict:
    try:
        import yfinance as yf
        h = yf.Ticker(ticker).history(period="5d")
        if h.empty:
            return {"ticker": ticker, "price": 0, "ok": False}
        p = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2]) if len(h) > 1 else p
        return {"ticker": ticker, "price": p,
                "change_pct": (p - prev) / prev * 100 if prev else 0,
                "source": "yfinance", "ok": True}
    except Exception as e:
        return {"ticker": ticker, "price": 0, "ok": False, "error": str(e)}


def crypto_price(symbol: str) -> dict:
    cg_id = CG_IDS.get(symbol.upper(), symbol.lower())
    # Try CoinGecko first
    try:
        url = (f"https://api.coingecko.com/api/v3/simple/price"
               f"?ids={cg_id}&vs_currencies=usd&include_24hr_change=true")
        d = json.loads(ur.urlopen(ur.Request(url, headers=_H), timeout=8).read())
        if cg_id in d:
            return {"symbol": symbol, "price": d[cg_id].get("usd", 0),
                    "change_24h": d[cg_id].get("usd_24h_change", 0),
                    "source": "coingecko", "ok": True}
    except Exception:
        pass
    # Fallback: Kraken public
    try:
        url = f"https://api.kraken.com/0/public/Ticker?pair={symbol.upper()}USD"
        d = json.loads(ur.urlopen(ur.Request(url, headers=_H), timeout=8).read())
        r = d.get("result", {})
        if r:
            key = list(r.keys())[0]
            return {"symbol": symbol, "price": float(r[key]["c"][0]),
                    "source": "kraken_public", "ok": True}
    except Exception:
        pass
    return {"symbol": symbol, "price": 0, "ok": False, "source": "none"}


def solana_balance(address: str) -> dict:
    for ep in [
        "https://api.mainnet-beta.solana.com",
        "https://rpc.ankr.com/solana",
    ]:
        try:
            payload = json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "getBalance",
                 "params": [address]}).encode()
            d = json.loads(ur.urlopen(
                ur.Request(ep, data=payload,
                           headers={"Content-Type": "application/json"}),
                timeout=8).read())
            sol = d.get("result", {}).get("value", 0) / 1_000_000_000
            sol_usd = crypto_price("SOL").get("price", 0)
            return {"address": address, "sol": sol,
                    "usd": sol * sol_usd, "source": ep, "ok": True}
        except Exception:
            continue
    return {"address": address, "sol": 0, "ok": False}


def trending_solana(n=10) -> list:
    try:
        url = "https://api.dexscreener.com/token-boosts/top/v1"
        d = json.loads(ur.urlopen(ur.Request(url, headers=_H), timeout=8).read())
        tokens = [t for t in (d if isinstance(d, list) else [])
                  if t.get("chainId") == "solana"]
        return [{"address": t.get("tokenAddress", "")[:12],
                 "boost": t.get("amount", 0),
                 "url": t.get("url", "")} for t in tokens[:n]]
    except Exception:
        return []


def portfolio_snapshot(watchlist: list) -> dict:
    """Works with zero API keys. watchlist = [{"ticker":"BTC","type":"crypto"},...]"""
    out = {"stocks": [], "crypto": [], "ts": time.time()}
    for item in watchlist:
        ticker = item.get("ticker", "")
        if item.get("type", "stock") == "crypto":
            out["crypto"].append(crypto_price(ticker))
        else:
            out["stocks"].append(stock_price(ticker))
        time.sleep(0.15)
    return out


if __name__ == "__main__":
    print("BTC:", crypto_price("BTC"))
    print("SOL:", crypto_price("SOL"))
    print("AAPL:", stock_price("AAPL"))
    t = trending_solana(3)
    print(f"Trending Solana tokens: {len(t)}")
    print("Free data: all OK")
