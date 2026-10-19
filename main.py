import os
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from mutagen import File
from openai import OpenAI
from telegram.ext import Application
from telegram.request import HTTPXRequest


# === Configuration ===
load_dotenv()
BOT_TOKEN = os.getenv("tg_bot_token")
AI_TOKEN = os.getenv("openai_token")
CHAT_ID = os.getenv("chat_id")
BASE_DIR = Path(__file__).resolve().parent
MUSIC_DIR = BASE_DIR / "music_playlist"


DATABASE_NAME = "my_playlist.db"
SUPPORTED_EXTENSIONS = ['.mp3', '.wav',
                        '.wave', '.flac', '.aac', '.m4a', '.alac']
MAX_RETRIES = 3
TIMEOUT = 600  # 10 minutes timeout

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
)


def initialize_database(database_name):
    try:
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_songs (
            artist TEXT NOT NULL,
            song TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT,
            UNIQUE(artist, song)
        );
        """)

        conn.commit()
        return conn, cursor

    except Exception as e:
        print(f"[!] Error initializing database: {e}")
        return None, None


connection, cursor = initialize_database(DATABASE_NAME)


def add_song_to_playlist(title, artist, file_path):
    now = datetime.now()
    uploaded_at = now.strftime("%Y-%m-%d")
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO playlist_songs (artist, song, file_path, uploaded_at) VALUES (?, ?, ?, ?)",
            (artist, title, file_path, uploaded_at)
        )
        connection.commit()
    except Exception as e:
        print(f"[!] Error adding song '{title} — {artist}': {e}")


def get_audio_metadata(file_path):
    try:
        audio = File(file_path, easy=True)
        if audio is None:
            print(f"❌ Unsupported or unreadable file: {file_path}")
            return os.path.basename(file_path), "Unknown Artist"

        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]

        if not title:
            title = os.path.basename(file_path)
        if not artist:
            artist = "Unknown Artist"

        return title, artist

    except Exception as e:
        print(f"❌ Error reading metadata for {file_path}: {e}")
        return os.path.basename(file_path), "Unknown Artist"


def generate_caption(artist_name, song_name):
    prompt = f"""
        You are formatting text for a Telegram post.

        TASK:
        Analyze the song "{song_name}" by "{artist_name}".

        Choose ONE option only:

        OPTION A:
        Return exactly 4 verbatim lyric lines from the song.

        OPTION B:
        If suitable lyrics cannot be confidently provided OR the lyrics are not emotionally meaningful,
        write exactly 4 original poetic lines inspired by the song.

        OUTPUT FORMAT:

        FOR LYRICS:
        <b>"Line 1...
        Line 2...
        Line 3...
        Line 4..." 😔</b>

        <b>#genre1 #genre2 🖤
        🎧 — @deadbutterflly</b>

        FOR POETRY:
        <b>"Poetic line 1...
        Poetic line 2...
        Poetic line 3...
        Poetic line 4..." 🌙</b>

        <b>#genre1 #genre2 🖤
        🎧 — @deadbutterflly</b>

        STRICT RULES:

        - Output ONLY the final formatted text.
        - No explanations.
        - No introductions.
        - No notes.
        - No markdown.
        - Use ONLY HTML <b> tags.
        - Do NOT add any spaces or blank lines immediately before or after the lyric/poetry text inside the quotation marks.
        - The first character inside the opening quotation mark must be the first character of the lyric or poetic line.
        - The last character of the final lyric or poetic line must be immediately followed by the closing quotation mark.
        - Never output more than 4 lyric lines.
        - Never output more than 2 poetry lines.
        - Never output fewer than the required number of lines.
        - Put exactly ONE emoji after the closing quote.
        - Do NOT add blank lines inside the quote.
        - Use exactly TWO genre hashtags.
        - Genres must be lowercase hashtags.
        - If a genre contains multiple words, join them with an underscore.
        - Examples: #progressive_rock #heavy_metal
        - Never use spaces inside a genre hashtag.
        - Never use more or fewer than TWO genre hashtags.
        - If using lyrics, they must be verbatim.
        - If you are not confident about the lyrics, use OPTION B instead.
        - Never mix lyrics and poetry.
        - Do not add any text before or after the required formatted output.
        """

    import time
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            completion = client.chat.completions.create(
                model="z-ai/glm-5.3-flash",
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                extra_body={"reasoning": {"enabled": True}}
            )
            generated_caption = completion.choices[0].message.content
            return generated_caption

        except Exception as e:
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            if code == 429 and attempt < max_attempts - 1:
                wait = 2 ** attempt
                print(f"⏳ Rate-limited (429), retrying in {wait}s...")
                time.sleep(wait)
                continue
            print(e)
            return None


async def send_file(app, title, artist, file_path, retries=0):
    print(f"📤 Generating caption for: {title} — {artist}")
    caption = generate_caption(artist, title)

    if not caption or caption.strip() == "":
        print(
            f"❌ Caption generation failed for '{title}' — '{artist}'. Stopping upload process.")
        return None

    print(f"📤 Uploading: {title} — {artist}")

    while retries < MAX_RETRIES:
        try:
            with open(file_path, "rb") as audio:
                await app.bot.send_audio(
                    chat_id=CHAT_ID,
                    audio=audio,
                    title=title,
                    performer=artist,
                    caption=caption,
                    parse_mode="HTML",
                    read_timeout=TIMEOUT,
                    write_timeout=TIMEOUT,
                    connect_timeout=TIMEOUT,
                )
            print(f"✅ Successfully uploaded: {title} — {artist}")
            return True

        except Exception as e:
            print(
                f"❌ Failed to upload {title} — {artist} (Attempt {retries + 1}/{MAX_RETRIES}): {str(e)}")
            retries += 1
            await asyncio.sleep(2 ** retries)

    print(
        f"🚫 Giving up on {title} — {artist} after {MAX_RETRIES} attempts.")
    return False


def has_been_uploaded(title, artist):
    cursor.execute(
        "SELECT song, artist FROM playlist_songs WHERE song = ? AND artist = ?", (title, artist))
    result = cursor.fetchone()
    return bool(result)


# === MAIN SCRIPT ===
async def main():
    print("🎵 Starting music upload process...")

    if not MUSIC_DIR.is_dir():
        print(f"❌ Music folder not found: {MUSIC_DIR}")
        return

    audio_files = [
        f for f in MUSIC_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    # Use a context manager to handle the bot's lifecycle:
    # context manager : which are Python objects that need to do something before and after a block of code.
    async with Application.builder().token(BOT_TOKEN).build() as app:
        if not audio_files:
            print("📂 No music files found in the folder")
            return

        new_files = []
        for file_path in audio_files:
            file_path = str(file_path)
            title, artist = get_audio_metadata(file_path)
            if not has_been_uploaded(title, artist):
                new_files.append((file_path, title, artist))

        print(f"📁 Found {len(new_files)} new file(s) to upload")

        for file_path, title, artist in new_files:
            result = await send_file(app, title, artist, file_path)
            if result is None:
                print("🛑 Upload process stopped due to caption generation failure.")
                break
            if result:
                add_song_to_playlist(title, artist, file_path)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        connection.close()
