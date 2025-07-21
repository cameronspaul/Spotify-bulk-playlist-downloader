import requests
import base64
import os
from dotenv import load_dotenv
import subprocess
from time import sleep
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
import argparse

# Load environment variables from .env file
load_dotenv()
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_access_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Failed to get token:", response.status_code, response.text)
        return None

access_token = get_access_token(client_id, client_secret)
if not access_token:
    exit(1)

#username = input("Enter your Spotify username: ")

# Spotify API endpoint and access token
#url = f"https://api.spotify.com/v1/users/{username}/playlists"
url = "https://api.spotify.com/v1/users/0388zbvwivve5cds878699i85/playlists"
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    playlists = data.get('items', [])
    print(f"Found {len(playlists)} playlists:\n")
    playlist_links = []
    playlist_names = []
    for playlist in playlists:
        name = playlist.get('name', 'N/A')
        description = playlist.get('description', '')
        tracks = playlist.get('tracks', {}).get('total', 0)
        link = playlist.get('external_urls', {}).get('spotify', '')
        print(f"Name: {name}")
        print(f"Description: {description}")
        print(f"Tracks: {tracks}")
        print(f"Link: {link}")
        print('-' * 40)
        if link:
            playlist_links.append(link)
            playlist_names.append(name)
    # User selection for download mode
    if playlist_links:
        base_dir = os.path.join(os.getcwd(), 'playlists')
        os.makedirs(base_dir, exist_ok=True)
        parser = argparse.ArgumentParser(description="Spotify Bulk Playlist Downloader")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-all', action='store_true', help='Download ALL playlists')
        group.add_argument('-interactive', action='store_true', help='Go through one at a time (choose Y/N for each)')
        group.add_argument('-number', type=str, help='Download certain playlist(s) by number, comma separated (e.g. 1,3,5)')
        args = parser.parse_args()
        if args.all:
            selected = list(range(len(playlist_links)))
        elif args.interactive:
            selected = []
            for idx, name in enumerate(playlist_names):
                yn = input(f"Download playlist '{name}'? (Y/N): ").strip().lower()
                if yn == 'y':
                    selected.append(idx)
        elif args.number:
            nums = args.number
            selected = []
            for n in nums.split(','):
                try:
                    i = int(n.strip()) - 1
                    if 0 <= i < len(playlist_links):
                        selected.append(i)
                except ValueError:
                    pass
        else:
            # Fallback to interactive prompt if no args
            print(f"\nLoaded {len(playlist_links)} playlists.")
            print("Choose download mode:")
            print("1. Download ALL playlists")
            print("2. Go through one at a time (choose Y/N for each)")
            print("3. Download a certain playlist by number")
            mode = input("Enter 1, 2, or 3: ").strip()
            if mode == '1':
                selected = list(range(len(playlist_links)))
            elif mode == '2':
                selected = []
                for idx, name in enumerate(playlist_names):
                    yn = input(f"Download playlist '{name}'? (Y/N): ").strip().lower()
                    if yn == 'y':
                        selected.append(idx)
            elif mode == '3':
                print("Available playlists:")
                for idx, name in enumerate(playlist_names):
                    print(f"{idx+1}. {name}")
                nums = input("Enter playlist numbers to download (comma separated): ")
                selected = []
                for n in nums.split(','):
                    try:
                        i = int(n.strip()) - 1
                        if 0 <= i < len(playlist_links):
                            selected.append(i)
                    except ValueError:
                        pass
            else:
                print("Invalid mode. Exiting.")
                exit(1)
        print("\nStarting download of selected playlists with spotdl...\n")
        total = len(selected)
        bar = tqdm(total=total, desc="Playlists", unit="playlist") if tqdm else None
        for idx in selected:
            pl_link = playlist_links[idx]
            pl_name = playlist_names[idx]
            safe_name = ''.join(c for c in pl_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            playlist_dir = os.path.join(base_dir, safe_name)
            os.makedirs(playlist_dir, exist_ok=True)
            print(f"\nDownloading: {pl_link} into {playlist_dir}")
            # Use subprocess to stream output line by line
            process = subprocess.Popen([
                'spotdl', 'download', pl_link, '--output', os.path.join(playlist_dir, '{artists} - {title}.{output-ext}')
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                print(line, end='')
                # Check for rate limit warning and sleep if needed
                if 'rate/request limit' in line:
                    import re
                    match = re.search(r'after: (\\d+)', line)
                    if match:
                        wait_time = int(match.group(1))
                        print(f"Rate limit hit, waiting {wait_time} seconds...")
                        sleep(wait_time)
            process.wait()
            if process.returncode != 0:
                print(f"spotdl exited with code {process.returncode}")
            if bar:
                bar.update(1)
        if bar:
            bar.close()
else:
    print(f"Error: {response.status_code}")
    print(response.text)
