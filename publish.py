"""Transition2CS: use a pre-tested Hugging Face Gradio Wan 2.2 Space.
Expected Gradio endpoint: /generate(prompt) -> video path/file.
Not enabled until connected and tested; no paid APIs used.
"""
import datetime as dt
import hashlib
import os
from pathlib import Path
from gradio_client import Client, handle_file
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TOPICS = [
    "How the internet routes packets",
    "What happens when you type a URL",
    "Cloud computing explained visually",
    "Encryption and secure communication",
    "How AI neural networks learn",
    "Docker containers versus virtual machines",
    "What is a firewall",
    "How Kubernetes schedules workloads",
    "How DNS works",
    "What is zero trust security",
]

def main():
    now = dt.datetime.now(IST)
    day = now.date().isoformat()
    ix = int(hashlib.sha256(day.encode()).hexdigest(), 16) % len(TOPICS)
    topic = TOPICS[ix]
    prompt = (
        f"Create a visually engaging 9:16 educational short about: {topic}. "
        "Clear accurate on-screen visual metaphors, clean modern technology style, "
        "cinematic motion, polished visual sequence, no trademarked characters, "
        "no fake credentials, no false security claims."
    )
    print("Date:", day, "Topic:", topic)
    client = Client(os.environ["HF_SPACE"], token=os.environ["HF_TOKEN"])
    result = client.predict(prompt, api_name="/generate")
    if isinstance(result, dict):
        result = result.get("video") or result.get("path") or result.get("name")
    elif isinstance(result, (list, tuple)):
        result = result[0]
    if not isinstance(result, str):
        raise RuntimeError("Space did not return a local video path; adapter needed.")
    video = Path(result)
    if not video.is_file() or video.stat().st_size < 10000:
        raise RuntimeError("No valid video file returned; no upload performed.")

    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    youtube = build("youtube", "v3", credentials=creds)
    title = f"{topic} in seconds #Shorts"
    body = {
        "snippet": {
            "title": title[:100],
            "description": f"Learn about {topic}. AI-generated visuals; verify any technical concepts independently. #Transition2CS #Shorts #ComputerScience",
            "categoryId": "27",
        },
        "status": {
            "privacyStatus": os.getenv("YOUTUBE_PRIVACY", "private"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True),
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    print("YouTube upload ID:", response.get("id"))

if __name__ == "__main__":
    main()
