"""Data intake modules for TrAId.
DNA:TRAID-FEEDS
"""
from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests
import yfinance as yf
import ccxt
import websockets
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(name: str) -> Path:
    return CACHE_DIR / f"{name}.json"


def _load_cache(name: str, ttl: int = 300) -> Any:
    path = _cache_path(name)
    if path.exists() and (datetime.now().timestamp() - path.stat().st_mtime) < ttl:
        with path.open() as fh:
            return json.load(fh)["data"]
    return None


def _save_cache(name: str, data: Any) -> None:
    path = _cache_path(name)
    with path.open("w") as fh:
        json.dump({"timestamp": datetime.utcnow().isoformat(), "data": data}, fh)


@dataclass
class MarketState:
    symbol: str
    prices: List[float]
    volumes: List[float]
    sentiment: float


class YFinanceFeed:
    """Fetches market data using yfinance with local caching."""

    def fetch(self, symbol: str) -> Dict[str, List[float]]:
        cache_key = f"yfinance_{symbol}"
        data = _load_cache(cache_key)
        if data is None:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            data = {
                "prices": hist["Close"].dropna().tolist(),
                "volumes": hist["Volume"].fillna(0).tolist(),
            }
            _save_cache(cache_key, data)
        return data


class CCXTFeed:
    """Fetches crypto data using ccxt with local caching."""

    def __init__(self, exchange: str = "binance"):
        self.exchange = getattr(ccxt, exchange)()

    def fetch(self, symbol: str) -> Dict[str, List[float]]:
        cache_key = f"ccxt_{symbol.replace('/', '_')}"
        data = _load_cache(cache_key)
        if data is None:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe="1m", limit=60)
            df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
            data = {
                "prices": df["close"].tolist(),
                "volumes": df["volume"].tolist(),
            }
            _save_cache(cache_key, data)
        return data


class NewsSentimentFeed:
    """Fetches sentiment data from news articles."""

    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def fetch(self, query: str) -> Dict[str, Any]:
        cache_key = f"news_{query}"
        data = _load_cache(cache_key, ttl=900)
        if data is None:
            api_key = os.environ.get("NEWS_API_KEY", "")
            url = (
                "https://newsapi.org/v2/everything?" f"q={query}&sortBy=publishedAt&language=en&apiKey={api_key}"
            )
            resp = requests.get(url, timeout=10)
            articles = resp.json().get("articles", [])
            sentiments = [
                self.analyzer.polarity_scores(a.get("title", ""))["compound"] for a in articles
            ]
            score = float(np.mean(sentiments)) if sentiments else 0.0
            data = {"score": score, "articles": articles[:5]}
            _save_cache(cache_key, data)
        return data


class BinanceWSFeed:
    """Async Binance websocket ticker feed."""

    async def stream(self, symbol: str):  # pragma: no cover - network
        url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@ticker"
        async with websockets.connect(url) as ws:
            async for msg in ws:
                yield json.loads(msg)


class Feeds:
    """Aggregates multiple feeds into a MarketState."""

    def __init__(self) -> None:
        self.yf = YFinanceFeed()
        self.ccxt = CCXTFeed()
        self.news = NewsSentimentFeed()

    def collect(self, symbol: str) -> MarketState:
        # prefer ccxt (crypto) data, fallback to yfinance
        market: Dict[str, Any] = {}
        ccxt_symbol = symbol.replace("-", "/").replace("USD", "USDT")
        try:
            market = self.ccxt.fetch(ccxt_symbol)
        except Exception:
            market = {}
        if not market.get("prices"):
            market = self.yf.fetch(symbol)

        sentiment_info = self.news.fetch(symbol)
        prices = market.get("prices", [])
        volumes = market.get("volumes", [])
        sentiment = sentiment_info.get("score", 0.0)
        return MarketState(symbol=symbol, prices=prices, volumes=volumes, sentiment=sentiment)
