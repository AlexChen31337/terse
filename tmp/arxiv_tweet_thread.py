#!/usr/bin/env python3
"""Post Arxiv-to-code tweet thread via Twitter GraphQL API using cookie auth."""
import json, time, sys, os, re

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

AUTH_TOKEN = "25472f65c86e1e2cc3cfa906e4681319dc056776"
CT0 = "0d42d73880783e42fd267f26fbf6b082374982e72d04b44459f6bd5cca0166f3fdad8f693e733f79c933a618ddae34d1d3b7855db0e9b775ff99caf1d8ca7d01e59e11035cb7fab0c1d02b1067eb2bb1"
BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

OUTFILE = "/media/DATA/.openclaw/workspace/tmp/tweet_results.json"
CHECKPOINT = "/media/DATA/.openclaw/workspace/memory/2026-04-23-arxiv-promo.md"

TWEETS = [
    "Excited to announce @arxiv_to_code — open-source replications of arxiv papers, generated daily by AI coding agents.\n\nEach repo = one paper. MIT licensed. Ship daily.\n\n🔗 github.com/Arxiv-to-code\n\nWhy I built this 🧵",
    "Research papers pile up. Most get read once and forgotten. The code — if it exists — is often behind a Google Drive link, incomplete, or tied to someone's 4-year-old CUDA setup.\n\nI wanted a simpler pattern: pick a paper, ship a working implementation the same week it drops.",
    "The pipeline:\n• Cron scrapes arxiv for interesting papers\n• Claude Sonnet 4.6 reads the PDF\n• Plans a minimal viable replication\n• Scaffolds the repo, writes tests, verifies\n• Opens a public GitHub repo with MIT license\n\nHumans stay in the loop for quality review.",
    "Already 18 papers replicated — multimodal reasoning, RL fine-tuning, agent orchestration, security protocols.\n\nIf you're a researcher and want your paper replicated, drop the arxiv ID below 👇\n\nFollowing up with a LinkedIn writeup tomorrow."
]

GRAPHQL_URL = "https://twitter.com/i/api/graphql/SoVnbfCycZ7fERGCwpZkYA/CreateTweet"

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
    "responsive_web_graphql_skip_user