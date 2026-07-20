#!/usr/bin/env python3
"""
fetch_youtube_history.py
Fetches your YouTube liked videos and saves them to a daily JSON file.
Requires: pip install google-api-python-client google-auth-oauthlib
"""

import os
import json
import datetime
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# --- CONFIGURATION ---
OUTPUT_DIR = Path.home() / "youtube_history"
CREDENTIALS_FILE = Path.home() / ".youtube_creds" / "client_secret.json"
TOKEN_FILE = Path.home() / ".youtube_creds" / "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
MAX_RESULTS = 200  # max videos to fetch per run
# ----------------------

def get_authenticated_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def fetch_liked_videos(youtube):
    videos = []
    request = youtube.videos().list(
        part="snippet,contentDetails",
        myRating="like",
        maxResults=50
    )
    fetched = 0
    while request and fetched < MAX_RESULTS:
        response = request.execute()
        for item in response.get("items", []):
            snippet = item["snippet"]
            videos.append({
                "id": item["id"],
                "title": snippet.get("title"),
                "channel": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "description": snippet.get("description", "")[:200],
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })
        fetched += len(response.get("items", []))
        request = youtube.videos().list_next(request, response)
    return videos

def save_history(videos):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    output_file = OUTPUT_DIR / f"youtube_history_{today}.json"
    data = {
        "fetched_at": datetime.datetime.now().isoformat(),
        "total_videos": len(videos),
        "videos": videos
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {len(videos)} videos to {output_file}")
    return output_file

def main():
    print(f"[{datetime.datetime.now()}] Starting YouTube history fetch...")
    youtube = get_authenticated_service()
    videos = fetch_liked_videos(youtube)
    save_history(videos)

if __name__ == "__main__":
    main()
