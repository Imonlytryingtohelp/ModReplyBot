
# Changelog

## [2.4.0]

### Added
- **Moderator-Removed Comment Cleanup:**
  - Tracks bot-created comment IDs in the persistent database.
  - Checks tracked comments periodically and deletes them when Reddit reports they were removed by a moderator.
  - Leaves comments with other or unknown removal causes untouched.
- **Delete All Bot Comments Chat Command:**
  - Added the moderator-only `delete-all <post-id>` chat command.
  - Deletes every comment authored by the bot on the specified post, including comments not in the tracking database.

## [2.3.1]

### Added
- **Filtered Posts Comment:**
  - Added the configurable `filtered_post_comment` wiki setting.
  - Posts a moderator-distinguished comment when a filtered or removed post appears in the mod queue.
  - Tracks filtered-post comments so each post is handled once.
- **Filtered Comment Deletion Chat Command:**
  - Added the moderator-only `delete-fc <post-id>` chat command.
  - Deletes the bot's matching moderator-distinguished filtered-post comment.
  - Keeps the post in filtered-comment tracking after deletion to prevent additional filtered comments.

## [2.3.0]

### ⚠️ BREAKING CHANGES
- **Docker Environment Variables Prefix Change:**
  - All Docker environment variables now require the `MRB_` prefix for security isolation.
  - Old variable names (e.g., `REDDIT_CLIENT_ID`) are **no longer supported**.
  - Migration required: Update your `.env` file with the new prefixed names:
    - `REDDIT_CLIENT_ID` → `MRB_REDDIT_CLIENT_ID`
    - `REDDIT_CLIENT_SECRET` → `MRB_REDDIT_CLIENT_SECRET`
    - `REDDIT_USERNAME` → `MRB_REDDIT_USERNAME`
    - `REDDIT_PASSWORD` → `MRB_REDDIT_PASSWORD`
    - `REDDIT_USER_AGENT` → `MRB_REDDIT_USER_AGENT`
    - `REDDIT_SUBREDDIT` → `MRB_REDDIT_SUBREDDIT`
    - `REDDIT_WIKI_PAGE` → `MRB_REDDIT_WIKI_PAGE`
    - `LOG_LEVEL` → `MRB_LOG_LEVEL`
  - No fallback for old variable names. Bot will fail to start if new names are not set.

## [2.2.3]

### Fixed
- **Template Variable Substitution in post_tags Comments:**
  - Fixed issue where `{author}` and `{{author}}` placeholders in `post_tags` comments were not being replaced with the actual post author's username.
  - Template variables now properly substitute in automatic post_tags comments, matching behavior of trigger-based comments.

## [2.2.2]

### Added
- **Required Text Feature for Config Validation:**
  - Added `required_text` section to `post_tags` for tag-specific validation rules.
  - Each tag can now have its own list of required text strings to validate posts.
  - If a post with a tag doesn't contain any of the required text strings, a custom message is prepended to the bot's comment.
  - Supports searching in title, body, or both (`search_in` field).
  - Properly handles quoted phrases (e.g., `"Tiny Takeover"`) by stripping quotes before comparison.
  - Allows multiple different validation rules within a single shared post_tag entry.



## [2.2.1]

### Added
- **Post Backfill on Startup:**
  - Added `backfill_recent_posts()` to automatically scan and comment on posts from the last 24 hours when bot starts up.
  - Prevents missed posts when bot is offline for extended periods.
  - Only processes posts created in the last 24 hours to avoid overwhelming backfill.
- **Duplicate Comment Detection:**
  - Bot now checks if the exact comment has already been posted on a post before commenting again.
  - Prevents duplicate comments on the same post.

### Changed
- Enhanced tag_post_watcher with better debug output and attempt tracking.
- Startup now prioritizes backfill thread for catching missed posts.

### Fixed
- Fixed issue where new submissions stream wasn't being processed (skip_existing=True issue).
- Improved stream error handling with attempt counter and better exception messages.

## [2.2.0]

### Added
- **Configurable Ignore Tags:**
  - Added `ignore_tags` section to wiki config. Bot now ignores posts with matching tags in the title or flair (case-insensitive).
  - Updated README.md and bot logic to support this feature.
- **Update Checker Integration:**
  - Added `update_checker.py` module to check for bot updates and notify moderators via modmail.
  - Update checker runs in a background thread and checks for updates hourly.
- **Bot Version & Name Constants:**
  - Added `BOT_VERSION` and `BOT_NAME` constants at the top of `modreplybot.py` for easy version/name changes.

### Changed
- Integrated update checker startup in main bot entrypoint.
- Improved documentation for ignore_tags and update checker features.

### Fixed
- N/A


## [2.1.2]

### Fixed
- Prevented AttributeError in modqueue watcher by checking for the 'title' attribute before accessing it. This ensures safe handling of Comment objects that do not have a 'title'.

## [2.1.1]

### Fixed
- Prevented AttributeError in modqueue watcher and tag_post_watcher by checking for 'link_flair_text' only on Submission objects. This avoids errors when processing Comment objects.

### Changed
- Updated logic in modqueue watcher and tag_post_watcher to safely handle both Submission and Comment objects.

## [2.1.0]

### Changed
- Improved tag_post_watcher and modqueue_watcher logic: now runs modqueue watcher in a dedicated thread for reliable detection and commenting on filtered/removed posts.
- Enhanced debug output for modqueue posts, including detailed attribute printing.
- Updated .gitignore to include tests.py.
- Updated DB/commented_posts.txt and DB/chat_wiki_requests.txt for persistent tracking.

### Fixed
- Fixed issue where bot did not comment on posts in modqueue due to threading/loop logic.
- Fixed detection of automod_filtered/removed posts in modqueue.

### Added
- Added modqueue_watcher thread for independent modqueue processing.
- Added debug print statements for modqueue post attributes and loop entry.



---
## [V2 release]

### Major Features & Enhancements
- **Chat-Based Config Reload:**
  - Bot reloads wiki config when a moderator sends a chat message containing `reload-config`.
  - Bot replies to chat messages indicating config validity.
  - Chat message IDs are tracked in `/DB/chat_wiki_requests.txt` for persistence across restarts.

- **Configurable Actions for Triggers and Tags:**
  - Added support for optional `flair_id`, `stickied`, `lock_post`, and `lock_comment` in both triggers and post_tags.
  - Bot can set flair, sticky comments, lock posts/comments as specified in wiki config.

- **Persistent Tracking:**
  - Auto-commented posts and processed chat requests are tracked in `/DB/commented_posts.txt` and `/DB/chat_wiki_requests.txt`.

### Code & Documentation Updates
- **modreplybot.py:**
  - Refactored to remove all modmail notification code.
  - All config reloads and error notifications are now handled via chat messages.
  - Improved error handling and logging.
  - Updated logic for flair/tag actions and chat message processing.

- **README.md & ModGuide.md:**
  - Updated to reflect chat-based config reload, new config options, and persistent tracking.
  - Added detailed examples for triggers and post_tags with new fields.

- **DB Folder:**
  - Added `/DB/chat_wiki_requests.txt` for persistent chat request tracking.
  - Updated `/DB/commented_posts.txt` for improved tracking.

### Other Changes
- **Removed:**
  - All modmail-based notifications and config reloads.
  - Legacy approval logic and unnecessary config options.


