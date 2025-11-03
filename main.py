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

def fetch_playlist_tracks(playlist_id, access_token):
    """Fetch all tracks from a Spotify playlist."""
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('items', []):
                track = item.get('track')
                if track and track.get('name') and track.get('artists'):
                    track_info = {
                        'name': track.get('name', 'Unknown'),
                        'artists': [artist.get('name', 'Unknown') for artist in track.get('artists', [])],
                        'duration_ms': track.get('duration_ms', 0),
                        'album': track.get('album', {}).get('name', 'Unknown'),
                        'track_number': track.get('track_number', 0),
                        'disc_number': track.get('disc_number', 1)
                    }
                    tracks.append(track_info)
            
            url = data.get('next')  # Get next page URL
        else:
            print(f"Error fetching tracks: {response.status_code}")
            break
    
    return tracks

def create_m3u_from_spotify(playlist_dir, playlist_name, tracks):
    """Create an M3U playlist file from Spotify track data."""
    m3u_path = os.path.join(playlist_dir, f"{playlist_name}.m3u")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(m3u_path), exist_ok=True)
    
    with open(m3u_path, 'w', encoding='utf-8') as m3u_file:
        m3u_file.write("#EXTM3U\n")
        for track in tracks:
            # Format track info for M3U
            artists = ", ".join(track['artists'])
            duration_seconds = track['duration_ms'] // 1000
            
            # Write EXTINF line with duration and title
            m3u_file.write(f"#EXTINF:{duration_seconds},{artists} - {track['name']}\n")
            
            # Create filename that would be expected from spotdl
            filename = f"{artists} - {track['name']}.mp3"
            m3u_file.write(f"{filename}\n")
    
    return m3u_path

