import subprocess
import sys
from datetime import datetime

def sync():
    date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        # Check if remote exists
        remotes = subprocess.run(["git", "remote"], capture_output=True, text=True).stdout.strip()
        if not remotes:
            print("No git remote configured. Skipping push.")
            return True
        
        # Add changes
        subprocess.run(["git", "add", "."], check=True)
        # Commit
        subprocess.run(["git", "commit", "-m", f"chore(brief): update daily intelligence for {date_str}"], check=False)
        # Push
        result = subprocess.run(["git", "push"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully pushed latest briefing to GitHub Pages.")
            return True
        else:
            print(f"Git push warning: {result.stderr}")
            return False
    except Exception as e:
        print(f"Sync error: {e}")
        return False

if __name__ == "__main__":
    sync()
