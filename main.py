import os

log_path = "songs_log.txt"
music_dir = "./music_playlist"
included_extensions = ['mp3', 'wav', 'wave', 'flac', 'aac', 'm4a', 'alac']

# Get current list of music files
music_files = [fn for fn in os.listdir(music_dir)
               if fn.lower().split('.')[-1] in included_extensions]

# Read previous log (if exists)
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as file:
        logged_files = file.read().splitlines()
else:
    logged_files = []

# Find new files
new_files = list(set(music_files) - set(logged_files))

with open(log_path, "w", encoding="utf-8") as file:
    for mf in music_files:
        file.write(mf + "\n")

# Show results
if new_files:
    print("New files found:", new_files)
else:
    print("No new files added.")


# i need a list of my uploaded musics
# i need to check my music folder and compare it with my pervious list to see the new files added
# if yes then ==> send the music files with a caption to my channel
# if no ==> just print there is no new music in the folder
