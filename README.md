# Spotify Bulk Playlist Downloader

> **Downloaded MP3 files include metadata such as song title, artist, album, and cover art (where available).**
> The script uses [spotDL](https://github.com/spotDL/spotify-downloader), which automatically tags downloaded files with this information.

This project allows you to fetch and list all playlists for a given Spotify user using the Spotify Web API. It uses the Client Credentials flow for authentication.

## Features
- Authenticate with Spotify using Client Credentials
- Fetch and display playlists for a specified user

## Setup

### 1. Clone the repository
```sh
git clone https://github.com/yourusername/spotify-bulk-playlist-downloader.git
cd spotify-bulk-playlist-downloader
```

### 2. Create a Spotify App
- Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
- Create a new app to get your `Client ID` and `Client Secret`

### 3. Configure Environment Variables
Create a `.env` file in the project root with the following content:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

Replace `your_client_id_here` and `your_client_secret_here` with your actual credentials.

### 4. Install Dependencies
```sh
pip install -r requirements.txt
```

### 5. Run the Script
```sh
python main.py
```

## Bulk Playlist Downloading

When you run the script, it will:
- List all playlists for the specified Spotify user.
- Prompt you to choose a download mode:
  1. **Download ALL playlists**
  2. **Go through one at a time** (choose Y/N for each playlist)
  3. **Download a certain playlist by number**
- Downloaded playlists are saved in a `playlists` folder, with each playlist in its own subfolder named after the playlist.
- The script uses [spotDL](https://github.com/spotDL/spotify-downloader) to download the tracks.
- A progress bar and live logs are shown for each playlist download. If a Spotify rate limit is hit, the script will automatically wait and retry.

## Command-Line Usage

You can now use command-line arguments to control the download mode directly:

- Download all playlists:
  ```sh
  python main.py -all
  ```
- Interactive mode (choose Y/N for each playlist):
  ```sh
  python main.py -interactive
  ```
- Download specific playlists by number (comma separated):
  ```sh
  python main.py -number 1,3,5
  ```

If you run without arguments, the script will prompt you to choose a mode interactively as before.

## Downloaded Files & Metadata
- Downloaded MP3 files include metadata such as song title, artist, album, and cover art (where available). The script uses [spotDL](https://github.com/spotDL/spotify-downloader), which automatically tags downloaded files with this information.

## Limitations & Important Notes
- **Only public playlists are supported.** This script uses the Spotify Client Credentials flow, which does **not** provide access to private playlists or user-specific data. Only playlists that are public and visible to everyone can be fetched and downloaded.
- For personal/private playlists, you need to implement the Authorization Code flow (not included in this project).
- The script does not download playlists that are marked as private or collaborative unless they are also public.

## License
MIT
