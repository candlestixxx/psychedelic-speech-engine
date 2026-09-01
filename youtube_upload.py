"""Upload a rendered MP4 to the authorized YouTube channel.

Requires `youtube_auth.py` to have been run once (creates youtube_token.json).

Usage:
  .venv\Scripts\python youtube_upload.py out.mp4 --title "..." \
      --description "..." --privacy unlisted --tags "psytrance,mandelbrot"
"""
import argparse
import json
import os

from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_credentials():
    from google.oauth2.credentials import Credentials

    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_token.json")
    if not os.path.exists(token_path):
        raise SystemExit("Run `youtube_auth.py` first to authorize (no youtube_token.json found).")
    data = json.load(open(token_path, encoding="utf-8"))
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes") or SCOPES,
    )


def upload_video(file_path, title, description="", tags=None, privacy="unlisted",
                 category="22"):
    """Upload `file_path` to the authorized channel; return the video id."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    youtube = build("youtube", "v3", credentials=get_credentials())
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": (tags or [])[:20],
            "categoryId": category,  # 22 = People & Blogs
        },
        "status": {"privacyStatus": privacy},  # private / unlisted / public
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  upload progress: {int(status.progress() * 100)}%")
    print(f"  uploaded: https://youtu.be/{resp['id']}")
    return resp["id"]


def main():
    p = argparse.ArgumentParser(description="Upload a video to YouTube.")
    p.add_argument("video", help="Path to the MP4 to upload")
    p.add_argument("--title", required=True, help="Video title")
    p.add_argument("--description", default="", help="Video description")
    p.add_argument("--privacy", choices=["private", "unlisted", "public"], default="unlisted")
    p.add_argument("--tags", default="", help="Comma-separated tags")
    args = p.parse_args()
    upload_video(
        args.video,
        args.title,
        args.description,
        [t.strip() for t in args.tags.split(",") if t.strip()],
        args.privacy,
    )


if __name__ == "__main__":
    main()
