import os
import requests

# Define the base tokens from Polygon network
POLYGON_BASE_TOKENS = ["USDT", "MATIC", "USDC", "TETHER", "WETH", "WBTC", "DAI"]

# Define the API endpoints for the various price sources
PARASWAP_API_ENDPOINT = "https://apiv4.paraswap.io/v2/prices"
ONEINCH_API_ENDPOINT = "https://api.1inch.exchange/v3.0/1/quote"
COINMARKETCAP_API_ENDPOINT = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
COINLIB_API_ENDPOINT = "https://coinlib.io/api/v1/coin"

# Define mapping of tokens to their contract addresses on Polygon network
TOKEN_CONTRACTS = {
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "MATIC": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
    "USDC": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "TETHER": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
    "WETH": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
    "WBTC": "0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
}

# Define CoinMarketCap and Coinlib API keys
CMC_API_KEY = os.environ.get("CMC_API_KEY")
COINLIB_API_KEY = os.environ.get("COINLIB_API_KEY")

# Define a dictionary to store the fetched prices
prices = {}

def fetch_paraswap_prices():
    """
    Fetches the latest prices for supported trading pairs from the Paraswap API.
    """
    global prices

    for base_asset in POLYGON_BASE_TOKENS:
        url = f"{PARASWAP_API_ENDPOINT}/{TOKEN_CONTRACTS[base_asset]}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            prices[base_asset] = {}

            for quote_asset, quote_data in data.items():
                if quote_asset != "error":
                    prices[base_asset][quote_asset] = float(quote_data["price"])
        else:
            print(f"Error fetching prices from Paraswap API for {base_asset}. Status code: {response.status_code}")

def fetch_oneinch_prices():
    """
    Fetches the latest prices for supported trading pairs from the 1inch API.
    """
    global prices

    for base_asset in POLYGON_BASE_TOKENS:
        prices[base_asset] = {}

        for quote_asset in POLYGON_BASE_TOKENS:
            if base_asset != quote_asset:
                url = f"{ONEINCH_API_ENDPOINT}?fromTokenAddress={TOKEN_CONTRACTS[base_asset]}&toTokenAddress={TOKEN_CONTRACTS[quote_asset]}&amount=1000000000000000000"
                response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    prices[base_asset][quote_asset] = float(data["toTokenAmount"]) / float(data["fromTokenAmount"])
                else:
                    print(f"Error fetching prices from 1inch API for {base_asset}/{quote_asset}. Status code: {response.status_code}")

def fetch_coinmarketcap_prices():
    """
    Fetches the latest prices for supported trading pairs from the CoinMarketCap API.
    """
    global prices

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY
    }

    for base_asset in POLYGON_BASE_TOKENS:
        prices[base_asset] = {}

        for quote_asset in POLYGON_BASE_TOKENS:
            if base_asset != quote_asset:
                response = requests.get(f"{COINMARKETCAP_API_ENDPOINT}?symbol={base_asset}&convert={quote_asset}", headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    prices[base_asset][quote_asset] = data["data"][base_asset]["quote"][quote_asset]["price"]
                else:
                    print(f"Error fetching prices from CoinMarketCap API for {base_asset}/{quote_asset}. Status code: {response.status_code}")

def fetch_coinlib_prices():
    """
    Fetches the latest prices for supported trading pairs from the Coinlib API.
    """
    global prices

    headers = {
        "Accepts": "application/json",
        "user-agent": "arbitrage-bot"
    }

    for base_asset in POLYGON_BASE_TOKENS:
        prices[base_asset] = {}

        for quote_asset in POLYGON_BASE_TOKENS:
            if base_asset != quote_asset:
                response = requests.get(f"{COINLIB_API_ENDPOINT}?symbol={base_asset}_{quote_asset}&pref=USD&key={COINLIB_API_KEY}", headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    prices[base_asset][quote_asset] = float(data["price"])
                else:
                    print(f"Error fetching prices from Coinlib API for {base_asset}/{quote_asset}. Status code: {response.status_code}")

def fetch_prices():
    """
    Fetches the latest prices for supported trading pairs from all sources.
    """
    fetch_paraswap_prices()
    fetch_oneinch_prices()
    fetch_coinmarketcap_prices()
    fetch_coinlib_prices()

def get_price(base_asset: str, quote_asset: str) -> float:
    """
    Returns the current price of a base asset against a quote asset.
    """
    global prices

    if base_asset not in prices:
        print(f"Error: {base_asset} is not a supported base asset.")
        return None

    if quote_asset not in prices[base_asset]:
        print(f"Error: {base_asset}/{quote_asset} is not a supported trading pair.")
        return None

    return prices[base_asset][quote_asset]