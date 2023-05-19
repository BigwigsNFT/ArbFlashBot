import time
import os
from typing import List
from web3 import Web3
from dotenv import load_dotenv
from price import fetch_prices, get_price
from tweet_sentiment import scrape_tweets
from findarbitrage import find_arbitrage_sequence

# Load environment variables
load_dotenv()

# Define the trading pairs to check for arbitrage opportunities
TRADING_PAIRS = [
    "ETH/USDT",
    "ETH/USDC",
    "ETH/DAI",
    "MATIC/USDT",
    "MATIC/USDC",
    "MATIC/DAI"
]

# Define the slippage percentage to use when checking for arbitrage opportunities
SLIPPAGE = 0.005

# Define the gas price to use when submitting transactions
GAS_PRICE = Web3.toWei("50", "gwei")

# Define the duration of the arbitrage trades (in seconds)
TRADE_DURATION = 3600  # 1 hour

# Define the annual interest rates for lending assets
LENDING_RATES = {
    "USDT": 0.05,
    "USDC": 0.03,
    "DAI": 0.01
}

# Define the minimum expected profit to proceed with arbitrage (in USD)
MIN_PROFIT = 10

# Define the wallet addresses to use for trading
WALLET_ADDRESS_1 = os.environ.get("WALLET_ADDRESS_1")
WALLET_ADDRESS_2 = os.environ.get("WALLET_ADDRESS_2")

# Define the private keys for the wallet addresses
WALLET_PRIVATE_KEY_1 = os.environ.get("WALLET_PRIVATE_KEY_1")
WALLET_PRIVATE_KEY_2 = os.environ.get("WALLET_PRIVATE_KEY_2")

# Define the Ethereum network and provider endpoint
NETWORK = "polygon"
PROVIDER_ENDPOINT = "https://rpc-mainnet.maticvigil.com"

# Define the contract addresses for the lending protocols
AAVE_LENDING_POOL_ADDRESSES = {
    "USDT": "0x8dff5e27ea6b7ac08ebfdf9eb090f32ee9a30fcf",
    "USDC": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "DAI": "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063"
}

COMPOUND_LENDING_POOL_ADDRESSES = {
    "USDT": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "USDC": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "DAI": "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063"
}

# Define the contract addresses for the decentralized exchanges
PARASWAP_EXCHANGE_ADDRESS = "0x90249ed4d69D70E709fFCd8beE2c5bD8d4D0c0Be"
ONEINCH_EXCHANGE_ADDRESS = "0x11111112542d85b3ef69ae05771c2dccff4faa26"

# Define the contract ABI for the lending protocols
LENDING_POOL_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "asset",
                "type": "address"
            }
        ],
        "name": "getReserveData",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "availableLiquidity",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "totalStableDebt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "totalVariableDebt",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "liquidityRate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "variableBorrowRate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "stableBorrowRate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "averageStableBorrowRate",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "liquidityIndex",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "variableBorrowIndex",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Define the contract ABI for the decentralized exchanges
EXCHANGE_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenIn",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "tokenOut",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "amountOutMin",
                "type": "uint256"
            },
            {
                "internalType": "address[]",
                "name": "path",
                "type": "address[]"
            },
            {
                "internalType": "address",
                "name": "to",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "deadline",
                "type": "uint256"
            }
        ],
        "name": "swap",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "amountOut",
                "type": "uint256"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def check_yield_vs_profit(pair: str, paraswap_price: float, oneinch_price: float, cmc_price: float, coinlib_price: float) -> bool:
    """
    Checks if the potential yield for lending assets over the duration of arbitrage trades outweighs expected profit.
    Returns True if the potential yield outweighs the expected profit, False otherwise.
    """
    base_asset, quote_asset = pair.split("/")
    lending_rate = LENDING_RATES.get(quote_asset)

    if not lending_rate:
        return False  # cannot lend quote asset

    # Calculate the potential yield for lending assets over the duration of arbitrage trades
    lending_pool_address = AAVE_LENDING_POOL_ADDRESSES.get(quote_asset)
    if not lending_pool_address:
        lending_pool_address = COMPOUND_LENDING_POOL_ADDRESSES.get(quote_asset)
        if not lending_pool_address:
            return False  # lending pool not found

    web3 = Web3(Web3.HTTPProvider(PROVIDER_ENDPOINT))
    lending_pool_contract = web3.eth.contract(address=lending_pool_address, abi=LENDING_POOL_ABI)
    reserve_data = lending_pool_contract.functions.getReserveData(Web3.toChecksumAddress(base_asset)).call()
    available_liquidity = reserve_data[0]
    lending_duration_in_years = TRADE_DURATION / (365 * 24 * 60 * 60)
    potential_yield = available_liquidity * (1 + lending_rate) ** lending_duration_in_years - available_liquidity

    # Calculate the expected profit from arbitrage trades
    paraswap_profit = paraswap_price / oneinch_price * cmc_price * (1 - SLIPPAGE) - cmc_price * (1 + SLIPPAGE)
    oneinch_profit = oneinch_price / paraswap_price * cmc_price * (1 - SLIPPAGE) - cmc_price * (1 + SLIPPAGE)
    expected_profit = max(paraswap_profit, oneinch_profit)

    # Compare the potential yield and expected profit
    if potential_yield > expected_profit:
        return True  # potential yield outweighs expected profit

    return False  # expected profit outweighs potential yield

