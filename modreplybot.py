import os
import praw
from config import get_reddit, Config
from update_checker import start_update_checker

BOT_VERSION = "2.3.1"  # Change this for new releases
BOT_NAME = "ModReplyBot"  # Change this if bot name changes

import time

class ModReplyBot:
    def chat_message_watcher(self):
        chat_requests_file = os.path.join(os.path.dirname(__file__), 'DB', 'chat_wiki_requests.txt')
        processed_message_ids = set()
        # Load processed IDs from file
        if os.path.exists(chat_requests_file):
            with open(chat_requests_file, 'r', encoding='utf-8') as f:
                for line in f:
                    processed_message_ids.add(line.strip())
        while True:
            try:
                for message in self.reddit.inbox.stream():
                    if not hasattr(message, 'id') or message.id in processed_message_ids:
                        continue
                    processed_message_ids.add(message.id)
                    # Save processed ID to file
                    with open(chat_requests_file, 'a', encoding='utf-8') as f:
                        f.write(message.id + '\n')
                    if hasattr(message, 'body'):
                        command_parts = message.body.strip().split()
                        command = command_parts[0].lower() if command_parts else ''
                        author = getattr(message, 'author', None)
                        if not author or author not in self.subreddit.moderator():
                            continue

                        if command == 'reload-config' or 'reload-config' in message.body.lower():
                            print(f"[CHAT WATCH] Moderator '{author}' requested config reload.")
                            result = self.fetch_yaml_config()
                            if result:
                                print("[CHAT WATCH] Wiki config reloaded successfully.")
                                reply_text = "Config reloaded successfully. Config is valid."
                            else:
                                print("[CHAT WATCH] Wiki config reload failed.")
                                reply_text = "Config reload failed. Config is invalid."
                        elif command == 'delete-fc':
                            if len(command_parts) != 2:
                                reply_text = "Usage: delete-fc <post-id>"
                            else:
                                reply_text = self.delete_filtered_comment(command_parts[1])
                        elif command == 'delete-all':
                            if len(command_parts) != 2:
                                reply_text = "Usage: delete-all <post-id>"
                            else:
                                reply_text = self.delete_all_bot_comments(command_parts[1])
                        else:
                            continue

                        try:
                            message.reply(reply_text)
                            print(f"[CHAT WATCH] Replied to chat message {message.id}.")
                        except Exception as e:
                            print(f"[CHAT WATCH] Error replying to chat message {message.id}: {e}")
            except Exception as e:
                print(f"Chat message watcher error: {e}")
            import time
            time.sleep(30)
    def comment_only(self, submission, comment_text, matched_tag=None):
        try:
            # Replace template variables
            comment_text = comment_text.replace("{{author}}", submission.author.name if submission.author else "unknown")
            comment_text = comment_text.replace("{author}", submission.author.name if submission.author else "unknown")
            
            # Check required text and prepend message if needed
            if matched_tag and matched_tag in self.tag_required_text:
                comment_text = self.check_required_text_and_prepend_message(
                    submission, comment_text, self.tag_required_text[matched_tag], matched_tag
                )
            
            comment = submission.reply(comment_text)
            self.save_bot_comment(comment.id)
            comment.mod.distinguish(sticky=True)
            print(f"Commented (no approval) on: {submission.id}")
            self.save_commented_post(submission.id)
        except Exception as e:
            print(f"Error commenting (no approval): {e}")
    def __init__(self):
        import os
        import threading
        self.reddit = get_reddit()
        self.subreddit = self.reddit.subreddit(Config.SUBREDDIT)
        self.config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        self.triggers = []
        self.comments = []
        self.statuses = []
        self.flair_ids = []
        self.stickied = []
        self.lock_post = []
        self.lock_comment = []
        self.trigger_required_text = []
        self.tag_comments = {}
        self.tag_statuses = {}
        self.tag_flair_ids = {}
        self.tag_required_text = {}
        self.filtered_post_comment = ''
        self.commented_posts = set()
        self.commented_posts_file = os.path.join(os.path.dirname(__file__), 'DB', 'commented_posts.txt')
        self.filtered_commented_posts = set()
        self.filtered_commented_posts_file = os.path.join(os.path.dirname(__file__), 'DB', 'filtered_commented_posts.txt')
        self.bot_comments = set()
        self.bot_comments_file = os.path.join(os.path.dirname(__file__), 'DB', 'bot_comments.txt')
        self.bot_comments_lock = threading.RLock()
        self.tagged_commented_posts_file = os.path.join(os.path.dirname(__file__), 'DB', 'tagged_commented_posts.txt')
        self.tagged_commented_posts = set()
        self._wiki_config_cache = None
        self._wiki_config_cache_time = 0
        self._wiki_config_cache_ttl = 300  # seconds (5 minutes)
        self.ensure_config_file()
        self.load_commented_posts()
        self.load_filtered_commented_posts()
        self.load_bot_comments()
        self.log_level = Config.LOG_LEVEL

    def log(self, message, debug_only=False):
        if self.log_level == 'Debug' or (self.log_level == 'Default' and not debug_only):
            print(message)

    def check_required_text_and_prepend_message(self, submission, comment_text, required_text_list, matched_tag=None):
        """Check if post contains required text strings, prepend message if not."""
        if not required_text_list:
            return comment_text
        
        # Get post content based on search_in
        title = submission.title.lower()
        body = getattr(submission, 'selftext', '').lower()
        title_and_body = title + ' ' + body
        
        print(f"[DEBUG] Checking required_text for tag '{matched_tag}', title='{title}', body='{body}'")
        
        for req_entry in required_text_list:
            req_tag = req_entry.get('tag', '').strip().lower()
            print(f"[DEBUG] Checking req_entry with tag '{req_tag}'")
            if req_tag and matched_tag and req_tag != matched_tag.lower():
                print(f"[DEBUG] Skipping req_entry, tag mismatch")
                continue  # This required_text is for a different tag
            
            text_list = req_entry.get('text', '').split(',')
            def normalize_req_text(item):
                item = item.strip()
                # Remove surrounding quotes (single or double) for exact phrases
                if (item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'")):
                    item = item[1:-1]
                return item.strip().lower()
            text_list = [normalize_req_text(t) for t in text_list if t.strip()]
            print(f"[DEBUG] Required text_list: {text_list}")
            
            search_in = req_entry.get('search_in', 'title_and_body').lower()
            if search_in == 'title':
                content = title
            elif search_in == 'body':
                content = body
            else:  # title_and_body
                content = title_and_body
            
            print(f"[DEBUG] Searching in '{search_in}', content='{content}'")
            
            # Check if any required text is present
            found = False
            for req_text in text_list:
                if req_text in content:
                    print(f"[DEBUG] Found required text '{req_text}' in content")
                    found = True
                    break
            
            if not found:
                print(f"[DEBUG] Required text not found, prepending message")
                # Prepend the message
                message = req_entry.get('message', '').strip()
                if message:
                    comment_text = message + '\n\n' + comment_text
            else:
                print(f"[DEBUG] Required text found, not prepending message")
        
        return comment_text

    def ensure_config_file(self):
        import os
        if not os.path.exists(self.config_path):
            default_yaml = (
                'triggers:\n'
                '  - trigger: help\n'
                '    comment: |\n'
                '      Thank you for your report!\n'
                '      This post is now approved.\n'
                '  - trigger: question\n'
                '    comment: |\n'
                '      This post has been approved.\n'
                '      Your question will be answered soon.\n'
            )
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(default_yaml)

    def fetch_yaml_config(self):
        # Track last error revision to prevent modmail spam
        if not hasattr(self, '_last_config_error_revision'):
            self._last_config_error_revision = None
        import yaml, time
        now = time.time()
        # Use cache if not expired
        if self._wiki_config_cache and (now - self._wiki_config_cache_time < self._wiki_config_cache_ttl):
            config = self._wiki_config_cache
            self._wiki_revision_id = getattr(self, '_wiki_revision_id', None)
        else:
            try:
                wiki_page = Config.WIKI_PAGE
                wiki = self.subreddit.wiki[wiki_page]
                wiki_content = wiki.content_md
                self._wiki_revision_id = getattr(wiki, 'revision_id', None)
                config = yaml.safe_load(wiki_content)
                self._wiki_config_cache = config
                self._wiki_config_cache_time = now
            except Exception as e:
                self.log(f"Error fetching YAML config from wiki: {e}")
                revision = getattr(self, '_wiki_revision_id', None)
                if revision != self._last_config_error_revision:
                    self._last_config_error_revision = revision
                return False
        if not isinstance(config, dict) or 'triggers' not in config:
            self.log("Wiki config missing required 'triggers' key or is not a dict.")
            return False
        self.triggers = []
        self.comments = []
        self.statuses = []
        self.flair_ids = []
        self.stickied = []
        self.lock_post = []
        self.lock_comment = []
        self.trigger_required_text = []
        self.tag_comments = {}
        self.tag_statuses = {}
        self.tag_flair_ids = {}
        self.tag_required_text = {}
        self.filtered_post_comment = config.get('filtered_post_comment', '') or ''
        if not isinstance(self.filtered_post_comment, str):
            self.log("Wiki config 'filtered_post_comment' must be a string.")
            return False
        self.filtered_post_comment = self.filtered_post_comment.strip()
        for entry in config.get('triggers', []):
            self.triggers.append(entry.get('trigger', '').strip())
            self.comments.append(entry.get('comment', '').strip())
            self.statuses.append(entry.get('status', 'enabled').strip().lower())
            self.flair_ids.append(entry.get('flair_id', '').strip())
            self.stickied.append(bool(entry.get('stickied', False)))
            # Parse lock_post as a proper boolean
            lock_post_val = entry.get('lock_post', False)
            if isinstance(lock_post_val, str):
                lock_post_val = lock_post_val.lower() in ['true', '1', 'yes']
            self.lock_post.append(bool(lock_post_val))
            self.lock_comment.append(bool(entry.get('lock_comment', False)))
            self.trigger_required_text.append(entry.get('required_text', []))
        for entry in config.get('post_tags', []):
            tags_str = entry.get('tag', '').strip()
            comment = entry.get('comment', '').strip()
            status = entry.get('status', 'enabled').strip().lower()
            flair_id = entry.get('flair_id', '').strip()
            required_text = entry.get('required_text', [])
            tags = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
            for tag in tags:
                self.tag_comments[tag] = comment
                self.tag_statuses[tag] = status
                self.tag_flair_ids[tag] = flair_id
                self.tag_required_text[tag] = required_text
        # Parse ignore_tags
        self.ignore_tags = set()
        for entry in config.get('ignore_tags', []):
            tag_val = entry.get('tag', '').strip().lower() if isinstance(entry, dict) else str(entry).strip().lower()
            if tag_val:
                self.ignore_tags.add(tag_val)
        self._last_config_error_revision = None
        return True

    def notify_mods_config_error(self, error_message):
        try:
            subject = "ModReplyBot wiki config error"
            body = f"The bot detected an error in the wiki config page and will not reload until it is fixed.\n\nError details: {error_message}\n\nPlease check the wiki config for formatting or missing information."
            data = {
                "subject": subject,
                "text": body,
                "to": f"/r/{Config.SUBREDDIT}",
            }
            self.reddit.post("api/compose/", data=data)
            self.log("Sent modmail notification about wiki config error.")
        except Exception as e:
            self.log(f"Error sending modmail notification about wiki config error: {e}")

    def load_commented_posts(self):
        try:
            with open(self.commented_posts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    self.commented_posts.add(line.strip())
        except FileNotFoundError:
            pass

    def save_commented_post(self, post_id):
        self.commented_posts.add(post_id)
        with open(self.commented_posts_file, 'a', encoding='utf-8') as f:
            f.write(post_id + '\n')

    def load_filtered_commented_posts(self):
        try:
            with open(self.filtered_commented_posts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    self.filtered_commented_posts.add(line.strip())
        except FileNotFoundError:
            pass

    def load_bot_comments(self):
        with self.bot_comments_lock:
            try:
                with open(self.bot_comments_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        comment_id = line.strip()
                        if comment_id:
                            self.bot_comments.add(comment_id)
            except FileNotFoundError:
                pass

    def save_bot_comment(self, comment_id):
        with self.bot_comments_lock:
            if not comment_id or comment_id in self.bot_comments:
                return
            self.bot_comments.add(comment_id)
            with open(self.bot_comments_file, 'a', encoding='utf-8') as f:
                f.write(comment_id + '\n')

    def remove_bot_comment(self, comment_id):
        with self.bot_comments_lock:
            self.bot_comments.discard(comment_id)
            with open(self.bot_comments_file, 'w', encoding='utf-8') as f:
                for tracked_id in sorted(self.bot_comments):
                    f.write(tracked_id + '\n')

    @staticmethod
    def was_removed_by_moderator(comment):
        removal_category = getattr(comment, 'removed_by_category', None)
        if isinstance(removal_category, str) and removal_category.lower() == 'moderator':
            return True

        if not getattr(comment, 'removed', False):
            return False

        removed_by = getattr(comment, 'banned_by', None)
        removed_by_name = getattr(removed_by, 'name', removed_by)
        if not removed_by_name:
            return False

        return str(removed_by_name).lower() not in {'automoderator', 'reddit'}

    def check_removed_bot_comments(self):
        with self.bot_comments_lock:
            comment_ids = list(self.bot_comments)
        for comment_id in comment_ids:
            try:
                comment = self.reddit.comment(id=comment_id)
                comment.refresh()
                if not self.was_removed_by_moderator(comment):
                    continue
                comment.delete()
                self.remove_bot_comment(comment_id)
                print(f"[COMMENT WATCH] Deleted moderator-removed bot comment: {comment_id}")
            except Exception as e:
                print(f"[COMMENT WATCH] Error checking bot comment {comment_id}: {e}")

    def bot_comment_watcher(self):
        while True:
            try:
                self.check_removed_bot_comments()
            except Exception as e:
                print(f"Bot comment watcher error: {e}")
            time.sleep(60)

    def comment_on_filtered_post(self, submission):
        if not self.filtered_post_comment or submission.id in self.filtered_commented_posts:
            return

        try:
            comment_text = self.filtered_post_comment.replace(
                '{{author}}', submission.author.name if submission.author else 'unknown'
            ).replace(
                '{author}', submission.author.name if submission.author else 'unknown'
            )
            comment = submission.reply(comment_text)
            self.save_bot_comment(comment.id)
            comment.mod.distinguish()
            self.filtered_commented_posts.add(submission.id)
            with open(self.filtered_commented_posts_file, 'a', encoding='utf-8') as f:
                f.write(submission.id + '\n')
            print(f"Posted distinguished filtered-post comment on: {submission.id}")
        except Exception as e:
            print(f"Error commenting on filtered post {submission.id}: {e}")

    def delete_filtered_comment(self, post_id):
        post_id = post_id.removeprefix('t3_')
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            bot_name = self.reddit.user.me().name
            expected_text = self.filtered_post_comment.replace(
                '{{author}}', submission.author.name if submission.author else 'unknown'
            ).replace(
                '{author}', submission.author.name if submission.author else 'unknown'
            )
            for comment in submission.comments.list():
                comment_author = getattr(comment.author, 'name', None)
                if (comment_author == bot_name and
                    getattr(comment, 'distinguished', None) == 'moderator' and
                    comment.body == expected_text):
                    comment.delete()
                    print(f"[CHAT WATCH] Deleted filtered comment from post {post_id}.")
                    return f"Filtered comment deleted from post {post_id}."
            return f"No matching filtered comment found on post {post_id}."
        except Exception as e:
            print(f"[CHAT WATCH] Error deleting filtered comment from post {post_id}: {e}")
            return f"Failed to delete filtered comment from post {post_id}: {e}"

    def delete_all_bot_comments(self, post_id):
        post_id = post_id.removeprefix('t3_')
        deleted_count = 0
        failed_count = 0
        deleted_comment_ids = []
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            bot_name = self.reddit.user.me().name
            for comment in submission.comments.list():
                comment_author = getattr(getattr(comment, 'author', None), 'name', None)
                if comment_author != bot_name:
                    continue
                try:
                    comment.delete()
                    deleted_count += 1
                    deleted_comment_ids.append(comment.id)
                    print(f"[CHAT WATCH] Deleted bot comment {comment.id} from post {post_id}.")
                except Exception as e:
                    failed_count += 1
                    print(f"[CHAT WATCH] Error deleting bot comment {comment.id} from post {post_id}: {e}")

            for comment_id in deleted_comment_ids:
                self.remove_bot_comment(comment_id)

            if failed_count:
                return f"Deleted {deleted_count} bot comment(s) from post {post_id}; {failed_count} failed."
            return f"Deleted {deleted_count} bot comment(s) from post {post_id}."
        except Exception as e:
            print(f"[CHAT WATCH] Error deleting bot comments from post {post_id}: {e}")
            return f"Failed to delete bot comments from post {post_id}: {e}"

    def run(self):
        import threading
        print("ModReplyBot started. Watching for comments and new posts...")
        try:
            config_ok = self.fetch_yaml_config()
            if not config_ok:
                self.log("Bot startup aborted due to wiki config error.")
                return
            self.log(f"Triggers loaded: {self.triggers}")
            self.log(f"Tag comments loaded: {self.tag_comments}")
            self.log(f"Reddit user: {self.reddit.user.me()}")
            self.log(f"Subreddit: {self.subreddit.display_name}")
        except Exception as e:
            self.log(f"Startup error: {e}")
            return

        def mod_comment_watcher():
            last_revision = None
            while True:
                try:
                    old_revision = last_revision
                    config_ok = self.fetch_yaml_config()
                    new_revision = getattr(self, '_wiki_revision_id', None)
                    if old_revision and new_revision and old_revision != new_revision:
                            if config_ok:
                                self.log("Wiki config changed, reloading triggers and tag comments.")
                            else:
                                self.log("Wiki config error detected, not reloading bot.")
                    self.log_level = Config.LOG_LEVEL
                    last_revision = new_revision
                    for comment in self.subreddit.stream.comments(skip_existing=True):
                        if comment.author and comment.author in self.subreddit.moderator():
                            self.handle_comment(comment)
                except Exception as e:
                    print(f"Mod comment watcher error: {e}")
                import time
                time.sleep(5)

        def mod_report_watcher():
            last_revision = None
            while True:
                try:
                    old_revision = last_revision
                    config_ok = self.fetch_yaml_config()
                    new_revision = getattr(self, '_wiki_revision_id', None)
                    if old_revision and new_revision and old_revision != new_revision:
                        if config_ok:
                            self.log("Wiki config changed, reloading triggers and tag comments.")
                            self.notify_mods_config_change(new_revision)
                        else:
                            self.log("Wiki config error detected, not reloading bot.")
                    last_revision = new_revision
                    for submission in self.subreddit.mod.stream.reports():
                        self.handle_submission(submission)
                except Exception as e:
                    print(f"Mod report watcher error: {e}")
                import time
                time.sleep(30)

        threading.Thread(target=mod_comment_watcher, daemon=True).start()
        threading.Thread(target=mod_report_watcher, daemon=True).start()
        threading.Thread(target=self.chat_message_watcher, daemon=True).start()
        threading.Thread(target=self.bot_comment_watcher, daemon=True).start()

        def backfill_recent_posts():
            """Scan recent posts from last 24 hours that bot may have missed while offline."""
            print("[BACKFILL] Starting backfill of recent posts (last 24 hours)...")
            import time
            current_time = time.time()
            one_day_ago = current_time - (24 * 3600)  # 24 hours in seconds
            backfill_count = 0
            
            try:
                # Scan new posts, stopping when we hit posts older than 24 hours
                for submission in self.subreddit.new(limit=1000):
                    if submission.created_utc < one_day_ago:
                        print(f"[BACKFILL] Reached posts older than 24 hours, stopping backfill.")
                        break
                    
                    if submission.id in self.commented_posts:
                        continue  # Already processed
                    
                    flair = (getattr(submission, 'link_flair_text', '') or '').strip().lower()
                    title = submission.title.strip()
                    import re
                    title_tags = re.findall(r'\[(.*?)\]', title)
                    title_tags_lower = [t.strip().lower() for t in title_tags]
                    
                    print(f"[BACKFILL] Checking post {submission.id}: title='{title}', flair='{flair}', title_tags={title_tags_lower}")
                    
                    # Ignore if any ignore_tag matches
                    ignore = False
                    if flair in self.ignore_tags:
                        ignore = True
                    else:
                        for tag in title_tags_lower:
                            if tag in self.ignore_tags:
                                ignore = True
                                break
                    
                    if ignore:
                        print(f"[BACKFILL] Ignoring post {submission.id} due to ignore tag.")
                        continue
                    
                    matched_tag = None
                    if flair in self.tag_comments:
                        matched_tag = flair
                    else:
                        for tag in title_tags_lower:
                            if tag in self.tag_comments:
                                matched_tag = tag
                                break
                    
                    if matched_tag:
                        status = self.tag_statuses.get(matched_tag, 'enabled')
                        comment_text = self.tag_comments[matched_tag]
                        flair_id = self.tag_flair_ids.get(matched_tag, '')
                        
                        # Check if bot has already commented this exact text on the post
                        try:
                            submission.comments.replace_more(limit=0)
                            bot_already_commented = False
                            for comment in submission.comments.list():
                                if comment.author and comment.author.name == self.reddit.user.me().name:
                                    if comment.body == comment_text:
                                        bot_already_commented = True
                                        print(f"[BACKFILL] Bot already posted this comment on {submission.id}, skipping.")
                                        break
                            
                            if bot_already_commented:
                                self.save_commented_post(submission.id)
                                continue
                        except Exception as e:
                            print(f"[BACKFILL] Error checking existing comments on {submission.id}: {e}")
                        
                        if flair_id:
                            try:
                                submission.flair.select(flair_id)
                                print(f"[BACKFILL] Set flair '{flair_id}' for post {submission.id}")
                            except Exception as e:
                                print(f"[BACKFILL] Error setting flair '{flair_id}' for post {submission.id}: {e}")
                        print(f"[BACKFILL] Auto-commenting on post {submission.id} with tag '{matched_tag}'")
                        self.comment_only(submission, comment_text, matched_tag)
                        backfill_count += 1
            except Exception as e:
                print(f"[BACKFILL] Error during backfill: {e}")
            print(f"[BACKFILL] Backfill complete. Commented on {backfill_count} posts, switching to stream mode.")

        def tag_post_watcher():
            print("[TAG WATCH] Starting tag post watcher thread...")
            attempt = 0
            while True:
                try:
                    attempt += 1
                    print(f"[TAG WATCH] Attempt {attempt}: Waiting for new submissions...")
                    for submission in self.subreddit.stream.submissions(skip_existing=True):
                        print(f"[TAG WATCH] GOT SUBMISSION: {submission.id}")
                        flair = (getattr(submission, 'link_flair_text', '') or '').strip().lower()
                        title = submission.title.strip()
                        import re
                        title_tags = re.findall(r'\[(.*?)\]', title)
                        title_tags_lower = [t.strip().lower() for t in title_tags]
                        print(f"[TAG WATCH] Post {submission.id}: title='{title}', flair='{flair}', title_tags={title_tags_lower}")
                        # Ignore if any ignore_tag matches flair or title tag
                        ignore = False
                        if flair in self.ignore_tags:
                            ignore = True
                        else:
                            for tag in title_tags_lower:
                                if tag in self.ignore_tags:
                                    ignore = True
                                    break
                        if ignore:
                            print(f"[TAG WATCH] Ignoring post {submission.id} due to ignore tag.")
                            continue
                        matched_tag = None
                        if flair in self.tag_comments:
                            matched_tag = flair
                        else:
                            for tag in title_tags_lower:
                                if tag in self.tag_comments:
                                    matched_tag = tag
                                    break
                        # Comment on all posts with matching tags
                        if matched_tag and (submission.id not in self.commented_posts):
                            status = self.tag_statuses.get(matched_tag, 'enabled')
                            comment_text = self.tag_comments[matched_tag]
                            flair_id = self.tag_flair_ids.get(matched_tag, '')
                            if flair_id:
                                try:
                                    submission.flair.select(flair_id)
                                    print(f"[TAG WATCH] Set flair '{flair_id}' for post {submission.id}")
                                except Exception as e:
                                    print(f"[TAG WATCH] Error setting flair '{flair_id}' for post {submission.id}: {e}")
                            print(f"Auto-commenting on post {submission.id} with tag '{matched_tag}'")
                            self.comment_only(submission, comment_text, matched_tag)
                except Exception as e:
                    print(f"Tag post watcher error: {e}")
                import time
                time.sleep(30)

        def modqueue_watcher():
            while True:
                try:
                    print("[MODQUEUE DEBUG] Entering modqueue loop...")
                    modqueue_posts = list(self.subreddit.mod.modqueue(limit=100))
                    print(f"[MODQUEUE DEBUG] Fetched {len(modqueue_posts)} posts from modqueue.")
                    for submission in modqueue_posts:
                        # Only access link_flair_text if it's a Submission
                        if hasattr(submission, 'link_flair_text'):
                            flair = (submission.link_flair_text or '').strip().lower()
                        else:
                            flair = ''
                        # Only access title if it's a Submission
                        if hasattr(submission, 'title'):
                            title = submission.title.strip()
                        else:
                            title = ''
                        import re
                        title_tags = re.findall(r'\[(.*?)\]', title)
                        title_tags_lower = [t.strip().lower() for t in title_tags]
                        # Debug print all relevant attributes
                        print(f"[MODQUEUE DEBUG] Post {submission.id}: title='{title}', flair='{flair}', title_tags={title_tags_lower}, author={submission.author}, removed_by_category={getattr(submission, 'removed_by_category', None)}, banned_by={getattr(submission, 'banned_by', None)}, mod_reason_title={getattr(submission, 'mod_reason_title', None)}, spam={getattr(submission, 'spam', None)}, removed={getattr(submission, 'removed', None)}")
                        matched_tag = None
                        if flair in self.tag_comments:
                            matched_tag = flair
                        else:
                            for tag in title_tags_lower:
                                if tag in self.tag_comments:
                                    matched_tag = tag
                                    break
                        # Detect filtered/removed posts
                        is_filtered = False
                        if getattr(submission, 'removed_by_category', None):
                            is_filtered = True
                        if getattr(submission, 'banned_by', None):
                            is_filtered = True
                        if getattr(submission, 'mod_reason_title', None):
                            is_filtered = True
                        if getattr(submission, 'spam', None):
                            is_filtered = True
                        if getattr(submission, 'removed', None):
                            is_filtered = True
                        if is_filtered and hasattr(submission, 'title'):
                            print(f"[MODQUEUE WATCH] Post {submission.id} is filtered/removed.")
                            self.comment_on_filtered_post(submission)
                        # Comment only on filtered/removed posts with matching tags
                        if matched_tag and is_filtered and (submission.id not in self.commented_posts):
                            status = self.tag_statuses.get(matched_tag, 'enabled')
                            comment_text = self.tag_comments[matched_tag]
                            flair_id = self.tag_flair_ids.get(matched_tag, '')
                            if flair_id:
                                try:
                                    submission.flair.select(flair_id)
                                    print(f"[MODQUEUE WATCH] Set flair '{flair_id}' for post {submission.id}")
                                except Exception as e:
                                    print(f"[MODQUEUE WATCH] Error setting flair '{flair_id}' for post {submission.id}: {e}")
                            print(f"Auto-commenting on filtered/removed post {submission.id} with tag '{matched_tag}' from modqueue")
                            self.comment_only(submission, comment_text, matched_tag)
                except Exception as e:
                    print(f"Modqueue watcher error: {e}")
                import time
                time.sleep(30)

        threading.Thread(target=tag_post_watcher, daemon=True).start()
        threading.Thread(target=modqueue_watcher, daemon=True).start()
        
        # Start backfill thread first so it catches posts from when bot was offline
        threading.Thread(target=backfill_recent_posts, daemon=True).start()

        # Keep main thread alive
        while True:
            import time
            time.sleep(60)
    def handle_submission(self, submission):
        # Respond to mod reports containing trigger phrases
        print(f"New mod report detected: {submission.id} | Title: {submission.title}")
        matched_trigger = None
        matched_comment = None
        matched_status = None
        matched_idx = None
        # Check report reasons for triggers
        if hasattr(submission, 'mod_reports') and submission.mod_reports:
            for report_tuple in submission.mod_reports:
                report_reason = report_tuple[0].strip().lower()
                for idx, trigger in enumerate(self.triggers):
                    expected = f"!{trigger.lower()}"
                    if expected in report_reason:
                        matched_trigger = trigger
                        matched_comment = self.comments[idx]
                        matched_status = self.statuses[idx] if idx < len(self.statuses) else 'enabled'
                        matched_idx = idx
                        break
                if matched_trigger:
                    break
        if matched_trigger:
            # Only skip if this exact trigger was already actioned for this post
            trigger_key = f"{submission.id}:{matched_trigger}"
            if hasattr(self, 'triggered_posts'):
                if trigger_key in self.triggered_posts:
                    print(f"Already actioned trigger [{matched_trigger}] on post {submission.id}, skipping.")
                    return
            else:
                self.triggered_posts = set()
            try:
                footer = "^I ^am ^a ^bot ^and ^this ^comment ^was ^made ^automatically. ^Message ^the ^Mod ^team ^if ^I'm ^not ^working ^correctly."
                comment_text = matched_comment.replace("{{author}}", submission.author.name if submission.author else "unknown") + "\n\n" + footer
                self.approve_and_comment(submission, comment_text, matched_status, matched_idx)
                self.triggered_posts.add(trigger_key)
            except Exception as e:
                print(f"Error commenting on mod report: {e}")
        else:
            print(f"No matching trigger found in mod report for post {submission.id}")

    def handle_comment(self, comment):
        comment_body = comment.body.lower()
        for idx, trigger in enumerate(self.triggers):
            expected = f"!{trigger.lower()}"
            words = [w.strip() for w in comment_body.split()]
            # Only respond if author is a moderator
            if expected in words and comment.author and comment.author in self.subreddit.moderator():
                status = self.statuses[idx] if idx < len(self.statuses) else 'enabled'
                if status == 'disabled':
                    print(f"Trigger '{trigger}' is disabled. Skipping.")
                    continue
                try:
                    comment.mod.remove()
                    print(f"Removed triggering comment: {comment.id}")
                except Exception as e:
                    print(f"Error removing comment: {e}")
                submission = comment.submission
                self.fetch_yaml_config()
                self.approve_and_comment(submission, self.comments[idx], status, idx)
                break

    def approve_and_comment(self, submission, comment_text, status='enabled', trigger_idx=None):
        try:
            print(f"[DEBUG] approve_and_comment called with trigger_idx={trigger_idx}")
            if trigger_idx is not None:
                print(f"[DEBUG] Config for trigger_idx={trigger_idx}: lock_post={self.lock_post[trigger_idx]}, stickied={self.stickied[trigger_idx]}, lock_comment={self.lock_comment[trigger_idx]}, flair_id={self.flair_ids[trigger_idx]}")
            # Approve post if configured for this trigger
            # Set flair, stickied, lock_post, lock_comment if configured for this trigger
            if trigger_idx is not None:
                flair_id = self.flair_ids[trigger_idx]
                if flair_id:
                    try:
                        submission.flair.select(flair_id)
                        print(f"[DEBUG] Set flair '{flair_id}' for post {submission.id}")
                    except Exception as e:
                        print(f"[DEBUG] Error setting flair '{flair_id}' for post {submission.id}: {e}")
                print(f"[DEBUG] lock_post[{trigger_idx}] = {self.lock_post[trigger_idx]}")
                if self.lock_post[trigger_idx]:
                    try:
                        submission.mod.lock()
                        print(f"[DEBUG] Locked post {submission.id}")
                    except Exception as e:
                        print(f"[DEBUG] Error locking post {submission.id}: {e}")
                
                # Check required text for triggers
                if trigger_idx < len(self.trigger_required_text):
                    comment_text = self.check_required_text_and_prepend_message(
                        submission, comment_text, self.trigger_required_text[trigger_idx], self.triggers[trigger_idx]
                    )
            
            if status == 'enabled':
                print(f"[DEBUG] Submission object: {submission}, ID: {submission.id}, Type: {type(submission)}")
                comment = submission.reply(comment_text)
                print(f"[DEBUG] Comment object: {comment}, ID: {comment.id}, Type: {type(comment)}")
                self.save_bot_comment(comment.id)
                # Always sticky if stickied is True, match tag logic
                if trigger_idx is not None and self.stickied[trigger_idx]:
                    try:
                        result = comment.mod.distinguish(sticky=True)
                        print(f"[DEBUG] Stickied bot comment {comment.id} on post {submission.id}, result: {result}")
                    except Exception as e:
                        print(f"[DEBUG] Error stickying comment {comment.id} on post {submission.id}: {e}")
                else:
                    try:
                        result = comment.mod.distinguish()
                        print(f"[DEBUG] Distinguished bot comment {comment.id} on post {submission.id}, result: {result}")
                    except Exception as e:
                        print(f"[DEBUG] Error distinguishing comment {comment.id} on post {submission.id}: {e}")
                if trigger_idx is not None and self.lock_comment[trigger_idx]:
                    try:
                        comment.mod.lock()
                        print(f"[DEBUG] Locked bot comment {comment.id} on post {submission.id}")
                    except Exception as e:
                        print(f"[DEBUG] Error locking comment {comment.id} on post {submission.id}: {e}")
                print(f"Approved and commented on: {submission.id}")
                self.save_commented_post(submission.id)
            elif status == 'log-only':
                print(f"Log-only: Approved but did not comment on: {submission.id}")
                self.save_commented_post(submission.id)
            elif status == 'disabled':
                print(f"Disabled: Did not approve/comment/log for: {submission.id}")
            else:
                print(f"Unknown status '{status}' for submission {submission.id}")
        except Exception as e:
            print(f"Error approving/commenting: {e}")

    def notify_mods_config_change(self, revision_id):
        try:
            subject = "ModReplyBot config wiki changed"
            body = f"The config wiki page was updated (revision: {revision_id}).\n\nBot restarted and is running successfully."
            data = {
                "subject": subject,
                "text": body,
                "to": f"/r/{Config.SUBREDDIT}",
            }
            self.reddit.post("api/compose/", data=data)
            print("Sent modmail notification about config change.")
        except Exception as e:
            print(f"Error sending modmail notification: {e}")

if __name__ == "__main__":
    bot = ModReplyBot()
    # Start update checker thread
    start_update_checker(bot.reddit, Config.SUBREDDIT, BOT_NAME, BOT_VERSION)
    bot.run()
