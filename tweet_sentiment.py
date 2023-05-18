import os
import pymongo
import snscrape.modules.twitter as sntwitter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Define the MongoDB connection details (optional)
MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DB_NAME = "arbitrage_bot"
MONGODB_COLLECTION_NAME = "tweets"

# Define the search terms for tweets
SEARCH_TERMS = ["crypto", "bitcoin", "ethereum", "polygon", "matic"]

def scrape_tweets():
    """
    Scrapes tweets using snscrape and performs sentiment analysis using vaderSentiment.
    """
    # Create an instance of the SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()

    # Connect to MongoDB (optional)
    if MONGODB_URI:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        collection = db[MONGODB_COLLECTION_NAME]

    # Loop through the search terms and scrape tweets
    for search_term in SEARCH_TERMS:
        query = f"{search_term} lang:en"
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= 100:
                break

            # Perform sentiment analysis on the tweet
            sentiment = analyzer.polarity_scores(tweet.content)

            # Print the tweet and sentiment analysis results
            print(f"Tweet: {tweet.content}")
            print(f"Sentiment: {sentiment}")

            # Insert the tweet and sentiment analysis results into MongoDB (optional)
            if MONGODB_URI:
                collection.insert_one({
                    "tweet": tweet.content,
                    "sentiment": sentiment
                })

if __name__ == "__main__":
    scrape_tweets()