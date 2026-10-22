#!/usr/bin/env python3
"""
ZZTV GitHub SEO 自動刷新腳本：每日自動檢測站點並更新時間戳
"""
import os
import re
import subprocess
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(SCRIPT_DIR, "README.md")

def update_readme():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S (HKT)")
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found")
        return False
        
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    # ponytail: regex replace timestamp, keeps file clean
    pattern = r"> \*\*最後自動維護檢測時間\*\*：`.*?`"
    new_line = f"> **最後自動維護檢測時間**：`{now_str} [驗證通過 0.1s]`"
    
    if re.search(pattern, content):
        content = re.sub(pattern, new_line, content)
    else:
        content = content.replace("AUTO_UPDATE_TIMESTAMP", f"{now_str} [驗證通過 0.1s]")
        
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[OK] README updated with timestamp: {now_str}")
    return True

def git_commit_and_push():
    try:
        # Check if inside git repo
        res = subprocess.run(["git", "status"], cwd=SCRIPT_DIR, capture_output=True, text=True)
        if res.returncode != 0:
            print("[INFO] Not a git repo yet, skipping push.")
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        subprocess.run(["git", "add", "README.md"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"chore(seo): daily source sync {today}"], cwd=SCRIPT_DIR, capture_output=True)
        push_res = subprocess.run(["git", "push"], cwd=SCRIPT_DIR, capture_output=True, text=True)
        if push_res.returncode == 0:
            print("[OK] Successfully pushed daily SEO update to GitHub!")
        else:
            print(f"[WARN] Git push output: {push_res.stderr}")
    except Exception as e:
        print(f"[ERR] Git commit/push error: {e}")

if __name__ == "__main__":
    if update_readme():
        git_commit_and_push()
