import nltk
nltk.download('vader_lexicon')
def get_base_assets():
    """
    Returns a list of base assets that will be used for arbitrage opportunities.
    """
    return ['USDT', 'MATIC', 'USDC', 'TETHER', 'WETH', 'WBTC', 'DAI']