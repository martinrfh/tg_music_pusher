from dotenv import load_dotenv
from telegram import Bot
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import os
import asyncio

# Load environment variables
load_dotenv()
tg_bot_token = os.getenv("tg_bot_token")
CHAT_ID = '@deadbutterflly'

# Paths and settings
log_path = "songs_log.txt"
music_dir = "./music_playlist"
included_extensions = ['mp3', 'wav', 'wave', 'flac', 'aac', 'm4a', 'alac']


def get_new_files(directory, log_path, extensions):
    all_files = [
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f))
    ]

    extensions = [ext.lower() for ext in extensions]
    filtered = [
        f for f in all_files if f.lower().split('.')[-1] in extensions
    ]

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logged = f.read().splitlines()
    else:
        logged = []

    new_files = list(set(filtered) - set(logged))
    return new_files


def update_file_log(log_path, files):
    with open(log_path, "a", encoding="utf-8") as f:
        for file in files:
            f.write(file + "\n")


async def send_file(title, artist, file_path):
    bot = Bot(token=tg_bot_token)
    print(f"Sending: {file_path}")
    try:
        with open(file_path, "rb") as audio:
            await bot.send_audio(
                chat_id=CHAT_ID,
                audio=audio,
                title=title,
                performer=artist,
                caption='@deadbutterflly'
            )
    except Exception as e:
        print(f"[ERROR] Failed to send '{file_path}': {e}")


def get_audio_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=ID3)
        title = audio.tags.get("TIT2")
        artist = audio.tags.get("TPE1")
        return (
            title.text[0] if title else os.path.basename(file_path),
            artist.text[0] if artist else "Unknown Artist"
        )
    except Exception as e:
        print(f"[ERROR] Reading metadata: {file_path} → {e}")
        return os.path.basename(file_path), "Unknown Artist"


# === MAIN SCRIPT ===

new_files = get_new_files(music_dir, log_path, included_extensions)

if new_files:
    print("New music found:", new_files)

    for filename in new_files:
        file_path = os.path.join(music_dir, filename)
        title, artist = get_audio_metadata(file_path)
        asyncio.run(send_file(title, artist, file_path))

    update_file_log(log_path, new_files)
else:
    print("No new music files in the folder.")
