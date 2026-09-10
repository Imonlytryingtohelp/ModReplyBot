
# ModReplyBot Moderator Guide

## Wiki Configuration Page

All bot configuration is managed via your subreddit wiki page. The page name is set by the `REDDIT_WIKI_PAGE` environment variable (default: `modreplybot-config`).

**Always use the old.reddit.com wiki link for editing and referencing your config:**

```
https://old.reddit.com/r/<your_subreddit>/wiki/<wiki_page>
```

## Triggers

Triggers allow moderators to perform bot actions by commenting with a trigger phrase or by reporting a post with a trigger phrase in the report reason. Triggers must start with a `!` (ex: `!test`).

### Example Trigger Configuration
```
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
```

- **trigger**: The phrase (without the `!`) that mods use in comments or report reasons.
- **comment**: The text the bot will post as a stickied comment.
- **status**:
  - `enabled`: Bot will comment and perform actions.
  - `log-only`: Bot will log but not comment.
  - `disabled`: Bot will not act on this trigger.
- **flair_id**: Optional. Set post flair by ID.
- **stickied**: Optional. Sticky the bot's comment.
- **lock_post**: Optional. Lock the post.
- **lock_comment**: Optional. Lock the bot's comment.

## Auto-Post Tags

Auto-post tags allow the bot to comment automatically on new posts with specific tags in the title.

### Example Auto-Post Tag Configuration
```
post_tags:
  - tag: Bedrock, Java
    comment: |
      __[Click here if your post says "Sorry, this post was removed by Reddit’s filters"](...)__
    status: enabled
    flair_id: 12345678-aaaa-bbbb-cccc-1234567890ab
```

- **tag**: Comma-separated list of tags. The bot matches tags in post titles (case-insensitive).
- **comment**: The text the bot will post as a stickied comment.
- **status**:
  - `enabled`: Bot will comment automatically.
  - `log-only`: Bot will log but not comment.
  - `disabled`: Bot will not act on this tag.
- **flair_id**: Optional. Set post flair by ID.

## Filtered Post Comments

Add an optional `filtered_post_comment` to the wiki configuration to post a moderator-distinguished comment when a filtered or removed post appears in the mod queue:

```yaml
filtered_post_comment: |
  This post is awaiting moderator review.
```

The comment is posted once per post and is not sticky. Leave the setting out, or set it to an empty value, to disable this behavior. The `{author}` and `{{author}}` placeholders are supported.

## Chat-Based Config Reload
- To reload the wiki config, send a chat message containing `reload-config` to the bot account from a moderator account.
- The bot will reply to the chat message indicating whether the config is valid or not.
- To delete a filtered-post comment, send `delete-fc <post-id>` from a moderator account. The bot deletes only its matching configured filtered-post comment and removes the post from its filtered-comment tracking file.
- Chat message IDs are tracked in `/DB/chat_wiki_requests.txt` to prevent duplicate reloads after restarts.

## Additional Notes
- The bot only comments once per trigger per post (even if triggered multiple times).
- The bot only auto-comments once per post for each tag.
- All bot actions are logged for transparency.
- If the wiki config is invalid, the bot will reply to the chat message with an error.

## Troubleshooting
- Make sure your wiki config is valid YAML and includes both `triggers` and `post_tags` sections.
- Use old.reddit.com for wiki editing to avoid formatting issues.
- Check bot logs for errors and chat replies for config issues.

## Example Wiki Config Excerpt
```
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
post_tags:
  - tag: Bedrock, Java
    comment: |
      __[Click here if your post says "Sorry, this post was removed by Reddit’s filters"](...)__
    status: enabled
    flair_id: 12345678-aaaa-bbbb-cccc-1234567890ab
```
