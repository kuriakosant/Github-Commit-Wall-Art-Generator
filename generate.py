#!/usr/bin/env python3
"""
Generate GitHub commit wall art by creating commits on specific dates based on ASCII art.
"""
import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pyfiglet import Figlet

def load_config():
    try:
        with open("config.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found. Create one (see README).")
        sys.exit(1)

def get_git_config(key):
    try:
        return subprocess.check_output(
            ["git", "config", "--get", key], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return None

def ensure_git_repo():
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        print("ERROR: Not a git repository. Run 'git init' first.")
        sys.exit(1)

def main():
    ensure_git_repo()
    cfg = load_config()
    msg = cfg.get("message", "HELLO")
    # Ensure start_date is correctly parsed from config
    start_date_str = cfg["start_date"]
    start = datetime.fromisoformat(start_date_str)
    
    end = cfg.get("end_date")
    end_date = datetime.fromisoformat(end).date() if end else None
    commit_msg = cfg.get("commit_message", f"chore: commit wall art - {msg}")
    file_name = cfg.get("file_name", ".art.txt")
    font = cfg.get("font", "banner") # Only used if not using manual_positions

    author = cfg.get("author_name") or get_git_config("user.name")
    email = cfg.get("author_email") or get_git_config("user.email")
    if not author or not email:
        print("ERROR: set author_name/email in git config or config.json")
        sys.exit(1)

    # align weeks to the Sunday on or before start_date
    dow = start.weekday()  # Mon=0..Sun=6
    sunday0 = start - timedelta(days=(dow + 1) % 7)
    print(f"Pattern origin Sunday: {sunday0.date()} (config start_date: {start.date()})")

    open(file_name, "a").close() # Ensure file exists

    commits_per_day = cfg.get("commits_per_day", 1)
    manual = cfg.get("manual_positions")

    if manual:
        print(f"Using manual_positions. Generating {commits_per_day} commit(s) per specified day.")
        for entry_idx, entry in enumerate(manual):
            cols = entry.get("cols") or [entry["col"]]
            start_seg_str = entry["start_date"]
            end_seg_str = entry["end_date"]
            start_seg = datetime.fromisoformat(start_seg_str).date()
            end_seg   = datetime.fromisoformat(end_seg_str).date()

            for col_idx, col in enumerate(cols):
                for row in range(7): # 0=Sunday, ..., 6=Saturday
                    d = sunday0 + timedelta(weeks=col, days=row)
                    d_date = d.date()

                    if d_date < start_seg or d_date > end_seg:
                        continue
                    
                    commit_time = datetime(d_date.year, d_date.month, d_date.day, 12, 0, 0) # Noon
                    date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S")
                    env = os.environ.copy()
                    env.update({
                        "GIT_AUTHOR_DATE":    date_str,
                        "GIT_COMMITTER_DATE": date_str,
                        "GIT_AUTHOR_NAME":    author,
                        "GIT_AUTHOR_EMAIL":   email,
                        "GIT_COMMITTER_NAME": author,
                        "GIT_COMMITTER_EMAIL": email,
                    })

                    for i in range(commits_per_day):
                        with open(file_name, "a") as f:
                            f.write(f"{d_date} • pos:({row},{col}) • commit #{i+1}/{commits_per_day} • entry {entry_idx}\n")
                        
                        subprocess.run(["git", "add", file_name], env=env, check=True)
                        try:
                            subprocess.run(["git", "commit", "-m", f"{commit_msg} ({d_date} P{i+1})"], env=env, check=True)
                        except subprocess.CalledProcessError as e:
                            print(f"ERROR during commit for {d_date} P{i+1}: {e}")
                            print("This might happen if there are no changes to commit (e.g., file was already committed with identical content).")
                            print("Check your .gitignore and ensure file_name is being modified uniquely.")


                    print(f"✔ {commits_per_day} commit(s) @ {d_date} (row {row}, col {col}) from manual entry {entry_idx}")
        print("Manual positions processed.")
        return

    # Fallback to Figlet ASCII art if manual_positions not used
    print(f"Using Figlet font '{font}' for message '{msg}'. Generating {commits_per_day} commit(s) per pixel.")
    art = Figlet(font=font).renderText(msg).splitlines()
    if not art:
        print(f"ERROR: Figlet could not render message '{msg}' with font '{font}'.")
        sys.exit(1)
        
    width = max(len(line) for line in art) if art else 0
    if len(art) < 7:
        pad = 7 - len(art)
        top = pad // 2
        art = [" " * width] * top + art + [" " * width] * (pad - top)
    elif len(art) > 7:
        art = art[:7]
    art = [line.ljust(width) for line in art]

    for col in range(width):
        for row in range(7):
            if art[row][col] != " ":
                d = sunday0 + timedelta(weeks=col, days=row)
                d_date = d.date()
                # Apply overall start_date and end_date from config if they exist
                if d_date < start.date(): continue
                if end_date and d_date > end_date: continue

                commit_time = datetime(d_date.year, d_date.month, d_date.day, 12, 0, 0)
                date_str = commit_time.strftime("%Y-%m-%d %H:%M:%S")
                env = os.environ.copy()
                env.update({
                    "GIT_AUTHOR_DATE": date_str,
                    "GIT_COMMITTER_DATE": date_str,
                    "GIT_AUTHOR_NAME": author,
                    "GIT_AUTHOR_EMAIL": email,
                    "GIT_COMMITTER_NAME": author,
                    "GIT_COMMITTER_EMAIL": email,
                })

                for i in range(commits_per_day):
                    with open(file_name, "a") as f:
                        f.write(f"{d_date} • art:({row},{col}) '{art[row][col]}' • commit #{i+1}/{commits_per_day}\n")
                    
                    subprocess.run(["git", "add", file_name], env=env, check=True)
                    try:
                        subprocess.run(["git", "commit", "-m", f"{commit_msg} ({d_date} P{i+1})"], env=env, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"ERROR during ASCII art commit for {d_date} P{i+1}: {e}")


                print(f"✔ {commits_per_day} commit(s) @ {d_date} (row {row}, col {col}) for char '{art[row][col]}'")
    print("Figlet art processed.")

if __name__ == "__main__":
    main() 