def check_arbitrage(pair: str, paraswap_price: float, oneinch_price: float, cmc_price: float, coinlib_price: float, sentiment: dict) -> dict:
    """
    Checks for arbitrage opportunities for the given trading pair and prices.
    Returns a dictionary containing the trading pair, prices, and whether an arbitrage opportunity exists.
    """
    base_asset, quote_asset = pair.split("/")
    paraswap_fee = paraswap_price * SLIPPAGE
    oneinch_fee = oneinch_price * SLIPPAGE

    # Check if potential yield for lending assets outweighs expected profit
    if check_yield_vs_profit(pair, paraswap_price, oneinch_price, cmc_price, coinlib_price):
        print(f"Not proceeding with arbitrage for {pair}: potential yield for lending assets outweighs expected profit")
        return {
            "pair": pair,
            "paraswap_price": paraswap_price,
            "oneinch_price": oneinch_price,
            "cmc_price ": cmc_price,
            "coinlib_price": coinlib_price,
"sentiment": sentiment,
"arbitrage_opportunity": False
}

# Check if the sentiment for the base asset is positive
if sentiment.get(base_asset, 0) < 0:
    print(f"Not proceeding with arbitrage for {pair}: negative sentiment for {base_asset}")
    return {
        "pair": pair,
        "paraswap_price": paraswap_price,
        "oneinch_price": oneinch_price,
        "cmc_price": cmc_price,
        "coinlib_price": coinlib_price,
        "sentiment": sentiment,
        "arbitrage_opportunity": False
    }

# Check if the prices on Paraswap and 1inch differ enough to allow for arbitrage
if paraswap_price * (1 + SLIPPAGE) >= oneinch_price:
    print(f"Not proceeding with arbitrage for {pair}: Paraswap price not lower than 1inch price")
    return {
        "pair": pair,
        "paraswap_price": paraswap_price,
        "oneinch_price": oneinch_price,
        "cmc_price": cmc_price,
        "coinlib_price": coinlib_price,
        "sentiment": sentiment,
        "arbitrage_opportunity": False
    }

# Check if the prices on CoinMarketCap and CoinLib differ enough to allow for arbitrage
if cmc_price * (1 + SLIPPAGE) <= coinlib_price:
    print(f"Not proceeding with arbitrage for {pair}: CoinMarketCap price not higher than CoinLib price")
    return {
        "pair": pair,
        "paraswap_price": paraswap_price,
        "oneinch_price": oneinch_price,
        "cmc_price": cmc_price,
        "coinlib_price": coinlib_price,
        "sentiment": sentiment,
        "arbitrage_opportunity": False
    }

# Check if the expected profit from arbitrage trades exceeds the minimum required profit
paraswap_profit = paraswap_price / oneinch_price * cmc_price * (1 - SLIPPAGE) - cmc_price * (1 + SLIPPAGE)
oneinch_profit = oneinch_price / paraswap_price * cmc_price * (1 - SLIPPAGE) - cmc_price * (1 + SLIPPAGE)
expected_profit = max(paraswap_profit, oneinch_profit)

if expected_profit < MIN_PROFIT:
    print(f"Not proceeding with arbitrage for {pair}: expected profit below minimum required profit")
    return {
        "pair": pair,
        "paraswap_price": paraswap_price,
        "oneinch_price": oneinch_price,
        "cmc_price": cmc_price,
        "coinlib_price": coinlib_price,
        "sentiment": sentiment,
        "arbitrage_opportunity": False
    }

# Arbitrage opportunity found
print(f"Arbitrage opportunity found for {pair}: expected profit of {expected_profit:.2f} USD")
return {
    "pair": pair,
    "paraswap_price": paraswap_price,
    "oneinch_price": oneinch_price,
    "cmc_price": cmc_price,
    "coinlib_price": coinlib_price,
    "sentiment": sentiment,
    "arbitrage_opportunity": True
}