import os
import json
import re
import gdown
import requests
import tkinter as tk
from tkinter import messagebox, simpledialog

# ---------------- CONFIG ----------------
API_KEY = "Pc1DFIKlQj2-Pe5Mc4wbM6wR"
API_BASE_URL = "https://deathstruckapi.lol"
ALLOWED_EXTENSIONS = (".lua", ".manifest", ".text")
MAIN_FOLDER = "gamefolder"

# ---------------- API FUNCTIONS ----------------
def get_all_games_from_api() -> dict:
    """Get game data from API /devs endpoint"""
    try:
        url = f"{API_BASE_URL}/devs"
        params = {"key": API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[API ERROR] Failed to fetch from /devs: {response.status_code}")
            return {}
    except Exception as e:
        print(f"[API ERROR] Failed to get games from API: {e}")
        return {}

# ---------------- HELPERS ----------------
def extract_file_id(link: str) -> str:
    """Extract the file/folder ID from a Google Drive link"""
    if "/file/d/" in link:
        return link.split("/file/d/")[1].split("/")[0]
    if "id=" in link:
        return link.split("id=")[1].split("&")[0]
    return None

def download_link(link: str, main_folder: str):
    os.makedirs(main_folder, exist_ok=True)
    folder_id = extract_file_id(link)
    if not folder_id:
        print(f"[SKIP] Could not extract ID from {link}")
        return None

    folder_path = os.path.join(main_folder, folder_id)
    os.makedirs(folder_path, exist_ok=True)

    # Use gdown.download_folder for both files and folders
    try:
        gdown.download_folder(link, output=folder_path, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"[ERROR] Failed to download {link}: {e}")
        return None

    # Filter allowed extensions
    for root, _, files in os.walk(folder_path):
        for f in files:
            if not f.endswith(ALLOWED_EXTENSIONS):
                os.remove(os.path.join(root, f))

    # Check for at least one .lua
    lua_found = any(f.endswith(".lua") for _, _, files in os.walk(folder_path) for f in files)
    if not lua_found:
        print(f"[FAILED] No .lua file in folder {folder_path}")
        return None

    print(f"[SUCCESS] Folder ready: {folder_path}")
    return folder_path

# ---------------- GUI ----------------
def start_download():
    # Get games from API
    games_db = get_all_games_from_api()
    if not games_db:
        messagebox.showerror("Error", "No games found on API")
        return

    # Show available games and let user select
    game_list = list(games_db.keys())
    if not game_list:
        messagebox.showerror("Error", "No games available")
        return

    # Create selection dialog
    selected_games = []
    for game_name in game_list:
        result = messagebox.askyesno("Select Game", f"Download {game_name}?")
        if result:
            selected_games.append(game_name)

    if not selected_games:
        messagebox.showinfo("Info", "No games selected")
        return

    # Process selected games
    failed = []
    for i, game_name in enumerate(selected_games, 1):
        print(f"\n[{i}/{len(selected_games)}] Processing {game_name}")
        game_data = games_db[game_name]
        
        # Assuming the API returns a download link or folder data
        if isinstance(game_data, str) and game_data.startswith("http"):
            # It's a direct link
            folder_path = download_link(game_data, MAIN_FOLDER)
            if not folder_path:
                failed.append(game_name)
        else:
            # It's game data, create folder and save
            folder_path = os.path.join(MAIN_FOLDER, game_name.replace(" ", "_"))
            os.makedirs(folder_path, exist_ok=True)
            
            # Save game data as JSON
            with open(os.path.join(folder_path, "game_data.json"), "w") as f:
                json.dump(game_data, f, indent=2)
            
            print(f"[SUCCESS] Game data saved: {folder_path}")

    messagebox.showinfo("Done", f"Finished processing {len(selected_games)} games.\nFailed: {len(failed)}")
    if failed:
        print("Failed games:\n" + "\n".join(failed))

# ---------------- MAIN WINDOW ----------------
root = tk.Tk()
root.title("Game Downloader")
root.geometry("400x200")

label = tk.Label(root, text="Download games from Google Drive links", font=("Arial", 12))
label.pack(pady=20)

btn = tk.Button(root, text="Start Download", command=start_download, width=20, height=2)
btn.pack(pady=20)

root.mainloop()


