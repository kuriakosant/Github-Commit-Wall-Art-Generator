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
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print("ERROR: Not a git repository. Run 'git init' first.")
        sys.exit(1)

def main():
    ensure_git_repo()
    cfg = load_config()
    msg = cfg.get("message", "HELLO")
    start = datetime.fromisoformat(cfg["start_date"])
    end = cfg.get("end_date")
    end_date = datetime.fromisoformat(end).date() if end else None
    commit_msg = cfg.get("commit_message", f"chore: commit wall art - {msg}")
    file_name = cfg.get("file_name", ".art.txt")
    font = cfg.get("font", "banner")

    # get author info
    author = cfg.get("author_name") or get_git_config("user.name")
    email = cfg.get("author_email") or get_git_config("user.email")
    if not author or not email:
        print("ERROR: set author_name/email in git config or config.json")
        sys.exit(1)

    # render ASCII art
    art = Figlet(font=font).renderText(msg).splitlines()
    width = max(len(line) for line in art)
    # pad/crop to 7 rows
    if len(art) < 7:
        pad = 7 - len(art)
        top = pad // 2
        art = [" " * width] * top + art + [" " * width] * (pad - top)
    elif len(art) > 7:
        art = art[:7]
    art = [line.ljust(width) for line in art]

    # align weeks to the Sunday on or before start_date
    dow = start.weekday()  # Mon=0..Sun=6
    sunday0 = start - timedelta(days=(dow + 1) % 7)
    print(f"Pattern origin Sunday: {sunday0.date()} (start requested {start.date()})")

    # ensure file exists
    open(file_name, "a").close()

    # create commits
    for col in range(width):
        for row in range(7):
            if art[row][col] != " ":
                d = sunday0 + timedelta(weeks=col, days=row)
                d_date = d.date()
                if d_date < start.date(): continue
                if end_date and d_date > end_date: continue

                # append to our art-file
                with open(file_name, "a") as f:
                    f.write(f"{d_date} • ({row},{col})\n")

                # build commit env
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
                subprocess.run(["git", "add", file_name], env=env)
                subprocess.run(["git", "commit", "-m", commit_msg], env=env)
                print(f"✔ commit @ {d_date}  (row {row}, col {col})")

if __name__ == "__main__":
    main() 