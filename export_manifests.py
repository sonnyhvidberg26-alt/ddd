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
def get_game_link_api(steamid: str) -> str:
    """Get game download link from gamegen.lol API"""
    try:
        url = f"{API_BASE_URL}/lua/{steamid}"
        params = {"key": API_KEY}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return f"{url}?key={API_KEY}"
        return None
    except Exception as e:
        print(f"[API ERROR] Failed to get game link {steamid}: {e}")
        return None

def get_all_games_from_api(steamids: list) -> dict:
    """Get game links for multiple Steam IDs from API"""
    games = {}
    for steamid in steamids:
        link = get_game_link_api(steamid)
        if link:
            games[steamid] = link
    return games

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
    try:
        num_games = int(simpledialog.askstring("Input", "How many games do you want to process?"))
        if num_games <= 0:
            raise ValueError
    except Exception:
        messagebox.showerror("Error", "Invalid number")
        return

    # Get Steam IDs from user (comma-separated)
    try:
        steamids_input = simpledialog.askstring("Steam IDs", "Enter Steam App IDs (comma-separated):")
        if not steamids_input:
            messagebox.showerror("Error", "No Steam IDs provided")
            return
        
        steamids = [sid.strip() for sid in steamids_input.split(",")][:num_games]
        if len(steamids) == 0:
            messagebox.showerror("Error", "Invalid Steam IDs")
            return
    except Exception:
        messagebox.showerror("Error", "Failed to parse Steam IDs")
        return

    # Get games from API
    games_db = get_all_games_from_api(steamids)
    if not games_db:
        messagebox.showerror("Error", "No games found on API")
        return

    links = list(games_db.values())

    failed = []
    for i, link in enumerate(links, 1):
        print(f"\n[{i}/{num_games}] Processing {link}")
        folder_path = download_link(link, MAIN_FOLDER)
        if not folder_path:
            failed.append(link)

    messagebox.showinfo("Done", f"Finished processing {num_games} games.\nFailed: {len(failed)}")
    if failed:
        print("Failed links:\n" + "\n".join(failed))

# ---------------- MAIN WINDOW ----------------
root = tk.Tk()
root.title("Game Downloader")
root.geometry("400x200")

label = tk.Label(root, text="Download games from Google Drive links", font=("Arial", 12))
label.pack(pady=20)

btn = tk.Button(root, text="Start Download", command=start_download, width=20, height=2)
btn.pack(pady=20)

root.mainloop()


