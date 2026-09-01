"""One-time YouTube OAuth2 authorization.

Opens a Google consent page in your browser, exchanges the auth code for a
refresh token, and saves the credentials to `youtube_token.json` (gitignored).

Run once:  .venv\Scripts\python youtube_auth.py
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def main():
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("Missing YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET in .env")

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # authorization_prompt="consent" forces the consent screen so a refresh
    # token is always returned (needed for unattended re-uploads).
    creds = flow.run_local_server(port=0, authorization_prompt="consent")

    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_token.json")
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Authorized. Refresh token saved to {token_path}")


if __name__ == "__main__":
    main()
