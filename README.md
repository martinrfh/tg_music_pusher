# Telegram Music Uploader 🎵🤖

This project is a **Python script** that automatically uploads music files from a local folder to your **Telegram channel** using the Telegram Bot API.

It's designed to save time and automate repetitive uploads. More features will be added in the future.

---

## 📌 Features

- ✅ Automatically finds and uploads new audio files
- ✅ Supports `.mp3`, `.flac`, `.m4a`, `.wav`, and more
- ✅ Extracts and uses metadata (title, artist)
- ✅ Tracks uploaded files using SQLite database
- ✅ Retries failed uploads with exponential backoff
- ✅ Built using `python-telegram-bot` (v22+) with async support
- ✅ Timeout handling for slow connections
- ✅ Automatic caption generation for uploads using AI

---

## 🔧 Setup

### 1. Clone the repo

```bash
git clone https://github.com/martinrfh/tg_music_pusher
cd your-repo
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your `.env` file

Create a file named `.env` in the root directory with the following content:

```
tg_bot_token=your_bot_token_here
chat_id=@your_channel_username
```

> 💡 Replace `@your_channel_username` with your channel's handle (your bot must be an **admin** in the channel).

### 4. Add music

Put your audio files in the `music_playlist/` folder.

### 5. Run the script

```bash
python main.py
```

---

## 📁 Folder Structure

```
project-root/
├── music_playlist/     # Your music files go here
├── songs_log.txt       # Keeps track of already uploaded files
├── main.py             # Main uploader script
├── .env                # Contains your bot token and chat ID
└── requirements.txt    # Python dependencies
```

---

## 🚧 Planned Features

- More metadata support
- Playlist upload scheduling
- Logging with timestamps and details

---

## 🤖 Bot Permissions

Make sure:

- Your bot is added to your channel
- Your bot has **admin** permission to send messages and media

## 🙌 Contributing

Pull requests and ideas are welcome. Just fork the repo and make your changes.

---
