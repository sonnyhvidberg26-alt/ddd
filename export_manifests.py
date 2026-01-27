import os
import json
import re
import gdown
import tkinter as tk
from tkinter import messagebox, simpledialog

# ---------------- CONFIG ----------------
DB_FILE = "Ourgames.json"
ALLOWED_EXTENSIONS = (".lua", ".manifest", ".text")
MAIN_FOLDER = "gamefolder"

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

    if not os.path.exists(DB_FILE):
        messagebox.showerror("Error", f"{DB_FILE} not found.")
        return

    with open(DB_FILE, "r", encoding="utf-8") as f:
        games_db = json.load(f)

    links = list(games_db.values())[:num_games]

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
