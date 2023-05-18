def get_slippage(base_asset: str, trading_pair: str) -> float:
    """
    Estimates the slippage for a given trading pair on a DEX aggregator.
    """
    if trading_pair in paraswap_prices[base_asset]:
        price = paraswap_prices[base_asset][trading_pair]
        gas_fee = gas_fees[base_asset]["paraswap"] + gas_fees[trading_pair]["paraswap"]
    else:
        price = oneinch_prices[base_asset][trading_pair]
        gas_fee = gas_fees[base_asset]["1inch"] + gas_fees[trading_pair]["1inch"]

    slippage = gas_fee / (price * (1 - SLIPPAGE_THRESHOLD)) if price > 0 else 1
    return slippage