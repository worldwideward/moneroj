'''Module to update Social media data'''
from datetime import date

from charts.api.reddit import RedditAPI
from charts.models import Social

from django.core.exceptions import ObjectDoesNotExist

REDDIT_API = RedditAPI()


def add_socials_entry(subreddit_title):

    today = date.today()

    try:
        Social.objects.get(name=subreddit_title)
        print("[INFO] Entry already exists, skipping")
    except ObjectDoesNotExist:

        client = REDDIT_API.connect()

        subscriber_count = REDDIT_API.get_subreddit_subscriber_count(client, subreddit_title)
        reddit_comments_by_post = REDDIT_API.get_subreddit_daily_comments(client, subreddit_title)

        comment_count = 0

        for post_id in reddit_comments_by_post:

            comments = reddit_comments_by_post[post_id]
            comment_count += len(comments)

        posts_per_hour = round(len(reddit_comments_by_post) / 24, 2)
        comments_per_hour = round(comment_count / 24, 2)

        entry = Social()
        entry.name = subreddit_title
        entry.date = today
        entry.subscriber_count = subscriber_count
        entry.comments_per_hour = comments_per_hour
        entry.posts_per_hour = posts_per_hour
        entry.save()

    except Exception as error:
        print(f'[INFO] An unknown error occurred: {error}')

    return None