def scan_audio_files(playlist_dir):
    """Scan directory for audio files and return a list."""
    audio_extensions = ['.mp3', '.flac', '.m4a', '.wav', '.ogg', '.opus']
    audio_files = []
    
    if os.path.exists(playlist_dir):
        for file in os.listdir(playlist_dir):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(file)
    
    return sorted(audio_files)

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
    playlist_ids = []
    
    for playlist in playlists:
        name = playlist.get('name', 'N/A')
        description = playlist.get('description', '')
        tracks = playlist.get('tracks', {}).get('total', 0)
        link = playlist.get('external_urls', {}).get('spotify', '')
        playlist_id = playlist.get('id', '')
        
        print(f"Name: {name}")
        print(f"Description: {description}")
        print(f"Tracks: {tracks}")
        print(f"Link: {link}")
        print('-' * 40)
        
        if link and playlist_id:
            playlist_links.append(link)
            playlist_names.append(name)
            playlist_ids.append(playlist_id)
    
    # User selection for download mode
    if playlist_links:
        base_dir = os.path.join(os.getcwd(), 'playlists')
        m3u_files_dir = os.path.join(os.getcwd(), 'playlist files')
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(m3u_files_dir, exist_ok=True)
        parser = argparse.ArgumentParser(description="Spotify Bulk Playlist Downloader")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-all', action='store_true', help='Download ALL playlists')
        group.add_argument('-interactive', action='store_true', help='Go through one at a time (choose Y/N for each)')
        group.add_argument('-number', type=str, help='Download certain playlist(s) by number, comma separated (e.g. 1,3,5)')
        group.add_argument('-m3u-only', action='store_true', help='Only create .m3u files from Spotify data (no downloads)')
        group.add_argument('-m3u', action='store_true', help='Download playlists AND create .m3u files')
        args = parser.parse_args()
        
        if args.m3u_only:
            print("\nCreating .m3u files from Spotify playlist data...\n")
            m3u_created = 0
            for idx, name in enumerate(playlist_names):
                safe_name = ''.join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                
                print(f"Fetching tracks for: {name}")
                tracks = fetch_playlist_tracks(playlist_ids[idx], access_token)
                
                if tracks:
                    m3u_path = create_m3u_from_spotify(m3u_files_dir, safe_name, tracks)
                    print(f"Created .m3u file: {m3u_path} ({len(tracks)} tracks)")
                    m3u_created += 1
                else:
                    print(f"No tracks found for playlist: {name}")
            
            print(f"\nCompleted! Created {m3u_created} .m3u files.")
            exit(0)
        
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
            print("4. Create .m3u files only (from Spotify data, no downloads)")
            print("5. Download playlists AND create .m3u files")
            print("6. Create .m3u files only (select playlists)")
            mode = input("Enter 1, 2, 3, 4, 5, or 6: ").strip()
            if mode == '1':
                selected = list(range(len(playlist_links)))
                args.m3u = False
            elif mode == '2':
                selected = []
                for idx, name in enumerate(playlist_names):
                    yn = input(f"Download playlist '{name}'? (Y/N): ").strip().lower()
                    if yn == 'y':
                        selected.append(idx)
                args.m3u = False
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
                args.m3u = False
            elif mode == '4':
                print("\nCreating .m3u files from Spotify playlist data...\n")
                m3u_created = 0
                for idx, name in enumerate(playlist_names):
                    safe_name = ''.join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                    
                    print(f"Fetching tracks for: {name}")
                    tracks = fetch_playlist_tracks(playlist_ids[idx], access_token)
                    
                    if tracks:
                        m3u_path = create_m3u_from_spotify(m3u_files_dir, safe_name, tracks)
                        print(f"Created .m3u file: {m3u_path} ({len(tracks)} tracks)")
                        m3u_created += 1
                    else:
                        print(f"No tracks found for playlist: {name}")
                
                print(f"\nCompleted! Created {m3u_created} .m3u files.")
                exit(1)
            elif mode == '5':
                selected = list(range(len(playlist_links)))
                args.m3u = True
            elif mode == '6':
                print("Available playlists:")
                for idx, name in enumerate(playlist_names):
                    print(f"{idx+1}. {name}")
                nums = input("Enter playlist numbers to create .m3u files for (comma separated): ")
                selected = []
                for n in nums.split(','):
                    try:
                        i = int(n.strip()) - 1
                        if 0 <= i < len(playlist_links):
                            selected.append(i)
                    except ValueError:
                        pass
                print("\nCreating .m3u files from Spotify playlist data for selected playlists...\n")
                m3u_created = 0
                for idx in selected:
                    name = playlist_names[idx]
                    safe_name = ''.join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

                    print(f"Fetching tracks for: {name}")
                    tracks = fetch_playlist_tracks(playlist_ids[idx], access_token)

                    if tracks:
                        m3u_path = create_m3u_from_spotify(m3u_files_dir, safe_name, tracks)
                        print(f"Created .m3u file: {m3u_path} ({len(tracks)} tracks)")
                        m3u_created += 1
                    else:
                        print(f"No tracks found for playlist: {name}")

                print(f"\nCompleted! Created {m3u_created} .m3u files.")
                exit(0)
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
            
            # Create .m3u file if requested
            if hasattr(args, 'm3u') and args.m3u:
                audio_files = scan_audio_files(playlist_dir)
                if audio_files:
                    m3u_path = create_m3u_file(playlist_dir, safe_name, audio_files)
                    print(f"Created .m3u file: {m3u_path} ({len(audio_files)} tracks)")
            
            if bar:
                bar.update(1)
        if bar:
            bar.close()
else:
    print(f"Error: {response.status_code}")
    print(response.text)

def create_m3u_file(playlist_dir, playlist_name, audio_files):
    """Create an M3U playlist file for the downloaded audio files."""
    m3u_path = os.path.join(playlist_dir, f"{playlist_name}.m3u")
    
    with open(m3u_path, 'w', encoding='utf-8') as m3u_file:
        m3u_file.write("#EXTM3U\n")
        for audio_file in audio_files:
            # Get file info for EXTINF tag (duration, title)
            abs_path = os.path.join(playlist_dir, audio_file)
            if os.path.exists(abs_path):
                # For simplicity, we'll just write the filename
                # You could enhance this by reading ID3 tags
                m3u_file.write(f"{audio_file}\n")
    
    return m3u_path
