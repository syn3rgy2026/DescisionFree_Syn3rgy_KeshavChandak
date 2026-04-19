"""
live_data_tools.py
------------------
Real-time structured data tools for Synergy Agent.

Tools:
  - get_cricket_score  : Live cricket matches via CricAPI
  - get_weather        : Current weather via OpenWeatherMap
  - get_stock_price    : Stock quotes via yfinance
  - get_crypto_price   : Crypto prices via CoinGecko (no key)
  - get_news           : Top headlines via NewsAPI
  - convert_currency   : Exchange rates via frankfurter.app (no key)

All tools return formatted strings and never raise exceptions.
API keys are read from environment variables (see .env).
"""

import os
import logging

from smolagents import tool

logger = logging.getLogger("live_data_tools")

# ── Shared HTTP helper ────────────────────────────────────────────────

def _get(url: str, params: dict = None, timeout: int = 10) -> dict | None:
    """Make a GET request, return parsed JSON or None on failure."""
    try:
        import requests
        resp = requests.get(url, params=params or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning(f"HTTP request failed [{url}]: {exc}")
        return None


# ── 1. Cricket Score ──────────────────────────────────────────────────

@tool
def get_cricket_score(query: str = "live matches") -> str:
    """Fetch live cricket match scores using CricAPI.

    Retrieves current matches including match name, status, and scores.
    Requires CRICAPI_KEY environment variable.

    Args:
        query: Optional filter string (e.g. 'IPL', 'Test'). Defaults to 'live matches'.

    Returns:
        Formatted string with up to 5 live match summaries.
    """
    api_key = os.getenv("CRICAPI_KEY", "")
    if not api_key:
        return (
            "No CricAPI key found. Set CRICAPI_KEY in your .env file.\n"
            "Get a free key at: https://www.cricapi.com/"
        )

    data = _get(
        "https://api.cricapi.com/v1/currentMatches",
        params={"apikey": api_key, "offset": 0},
    )

    if not data:
        return "Cricket API request failed. Check your internet connection or API key."

    if data.get("status") != "success":
        msg = data.get("reason", "Unknown error")
        return f"CricAPI error: {msg}"

    matches = data.get("data", [])
    if not matches:
        return "No live cricket matches found right now."

    lines = ["Live Cricket Matches", "=" * 40]
    for m in matches[:5]:
        name   = m.get("name", "Unknown Match")
        status = m.get("status", "Status unknown")
        scores = m.get("score", [])

        lines.append(f"\nMatch  : {name}")
        lines.append(f"Status : {status}")

        if scores:
            for s in scores:
                inning = s.get("inning", "")
                runs   = s.get("r", "-")
                wkts   = s.get("w", "-")
                overs  = s.get("o", "-")
                lines.append(f"Score  : {inning} — {runs}/{wkts} ({overs} ov)")
        else:
            lines.append("Score  : Not yet available")

        lines.append("-" * 40)

    return "\n".join(lines)


# ── 2. Weather ────────────────────────────────────────────────────────

@tool
def get_weather(city: str) -> str:
    """Get current weather for any city using OpenWeatherMap.

    Requires OPENWEATHER_API_KEY environment variable.

    Args:
        city: City name (e.g. 'Mumbai', 'London', 'New York').

    Returns:
        Formatted string with temperature, conditions, humidity, and wind.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not api_key:
        return (
            "No OpenWeatherMap key found. Set OPENWEATHER_API_KEY in your .env file.\n"
            "Get a free key at: https://openweathermap.org/api"
        )

    data = _get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": api_key, "units": "metric"},
    )

    if not data:
        return f"Weather request failed for '{city}'. Check city name or internet connection."

    if data.get("cod") != 200:
        msg = data.get("message", "Unknown error")
        return f"OpenWeatherMap error for '{city}': {msg}"

    main    = data.get("main", {})
    wind    = data.get("wind", {})
    weather = data.get("weather", [{}])[0]
    name    = data.get("name", city)
    country = data.get("sys", {}).get("country", "")

    temp      = main.get("temp", "N/A")
    feels     = main.get("feels_like", "N/A")
    humidity  = main.get("humidity", "N/A")
    condition = weather.get("description", "N/A").capitalize()
    wind_spd  = wind.get("speed", "N/A")

    return (
        f"Weather in {name}, {country}\n"
        f"{'=' * 35}\n"
        f"Condition  : {condition}\n"
        f"Temperature: {temp}°C (feels like {feels}°C)\n"
        f"Humidity   : {humidity}%\n"
        f"Wind Speed : {wind_spd} m/s"
    )


# ── 3. Stock Price ────────────────────────────────────────────────────

@tool
def get_stock_price(symbol: str) -> str:
    """Get real-time stock price and daily stats using yfinance (no API key needed).

    Args:
        symbol: Stock ticker symbol (e.g. 'AAPL', 'TSLA', 'RELIANCE.NS').

    Returns:
        Formatted string with current price, daily high/low, and % change.
    """
    try:
        import yfinance as yf
    except ImportError:
        return "yfinance is not installed. Run: pip install yfinance"

    try:
        ticker = yf.Ticker(symbol.upper())
        info   = ticker.fast_info

        price   = getattr(info, "last_price",       None)
        high    = getattr(info, "day_high",          None)
        low     = getattr(info, "day_low",           None)
        prev    = getattr(info, "previous_close",    None)
        currency = getattr(info, "currency",         "USD")

        if price is None:
            return f"No data found for symbol '{symbol}'. Check the ticker and try again."

        change_pct = ((price - prev) / prev * 100) if prev else 0
        direction  = "+" if change_pct >= 0 else ""

        return (
            f"Stock: {symbol.upper()}  ({currency})\n"
            f"{'=' * 35}\n"
            f"Current Price : {currency} {price:,.2f}\n"
            f"Day High      : {currency} {high:,.2f}\n"
            f"Day Low       : {currency} {low:,.2f}\n"
            f"Change        : {direction}{change_pct:.2f}%"
        )
    except Exception as exc:
        return f"Failed to fetch stock data for '{symbol}': {exc}"


# ── 4. Crypto Price ───────────────────────────────────────────────────

@tool
def get_crypto_price(coin: str) -> str:
    """Get cryptocurrency price, market cap, and 24-hour change via CoinGecko.

    No API key required.

    Args:
        coin: Coin name or CoinGecko ID (e.g. 'bitcoin', 'ethereum', 'solana').

    Returns:
        Formatted string with price, market cap, and 24h % change.
    """
    # Normalise common aliases
    aliases = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
        "bnb": "binancecoin", "xrp": "ripple", "ada": "cardano",
        "doge": "dogecoin", "shib": "shiba-inu", "matic": "matic-network",
        "dot": "polkadot", "ltc": "litecoin", "avax": "avalanche-2",
    }
    coin_id = aliases.get(coin.lower(), coin.lower())

    data = _get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
        },
    )

    if not data:
        return f"CoinGecko request failed for '{coin}'. Check internet connection."

    if not data:
        return f"Coin '{coin}' not found. Try the CoinGecko ID (e.g. 'bitcoin', 'ethereum')."

    c = data[0] if data else None
    if not c:
        return f"No data returned for '{coin}'. Try the exact CoinGecko coin ID."

    name       = c.get("name", coin)
    symbol_str = c.get("symbol", "").upper()
    price      = c.get("current_price", 0)
    market_cap = c.get("market_cap", 0)
    change_24h = c.get("price_change_percentage_24h", 0) or 0
    direction  = "+" if change_24h >= 0 else ""

    def fmt_large(n):
        if n >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"${n / 1_000_000:.2f}M"
        return f"${n:,.0f}"

    return (
        f"Crypto: {name} ({symbol_str})\n"
        f"{'=' * 35}\n"
        f"Current Price : ${price:,.4f}\n"
        f"Market Cap    : {fmt_large(market_cap)}\n"
        f"24h Change    : {direction}{change_24h:.2f}%"
    )


# ── 5. News ───────────────────────────────────────────────────────────

@tool
def get_news(query: str) -> str:
    """Fetch top 5 news headlines for any topic using NewsAPI.

    Requires NEWS_API_KEY environment variable.

    Args:
        query: Search topic (e.g. 'AI', 'cricket IPL', 'stock market').

    Returns:
        Formatted string with top 5 headlines, sources, and descriptions.
    """
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        return (
            "No NewsAPI key found. Set NEWS_API_KEY in your .env file.\n"
            "Get a free key at: https://newsapi.org/"
        )

    data = _get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "apiKey": api_key,
            "pageSize": 5,
            "language": "en",
            "sortBy": "publishedAt",
        },
    )

    if not data:
        return f"News request failed for '{query}'. Check your API key or internet connection."

    if data.get("status") != "ok":
        msg = data.get("message", "Unknown error")
        return f"NewsAPI error: {msg}"

    articles = data.get("articles", [])
    if not articles:
        return f"No news articles found for '{query}'."

    lines = [f"Top News: {query}", "=" * 45]
    for i, a in enumerate(articles[:5], 1):
        title   = a.get("title", "No title")
        source  = a.get("source", {}).get("name", "Unknown")
        desc    = a.get("description") or "No description available."
        # Trim description to 120 chars
        if len(desc) > 120:
            desc = desc[:117] + "..."
        lines.append(f"\n{i}. {title}")
        lines.append(f"   Source : {source}")
        lines.append(f"   {desc}")

    return "\n".join(lines)


# ── 6. Currency Conversion ────────────────────────────────────────────

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies using frankfurter.app (no API key needed).

    Args:
        amount: Amount to convert (e.g. 100.0).
        from_currency: Source currency code (e.g. 'USD', 'INR', 'EUR').
        to_currency: Target currency code (e.g. 'GBP', 'JPY', 'USD').

    Returns:
        Formatted string with converted amount and exchange rate.
    """
    from_c = from_currency.upper().strip()
    to_c   = to_currency.upper().strip()

    data = _get(
        f"https://api.frankfurter.app/latest",
        params={"from": from_c, "to": to_c},
    )

    if not data:
        return (
            f"Currency conversion failed for {from_c} → {to_c}. "
            "Check currency codes or internet connection."
        )

    if "error" in data:
        return f"Frankfurter API error: {data['error']}"

    rates = data.get("rates", {})
    if to_c not in rates:
        return (
            f"Exchange rate for {to_c} not found. "
            f"Supported currencies include: USD, EUR, GBP, INR, JPY, AUD, CAD, CHF, CNY."
        )

    rate      = rates[to_c]
    converted = amount * rate

    return (
        f"Currency Conversion\n"
        f"{'=' * 35}\n"
        f"Amount        : {amount:,.2f} {from_c}\n"
        f"Exchange Rate : 1 {from_c} = {rate:.4f} {to_c}\n"
        f"Converted     : {converted:,.2f} {to_c}"
    )


# ── Export list ───────────────────────────────────────────────────────

LIVE_DATA_TOOLS = [
    get_cricket_score,
    get_weather,
    get_stock_price,
    get_crypto_price,
    get_news,
    convert_currency,
]
