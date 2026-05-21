
# Changelog

## [2.2.3] - 2026-04-04

### Fixed
- **Template Variable Substitution in post_tags Comments:**
  - Fixed issue where `{author}` and `{{author}}` placeholders in `post_tags` comments were not being replaced with the actual post author's username.
  - Template variables now properly substitute in automatic post_tags comments, matching behavior of trigger-based comments.

## [2.2.2] - 2026-03-29

### Added
- **Required Text Feature for Config Validation:**
  - Added `required_text` section to `post_tags` for tag-specific validation rules.
  - Each tag can now have its own list of required text strings to validate posts.
  - If a post with a tag doesn't contain any of the required text strings, a custom message is prepended to the bot's comment.
  - Supports searching in title, body, or both (`search_in` field).
  - Properly handles quoted phrases (e.g., `"Tiny Takeover"`) by stripping quotes before comparison.
  - Allows multiple different validation rules within a single shared post_tag entry.



## [2.2.1] - 2026-03-14

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

## [2.2.0] - 2026-03-12

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


## [2.1.2] - 2026-03-10

### Fixed
- Prevented AttributeError in modqueue watcher by checking for the 'title' attribute before accessing it. This ensures safe handling of Comment objects that do not have a 'title'.

## [2.1.1] - 2026-03-10

### Fixed
- Prevented AttributeError in modqueue watcher and tag_post_watcher by checking for 'link_flair_text' only on Submission objects. This avoids errors when processing Comment objects.

### Changed
- Updated logic in modqueue watcher and tag_post_watcher to safely handle both Submission and Comment objects.

## [2.1.0] - 2026-03-10

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


