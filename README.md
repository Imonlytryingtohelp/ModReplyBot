
# ModReplyBot

ModReplyBot is a Reddit bot for moderators that automates post approval and stickied comments based on subreddit wiki configuration. It responds to mod comments and mod reports containing trigger phrases, and auto-comments on posts with configured tags. All configuration is managed via a subreddit wiki page and environment variables.

## Features
- Responds to moderator comments containing trigger phrases (starting with `!`)
- Responds to moderator reports containing trigger phrases (starting with `!`)
- Approves posts and leaves stickied comments
- Posts automatic comments based on tags in post titles (e.g., `[Bedrock]`, `[Java]`)
- Triggers, tag comments, and bot config are managed via a subreddit wiki page
- Notifies mods via modmail when the config wiki page changes or is invalid
- Persistent database for auto-commented posts (survives restarts and container recreations)
- Docker and baremetal support

## Configuration


### 1. Wiki Page Configuration
Edit your subreddit wiki page (name set by `REDDIT_WIKI_PAGE` env variable) with YAML like:

```yaml
triggers:
  - trigger: help
    comment: |
      Thank you for your report!
      This post is now approved.
    status: enabled
    flair_id: 12345678-aaaa-bbbb-cccc-1234567890ab
    stickied: true
    lock_post: false
    lock_comment: false
  - trigger: wc
    comment: |
      Welcome to the community!
    status: log-only

post_tags:
  - tag: Bedrock, Java
    comment: |
      __[Click here if your post says "Sorry, this post was removed by Reddit’s filters"](...)__
    status: enabled
    flair_id: 12345678-aaaa-bbbb-cccc-1234567890ab

filtered_post_comment: |
  This post is awaiting moderator review.

# New: Ignore tags
ignore_tags:
  - tag: Off-Topic
  - tag: Meme
```

- Triggers: Bot responds to mod comments and mod reports containing `!trigger` (e.g., `!help`) with the configured comment and actions.

- post_tags: Bot posts the comment automatically on new posts with matching tags in the title and can set flair.
- filtered_post_comment: Optional comment posted on filtered or removed posts found in the mod queue. The comment is distinguished by the bot as a moderator comment and is posted once per post.
- ignore_tags: Bot will ignore (not comment on) posts with these tags in the title. Tags are case-insensitive and match `[Tag]` in the post title or flair.
- Status options: `enabled`, `log-only`, `disabled`.
- Optional actions: `flair_id`, `stickied`, `lock_post`, `lock_comment`.

### 2. Environment Variables
Create a `.env` file (or set env variables directly) with:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_USER_AGENT=modreplybot by /u/your_username
REDDIT_SUBREDDIT=your_subreddit
REDDIT_WIKI_PAGE=modreplybot-config
LOG_LEVEL=Default
```

## Installation

### Docker Compose (Recommended)
1. Copy `.env.example` to `.env` and fill in your values.
2. Run:

```
docker compose up -d
```

* The DB folder is mounted for persistent database storage.

### Docker Run
1. Copy `.env.example` to `.env` and fill in your values.
2. Run:

```
docker run --env-file .env -v $(pwd)/DB:/app/DB slfhstd.uk/slfhstd/modreplybot:latest
```

### Baremetal (Direct Python)
1. Install Python 3.11+
2. Install dependencies:

```
pip install -r requirements.txt
```

3. Set environment variables or create a `.env` file.
4. Run:

```
python modreplybot.py
```

## Chat-Based Config Reload
- To reload the wiki config, send a chat message containing `reload-config` to the bot account from a moderator account.
- The bot will reply to the chat message indicating whether the config is valid or not.
- To delete a filtered-post comment, send `delete-fc <post-id>` from a moderator account. The bot will delete its matching filtered-post comment while keeping the post in its filtered-comment tracking file.
- To delete all comments made by the bot on a post, send `delete-all <post-id>` from a moderator account. The bot scans the full comment tree and reports how many comments were deleted.
- Chat message IDs are tracked in `/DB/chat_wiki_requests.txt` to prevent duplicate reloads after restarts.

### Moderator Interaction Log
- Moderator chat commands, trigger comments, and mod reports are recorded in `/DB/moderator_interactions.jsonl`.
- Each line is a JSON object containing a UTC timestamp, moderator username, interaction type, Reddit IDs, trigger or command, status, and result or error details where available.
- The file is append-only and persisted with the Docker `DB` volume so an external webserver can read or tail it.

### Moderator Activity Dashboard
- The dependency-free dashboard is in `/web` and reads the interaction log through `/api/interactions`.
- Run it with `python web/server.py`; it serves the page on port `8080` by default.
- For Docker, run a separate service from the same image with `python web/server.py`, mount the same `DB` volume, and expose the port through your preferred reverse proxy or host configuration.
- Set `MRB_WEB_PORT` or `MRB_INTERACTIONS_LOG` when the defaults need to be changed.

## Troubleshooting
- Ensure your Reddit credentials are correct and have moderator permissions.
- The bot must be able to read the wiki page and approve posts.
- Check logs for errors.
- The bot only responds to mod comments and mod reports for triggers.
- Database is stored in `/DB/commented_posts.txt` and `/DB/chat_wiki_requests.txt` and survives container restarts.
- If the wiki config is invalid, the bot will reply to the chat message with an error.

## Moderator Guide
See `ModGuide.md` for a detailed guide to configuring triggers, auto-post tags, and wiki options.

## License
MIT
