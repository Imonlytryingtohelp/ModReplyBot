import requests
import threading
import time
import os
from datetime import datetime

UPDATE_CHECK_INTERVAL = 3600  # Check every hour
UPDATE_COOLDOWN = 86400  # Don't send mail more than once per 24 hours
LAST_UPDATE_FILE = os.path.join(os.path.dirname(__file__), 'DB', '.last_update_check.txt')


def get_latest_version(bot_name):
    """Fetch latest version info from update server."""
    try:
        response = requests.get(f'https://updts.slfhstd.uk/api/version/{bot_name}', timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[UPDATE_CHECKER] Error fetching version: {e}")
    return None


def send_update_modmail(reddit, subreddit_name, bot_name, current_version, available_version, changelog_url):
    """Send modmail to subreddit modteam about available update."""
    try:
        subject = f"🤖 {bot_name} Update Available (v{available_version})"
        message = f"""Hello,

An update is available for {bot_name}!

**Current Version:** {current_version}
**Available Version:** {available_version}

Changelog: {changelog_url}

Please visit the update server for installation instructions.

---
This is an automated message from the Update Checker."""
        data = {
            "subject": subject,
            "text": message,
            "to": f"/r/{subreddit_name}",
        }
        reddit.post("api/compose/", data=data)
        print(f"[UPDATE_CHECKER] Sent update notification to r/{subreddit_name}")
        return True
    except Exception as e:
        print(f"[UPDATE_CHECKER] Error sending modmail: {e}")
    return False


def should_send_update_mail():
    """Check if enough time has passed since last update mail."""
    if not os.path.exists(LAST_UPDATE_FILE):
        return True
    try:
        with open(LAST_UPDATE_FILE, 'r') as f:
            last_check = float(f.read().strip())
        return (time.time() - last_check) >= UPDATE_COOLDOWN
    except:
        return True


def mark_update_mailed():
    """Record when update mail was sent."""
    os.makedirs(os.path.dirname(LAST_UPDATE_FILE), exist_ok=True)
    with open(LAST_UPDATE_FILE, 'w') as f:
        f.write(str(time.time()))


def update_checker_thread(reddit, subreddit_name, bot_name, current_version):
    """Background thread that checks for updates periodically."""
    print(f"[UPDATE_CHECKER] Started for {bot_name} v{current_version}")
    while True:
        try:
            latest = get_latest_version(bot_name)
            if latest:
                available_version = latest.get('version')
                changelog_url = latest.get('changelog_url', '')
                if available_version and available_version != current_version:
                    if should_send_update_mail():
                        sent = send_update_modmail(
                            reddit, subreddit_name, bot_name, current_version, available_version, changelog_url
                        )
                        if sent:
                            mark_update_mailed()
            else:
                print(f"[UPDATE_CHECKER] No version info received.")
        except Exception as e:
            print(f"[UPDATE_CHECKER] Error in update checker thread: {e}")
        time.sleep(UPDATE_CHECK_INTERVAL)


def start_update_checker(reddit, subreddit_name, bot_name, current_version):
    threading.Thread(
        target=update_checker_thread,
        args=(reddit, subreddit_name, bot_name, current_version),
        daemon=True
    ).start()
