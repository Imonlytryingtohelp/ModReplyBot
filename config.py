import os
import praw

class Config:
    CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
    USERNAME = os.environ.get('REDDIT_USERNAME')
    PASSWORD = os.environ.get('REDDIT_PASSWORD')
    USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'modreplybot by /u/your_username')
    SUBREDDIT = os.environ.get('REDDIT_SUBREDDIT')
    WIKI_PAGE = os.environ.get('REDDIT_WIKI_PAGE', 'modreplybot-config')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'Default')

    @staticmethod
    def validate():
        required = [Config.CLIENT_ID, Config.CLIENT_SECRET, Config.USERNAME, Config.PASSWORD, Config.SUBREDDIT]
        if not all(required):
            raise ValueError('Missing required Reddit environment variables.')


def get_reddit():
    Config.validate()
    return praw.Reddit(
        client_id=Config.CLIENT_ID,
        client_secret=Config.CLIENT_SECRET,
        username=Config.USERNAME,
        password=Config.PASSWORD,
        user_agent=Config.USER_AGENT
    )
