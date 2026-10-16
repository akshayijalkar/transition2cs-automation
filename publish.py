"""Daily Transition2CS publisher; never posts without explicit upload gate."""
import os, pathlib, datetime, json, hashlib
from gradio_client import Client, handle_file
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOPICS = [
    ("What happens when you open a website?", "A vivid 3D visualization of packets traveling through a network router to a web server, glowing fiber optic lines, cinematic technical illustration, no text, vertical composition"),
    ("How cloud computing works", "Cinematic 3D visualization of cloud data centers and distributed servers exchanging glowing data packets, technical education video, no text, vertical composition"),
    ("What is cybersecurity?", "Cinematic blue cyber security shield protecting a stream of encrypted network packets from red malicious nodes, clean technical visual, no text, vertical composition"),
    ("How AI learns patterns", "Cinematic visualization of an artificial neural network lighting up as signals pass between connected neurons, beautiful technical animation, no text, vertical composition"),
    ("Inside a computer network", "Cinematic technical visualization of a local area network, glowing nodes, routers and switches communicating, blue highlights, no text, vertical composition")
]

def required(key):
    value = os.environ.get(key, '').strip()
    if not value:
        raise RuntimeError(f'Missing required setting: {key}')
    return value

def main():
    if os.environ.get('UPLOAD_ENABLED', '').lower() != 'true':
        print('UPLOAD_ENABLED is not true. No generation or upload attempted.'); return
    hf_space = required('HF_SPACE_ID')
    hf_token = required('HF_TOKEN')
    expected_channel = required('YOUTUBE_CHANNEL_ID')
    today = datetime.date.today()
    title, prompt = TOPICS[today.toordinal() % len(TOPICS)]
    client = Client(hf_space, token=hf_token)
    # A compatible Space must expose generate(prompt: str) -> file on /generate.
    result = client.predict(prompt=prompt, api_name='/generate')
    if isinstance(result, (list, tuple)):
        result = result[0]
    if isinstance(result, dict):
        result = result.get('video') or result.get('path')
    video_path = pathlib.Path(result)
    if not video_path.exists() or video_path.stat().st_size < 100_000:
        raise RuntimeError('No valid video returned from Hugging Face')
    credentials = Credentials(
        None,
        refresh_token=required('YOUTUBE_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=required('YOUTUBE_CLIENT_ID'),
        client_secret=required('YOUTUBE_CLIENT_SECRET'),
        scopes=['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']
    )
    credentials.refresh(Request())
    youtube = build('youtube', 'v3', credentials=credentials)
    mine = youtube.channels().list(part='id,snippet', mine=True).execute().get('items', [])
    if not mine or mine[0]['id'] != expected_channel:
        raise RuntimeError('Authorized channel does not match YOUTUBE_CHANNEL_ID: REFUSING upload.')
    body = {
        'snippet': {'title': title + ' | Transition2CS #Shorts',
                    'description': 'Visual AI-generated illustration of a computer science concept. #ComputerScience #AI #Shorts',
                    'categoryId': '28', 'tags': ['Computer Science', 'Transition2CS', 'AI']},
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': True}
    }
    request = youtube.videos().insert(part='snippet,status', body=body,
        media_body=MediaFileUpload(str(video_path), mimetype='video/mp4', resumable=True))
    response = None
    while response is None:
        _, response = request.next_chunk()
    print('Uploaded video ID:', response['id'])

if __name__ == '__main__':
    main()
