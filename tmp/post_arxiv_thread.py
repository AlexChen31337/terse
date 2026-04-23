#!/usr/bin/env python3
"""
Post Arxiv-to-code 4-tweet thread via Twitter's internal GraphQL API.
Uses browser auth cookies directly — no Playwright needed.
"""
import json
import time
import sys

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

AUTH_TOKEN = "25472f65c86e1e2cc3cfa906e4681319dc056776"
CT0 = "0d42d73880783e42fd267f26fbf6b082374982e72d04b44459f6bd5cca0166f3fdad8f693e733f79c933a618ddae34d1d3b7855db0e9b775ff99caf1d8ca7d01e59e11035cb7fab0c1d02b1067eb2bb1"

CHECKPOINT_FILE = "/media/DATA/.openclaw/workspace/memory/2026-04-23-arxiv-promo.md"

TWEETS = [
    "Excited to announce @arxiv_to_code — open-source replications of arxiv papers, generated daily by AI coding agents.\n\nEach repo = one paper. MIT licensed. Ship daily.\n\n\U0001f517 github.com/Arxiv-to-code\n\nWhy I built this \U0001f9f5",
    "Research papers pile up. Most get read once and forgotten. The code \u2014 if it exists \u2014 is often behind a Google Drive link, incomplete, or tied to someone\u2019s 4-year-old CUDA setup.\n\nI wanted a simpler pattern: pick a paper, ship a working implementation the same week it drops.",
    "The pipeline:\n\u2022 Cron scrapes arxiv for interesting papers\n\u2022 Claude Sonnet 4.6 reads the PDF\n\u2022 Plans a minimal viable replication\n\u2022 Scaffolds the repo, writes tests, verifies\n\u2022 Opens a public GitHub repo with MIT license\n\nHumans stay in the loop for quality review.",
    "Already 18 papers replicated \u2014 multimodal reasoning, RL fine-tuning, agent orchestration, security protocols.\n\nIf you\u2019re a researcher and want your paper replicated, drop the arxiv ID below \U0001f447\n\nFollowing up with a LinkedIn writeup tomorrow."
]

GRAPHQL_URL = "https://twitter.com/i/api/graphql/SoVnbfCycZ7fERGCwpZkYA/CreateTweet"
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

def get_headers():
    return {
        "authorization": f"Bearer {BEARER}",
        "cookie": f"auth_token={AUTH_TOKEN}; ct0={CT0}",
        "x-csrf-token": CT0,
        "content-type": "application/json",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "x-twitter-active-user": "yes",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "referer": "https://twitter.com/",
        "origin": "https://twitter.com",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
    }

FEATURES = {
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": False,
    "tweet_awards_web_tipping_enabled": False,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

def verify_auth():
    """Verify credentials are valid."""
    url = "https://twitter.com/i/api/2/timeline/home.json"
    # Use simpler verification
    url2 = "https://twitter.com/i/api/1.1/account/verify_credentials.json"
    r = requests.get(url2, headers=get_headers(), timeout=15,
                     params={"skip_status": "true", "include_entities": "false"})
    print(f"Auth check: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        screen_name = data.get("screen_name", "unknown")
        print(f"Authenticated as: @{screen_name}")
        return screen_name
    else:
        print(f"Auth failed: {r.text[:300]}")
        return None

def post_tweet(text, reply_to_id=None):
    """Post a tweet, return (tweet_id, url) or (None, None) on failure."""
    variables = {
        "tweet_text": text,
        "dark_request": False,
        "media": {"media_entities": [], "possibly_sensitive": False},
        "semantic_annotation_ids": [],
        "disallowed_reply_options": None,
    }
    if reply_to_id:
        variables["reply"] = {
            "in_reply_to_tweet_id": reply_to_id,
            "exclude_reply_user_ids": [],
        }

    payload = {
        "variables": variables,
        "features": FEATURES,
        "queryId": "SoVnbfCycZ7fERGCwpZkYA",
    }

    r = requests.post(GRAPHQL_URL, headers=get_headers(), json=payload, timeout=30)
    print(f"  POST status: {r.status_code}")

    if r.status_code != 200:
        print(f"  Error: {r.text[:600]}")
        return None, None

    data = r.json()
    try:
        result = data["data"]["create_tweet"]["tweet_results"]["result"]
        tweet_id = result["rest_id"]
        screen_name = result.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("screen_name", "AlexChen31337")
        url = f"https://twitter.com/{screen_name}/status/{tweet_id}"
        print(f"  Posted: {url}")
        return tweet_id, url
    except (KeyError, TypeError) as e:
        print(f"  Parse error: {e}")
        print(f"  Response: {json.dumps(data, indent=2)[:800]}")
        return None, None

def append_checkpoint(text):
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(f"\n{text}\n")

def main():
    print("=== Arxiv-to-code Twitter Thread ===")

    # Verify auth
    screen_name = verify_auth()
    if not screen_name:
        print("FATAL: Auth verification failed. Aborting.")
        sys.exit(1)

    results = []
    prev_id = None

    for i, tweet_text in enumerate(TWEETS):
        print(f"\n--- Tweet {i+1}/{len(TWEETS)} ---")
        print(f"Text: {tweet_text[:80]}...")

        tweet_id, url = post_tweet(tweet_text, reply_to_id=prev_id)
        if tweet_id is None:
            print(f"FATAL: Tweet {i+1} failed. Aborting thread.")
            # Save partial results
            with open("/media/DATA/.openclaw/workspace/tmp/twitter_results.json", "w") as f:
                json.dump({"success": False, "posted": results, "failed_at": i+1}, f, indent=2)
            sys.exit(1)

        results.append({"index": i+1, "id": tweet_id, "url": url})
        append_checkpoint(f"Tweet {i+1}: {url}")
        prev_id = tweet_id

        if i < len(TWEETS) - 1:
            print(f"  Waiting 15s before next tweet...")
            time.sleep(15)

    print(f"\n=== SUCCESS: {len(results)} tweets posted ===")
    for r in results:
        print(f"  Tweet {r['index']}: {r['url']}")

    with open("/media/DATA/.openclaw/workspace/tmp/twitter_results.json", "w") as f:
        json.dump({"success": True, "posted": results}, f, indent=2)

    return results

if __name__ == "__main__":
    main()
