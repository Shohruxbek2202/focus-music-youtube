"""
6-QISM: YouTube'ga avtomatik yuklash.

Birinchi ishga tushirishda brauzer orqali bir martalik OAuth ruxsat so'raladi
(shohruxbek.digital@gmail.com akkauntida "Allow" bosish kerak bo'ladi).
Keyingi barcha ishga tushirishlarda token.json fayli orqali avtomatik ishlaydi —
qayta login shart emas.

Ishlatish:
    python3 youtube_upload.py output/calm_101 --privacy unlisted
    python3 youtube_upload.py output/calm_101 --privacy public
"""

import argparse
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


def get_authenticated_service():
    # CI muhitida (GitHub Actions) — GitHub Secrets orqali kelgan ma'lumotlardan.
    env_refresh = os.environ.get("YT_REFRESH_TOKEN")
    env_client_id = os.environ.get("YT_CLIENT_ID")
    env_client_secret = os.environ.get("YT_CLIENT_SECRET")
    if env_refresh and env_client_id and env_client_secret:
        creds = Credentials(
            token=None,
            refresh_token=env_refresh,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env_client_id,
            client_secret=env_client_secret,
            scopes=SCOPES,
        )
        creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)

    # Lokal (Mac) — token.json fayli orqali.
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            print("\nBrauzer ochiladi — shohruxbek.digital@gmail.com akkaunti bilan\n"
                  "'Allow' bosib ruxsat bering...\n")
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(outdir, privacy="unlisted"):
    meta_path = os.path.join(outdir, "youtube_metadata.json")
    video_path = os.path.join(outdir, "piano_video.mp4")
    thumb_path = os.path.join(outdir, "thumbnail.png")

    with open(meta_path) as f:
        meta = json.load(f)

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": meta["title"][:100],
            "description": meta["description"],
            "tags": meta["tags"][:500],
            "categoryId": "10",  # Music
        },
        "status": {
            "privacyStatus": privacy,  # "private" | "unlisted" | "public"
            "selfDeclaredMadeForKids": False,
        },
    }

    print(f"Yuklanmoqda: {meta['title']}  ({privacy})")
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  yuklandi: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Video yuklandi: https://youtu.be/{video_id}")

    if os.path.exists(thumb_path):
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb_path)).execute()
        print("Thumbnail o'rnatildi")

    return video_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir")
    parser.add_argument("--privacy", default="unlisted", choices=["private", "unlisted", "public"])
    args = parser.parse_args()

    upload_video(args.outdir, privacy=args.privacy)
