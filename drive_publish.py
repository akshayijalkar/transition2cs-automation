"""Transition2CS: Drive MP4 queue -> verified YouTube channel.
Safe-by-default: no uploads unless UPLOAD_ENABLED == 'true'.
"""
import io
import json
import os
import re
import time
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

ROOT = "https://api.github.com"
READ_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
YT_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]

def required(key):
    result = os.getenv(key, "").strip()
    if not result:
        raise RuntimeError("Missing required variable/secret: " + key)
    return result

def credentials(refresh_token, scopes):
    c = Credentials(
        None, refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("YOUTUBE_CLIENT_ID"),
        client_secret=required("YOUTUBE_CLIENT_SECRET"),
        scopes=scopes,
    )
    c.refresh(Request())
    return c

def api_services():
    drive = build("drive", "v3", credentials=credentials(required("DRIVE_REFRESH_TOKEN"), [READ_SCOPE]),
                  cache_discovery=False)
    youtube = build("youtube", "v3", credentials=credentials(required("YOUTUBE_REFRESH_TOKEN"), YT_SCOPES),
                    cache_discovery=False)
    return drive, youtube

def get_queue(drive):
    folder = required("DRIVE_FOLDER_ID")
    files = []
    token = None
    while True:
        response = drive.files().list(
            q="'%s' in parents and trashed = false and (mimeType = 'video/mp4' or name contains '.mp4')" % folder,
            fields="nextPageToken,files(id,name,mimeType,size,createdTime)",
            page_size=100, page_token=token,
            orderBy="createdTime asc",
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        files += [f for f in response.get("files", [])
                  if f.get("name", "").lower().endswith(".mp4")]
        token = response.get("nextPageToken")
        if not token:
            return files

def ledger_request(method, path, payload=None):
    headers = {
        "Authorization": "Bearer " + required("GITHUB_TOKEN"),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    return requests.request(method, ROOT + "/repos/" + required("GITHUB_REPOSITORY") +
                            "/contents/" + path, headers=headers, json=payload, timeout=45)

def fetch_ledger():
    import base64
    r = ledger_request("GET", "uploaded.json")
    if r.status_code == 404:
        return {}, None
    r.raise_for_status()
    obj = r.json()
    return json.loads(base64.b64decode(obj["content"]).decode()), obj["sha"]

def save_ledger(data, sha):
    import base64
    payload = {
        "message": "Record claimed Transition2CS Drive video",
        "content": base64.b64encode((json.dumps(data, indent=2, sort_keys=True) + "\n").encode()).decode(),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    r = ledger_request("PUT", "uploaded.json", payload)
    r.raise_for_status()

def download_video(drive, file_info):
    import tempfile
    max_size = 180 * 1024 * 1024
    if int(file_info.get("size") or 0) > max_size:
        raise RuntimeError("MP4 exceeds 180 MB safety size limit")
    fh = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    size = 0
    try:
        request = drive.files().get_media(fileId=file_info["id"])
        downloader = MediaIoBaseDownload(fh, request, chunksize=4 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            size = fh.tell()
            if size > max_size:
                raise RuntimeError("MP4 exceeds 180 MB download limit")
    finally:
        fh.close()
    if size < 100000:
        raise RuntimeError("Downloaded file is too small for a valid video")
    return fh.name

def main():
    enabled = os.getenv("UPLOAD_ENABLED", "").lower() == "true"
    drive, youtube = api_services()
    expected = required("YOUTUBE_CHANNEL_ID")
    items = youtube.channels().list(part="id,snippet", mine=True).execute().get("items", [])
    if len(items) != 1 or items[0]["id"] != expected:
        raise RuntimeError("OAuth channel does not match Transition2CS; refusing upload")
    print("Verified YouTube channel:", items[0]["snippet"]["title"])
    queue = get_queue(drive)
    print("Drive MP4 files available:", len(queue))
    if not enabled:
        print("DRY RUN ONLY: UPLOAD_ENABLED is false. No downloads or uploads.")
        for f in queue[:5]:
            print("Queued:", f["name"], "ID:", f["id"])
        return
    data, sha = fetch_ledger()
    pending = [f for f in queue if f["id"] not in data]
    if not pending:
        print("No unprocessed MP4; nothing uploaded.")
        return
    chosen = pending[0]
    # Claim FIRST to avoid unintended duplicate public posts if later stages fail.
    data[chosen["id"]] = {"name": chosen["name"], "state": "claimed",
                           "claimedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    save_ledger(data, sha)
    print("Claimed video:", chosen["name"], "ID:", chosen["id"])
    path = download_video(drive, chosen)
    title = re.sub(r"[_-]+", " ", chosen["name"].rsplit(".", 1)[0]).strip()[:85] or "Transition2CS"
    privacy = os.getenv("YOUTUBE_PRIVACY", "private").lower()
    if privacy not in ("private", "unlisted", "public"):
        raise RuntimeError("Invalid YouTube privacy setting")
    body = {
        "snippet": {
            "title": title + " | Transition2CS #Shorts",
            "description": "Educational AI-generated visual created with Google Flow/Veo. #Transition2CS #ComputerScience #Shorts",
            "categoryId": "28",
            "tags": ["Transition2CS", "Computer Science", "AI"]
        },
        "status": {"privacyStatus": privacy,
                   "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True}
    }
    request = youtube.videos().insert(
        part="snippet,status", body=body,
        media_body=MediaFileUpload(path, mimetype="video/mp4", resumable=True)
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    print("Upload succeeded. Video ID:", response["id"], "Privacy:", privacy)
    # Claimed entries are intentionally never retried automatically.

if __name__ == "__main__":
    main()
