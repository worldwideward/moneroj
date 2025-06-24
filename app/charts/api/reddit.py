'''A module to communicate with the Reddit API'''

import os
import json
import praw

from django.conf import settings

REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')

TOR_HOST = settings.TOR_HOST
TOR_PORT = settings.TOR_PORT

class RedditAPI():

    def __init__(self):
        '''Initialize a Reddit API client through a TOR proxy'''

        #self.endpoint = "https://www.reddittorjg6rue252oqsxryoxengawnmo46qy4kyii5wtqnwfj4ooad.onion"
        self.user_agent = "Moneroj.net"

        self.client_id=REDDIT_CLIENT_ID
        self.client_secret=REDDIT_CLIENT_SECRET
        self.reddit_username=REDDIT_USERNAME
        self.reddit_password=REDDIT_PASSWORD

        #os.environ["HTTP_PROXY"] = f'socks5h://{TOR_HOST}:{TOR_PORT}'
        #os.environ["HTTPS_PROXY"] = f'socks5h://{TOR_HOST}:{TOR_PORT}'

        return None

    def connect(self):
        '''Connect to the Reddit API using the password flow for Script Applications'''

        client = praw.Reddit(
                #reddit_url=self.endpoint,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.reddit_username,
                password=self.reddit_password,
                user_agent=self.user_agent)

        authenticated_user = client.user.me()

        print(f'[DEBUG] Authenticated user: {authenticated_user}')

        return client

    def get_subreddit_subscriber_count(self, client, subreddit_title):
        '''Retrieve total subscriber count for a subreddit'''

        subreddit = client.subreddit(subreddit_title)

        subscriber_count = subreddit.subscribers

        return subscriber_count

    def get_subreddit_daily_posts(self, client, subreddit_title):
        '''Retrieve list of Reddit posts from the past day for a given subreddit'''

        subreddit = client.subreddit(subreddit_title)

        reddit_post_ids = []

        for entry in subreddit.search(query="*", time_filter="day"):

            reddit_post_ids.append(entry.id)

        print(f'[DEBUG] Found {len(reddit_post_ids)} Reddit posts')

        return reddit_post_ids

    def get_subreddit_daily_comments(self, client, subreddit_title):
        '''Retrieve dictonary of comments on Reddit posts from the past day for a give subreddit'''

        subreddit = client.subreddit(subreddit_title)

        reddit_comments_by_post = {}

        reddit_post_ids = []

        for entry in subreddit.search(query="*", time_filter="day"):

            reddit_post_ids.append(entry.id)

        print(f'[DEBUG] Found {len(reddit_post_ids)} Reddit posts')

        for post_id in reddit_post_ids:

            post = client.submission(id=post_id)

            print(f'[DEBUG] Parsing comments for post {post_id} with title: {post.title}')

            comments = post.comments.list()

            comment_ids = []

            for comment in comments:

                comment_ids.append(comment.id)

                #print(f'[DEBUG] Parsing comment {comment.id} from {comment.author}')

            print(f'[DEBUG] This post has yielded {len(comment_ids)} comments')

            reddit_comments_by_post[post_id] = comment_ids

        return reddit_comments_by_post
