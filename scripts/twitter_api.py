#!/usr/bin/env python3
"""Twitter API wrapper using OAuth 1.0a keys (replaces bird cookie auth)"""
import tweepy, sys, json, argparse

API_KEY = "BYwrdIkfn852sjAqAbBfwiv0f"
API_SECRET = "JFFvvMjNl9YVKPhfUZGc4jaLLi00MGvxCUtYSroN1Y9rT8wNaX"
ACCESS_TOKEN = "2018569482017648640-WnJ4KFb57urewV0271uo8VBYppc6Ed"
ACCESS_SECRET = "SCcuiTLFC4sirtCcWVy9jgzsrNYHjgzqxkFIGmrbaBDvo"

client = tweepy.Client(
    consumer_key=API_KEY, consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN, access_token_secret=ACCESS_SECRET
)

parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["whoami", "tweet", "search", "timeline"])
parser.add_argument("text", nargs="?")
parser.add_argument("-n", "--count", type=int, default=10)
args = parser.parse_args()

if args.action == "whoami":
    me = client.get_me(user_fields=["public_metrics"])
    print(json.dumps({"username": me.data.username, "id": me.data.id}, indent=2))

elif args.action == "tweet":
    r = client.create_tweet(text=args.text)
    print(f"Tweeted: https://x.com/i/web/status/{r.data['id']}")

elif args.action == "search":
    tweets = client.search_recent_tweets(query=args.text, max_results=min(args.count, 100),
        tweet_fields=["created_at","author_id","public_metrics"])
    for t in (tweets.data or []):
        print(f"[{t.created_at}] {t.text[:100]}")

elif args.action == "timeline":
    me = client.get_me()
    tweets = client.get_users_tweets(me.data.id, max_results=min(args.count, 100),
        tweet_fields=["created_at","public_metrics"])
    for t in (tweets.data or []):
        print(f"[{t.created_at}] {t.text[:100]}")
