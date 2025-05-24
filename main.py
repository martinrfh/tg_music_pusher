from dotenv import load_dotenv
from telegram import Bot
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import os
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("tg_bot_token")
CHAT_ID = os.getenv("chat_id")

# Paths and settings
LOG_FILE = "songs_log.txt"
MUSIC_DIR = "./music_playlist"
SUPPORTED_EXTENSIONS = ['mp3', 'wav', 'wave', 'flac', 'aac', 'm4a', 'alac']


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
    bot = Bot(token=BOT_TOKEN)
    print(f"📤 Uploading: {os.path.basename(file_path)}")
    try:
        with open(file_path, "rb") as audio:
            await bot.send_audio(
                chat_id=CHAT_ID,
                audio=audio,
                title=title,
                performer=artist,
                caption='@deadbutterflly'
            )
        print(f"✅ Successfully uploaded: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"❌ Failed to upload {os.path.basename(file_path)}: {str(e)}")
        return False


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
        print(
            f"❌ Error reading metadata for {os.path.basename(file_path)}: {e}")
        return os.path.basename(file_path), "Unknown Artist"


# === MAIN SCRIPT ===
print("🎵 Starting music upload process...")

new_files = get_new_files(MUSIC_DIR, LOG_FILE, SUPPORTED_EXTENSIONS)

if new_files:
    print(f"📁 Found {len(new_files)} new files to process")
    uploaded_files = []

    for file in new_files:
        file_path = os.path.join(MUSIC_DIR, file)
        title, artist = get_audio_metadata(file_path)

        if asyncio.run(send_file(title, artist, file_path)):
            uploaded_files.append(file)
        else:
            print(f"⚠️ Skipping {file} due to upload failure")

    if uploaded_files:
        update_file_log(LOG_FILE, uploaded_files)
        print(
            f"✅ Upload complete: {len(uploaded_files)} files uploaded successfully")
    else:
        print("❌ No files were successfully uploaded")
else:
    print("📂 No new music files found in the folder")
