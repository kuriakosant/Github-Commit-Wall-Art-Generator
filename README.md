# GitHub Commit Wall Art Generator

Render text (or simple emojis) on your GitHub contributions graph by making back‐dated commits.

## Prerequisites

- Python 3.x  
- `pyfiglet` (install with `pip install pyfiglet`)

## Setup

1. Clone or create a new repo and enter it:
   ```bash
   git init
   ```

2. Copy these files into your repo root.

3. Install dependencies:
   ```bash
   pip install pyfiglet
   ```

4. Edit `config.json`:
   ```json
   {
     "message": "HELLO",
     "start_date": "2025-01-01",
     "end_date": "2025-04-20",
     "commit_message": "chore: commit wall art",
     "font": "banner",
     "file_name": ".art.txt"
   }
   ```

5. Run the generator:
   ```bash
   python3 generate.py
   ```

6. Push to GitHub:
   ```bash
   git remote add origin <your-repo-URL>
   git push -u origin main
   ```

7. View your profile to see the “HELLO” (or your custom message) on the commit heatmap!

---

### How It Works

- Uses **pyfiglet** to turn your `message` into a 7-line ASCII art grid.
- Aligns the first column to the Sunday on or before `start_date`.
- Creates one commit per “pixel” (non-space character) by setting `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` to that day at noon.
- Skips any commits outside your `[start_date, end_date]` window.

Enjoy your custom GitHub contribution art!  