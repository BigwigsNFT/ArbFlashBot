import requests

def get_paraswap_gas_fee(asset: str) -> float:
    """
    Fetches the gas fee for a given asset from the Paraswap API.
    """
    url = f"https://apiv4.paraswap.io/v2/networks/1/gas-prices/{asset}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        gas_fee = data["gasPrices"]["fast"]
        return gas_fee
    else:
        print(f"Error fetching Paraswap gas fee data for {asset}. Status code: {response.status_code}")

def get_oneinch_gas_fee(asset: str) -> float:
    """
    Fetches the gas fee for a given asset from the 1inch API.
    """
    url = f"https://api.1inch.io/v5.0/1/gasPrice?tokenAddress={asset}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        gas_fee = data["fast"] / 10 ** 9
        return gas_fee
    else:
        print(f"Error fetching 1inch gas fee data for {asset}. Status code: {response.status_code}")

paraswap_gas_fees = {}
oneinch_gas_fees = {}