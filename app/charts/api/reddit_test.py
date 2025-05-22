from django.test import TestCase

from unittest.mock import Mock
from unittest.mock import patch

from .reddit import RedditAPI

class TestRedditAPI(TestCase):
    '''Testing Reddit API class'''

    def test_reddit_api(self):
        '''Test retrieving init model'''

        reddit = RedditAPI()

        got = reddit.endpoint
        want = "https://www.reddittorjg6rue252oqsxryoxengawnmo46qy4kyii5wtqnwfj4ooad.onion"

        self.assertEqual(got, want)

    def test_get_subreddit_metadata(self):

        reddit = RedditAPI()

        data = reddit.get_subreddit_metadata('xmr')

        got = data["display_name"]
        want = "Monero"

        self.assertEqual(got, want)
