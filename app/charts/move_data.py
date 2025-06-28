'''Move data from DailyData to dedicated models'''

from charts.models import DailyData
from charts.models import Social


def erase_empty_entries_social():
    '''Remove empty entries from social model'''

    social_data = Social.objects.order_by('date')

    for x in social_data:

        if x.subscriber_count == 0:

            x.delete()

    return True

def migrate_daily_to_social():
    '''Migrate Reddit data to social model'''

    daily_data = DailyData.objects.order_by('date')

    for x in daily_data:

        monero = Social()
        monero.name = 'Monero'
        monero.date = x.date
        monero.subscriber_count = int(x.xmr_subscriber_count)
        monero.comments_per_hour = x.xmr_comments_per_hour
        monero.posts_per_hour = x.xmr_posts_per_hour
        monero.save()

        bitcoin = Social()
        bitcoin.name = 'Bitcoin'
        bitcoin.date = x.date
        bitcoin.subscriber_count = int(x.btc_subscriber_count)
        bitcoin.comments_per_hour = x.btc_comments_per_hour
        bitcoin.posts_per_hour = x.btc_posts_per_hour
        bitcoin.save()

        cryptocurrency = Social()
        cryptocurrency.name = 'CryptoCurrency'
        cryptocurrency.date = x.date
        cryptocurrency.subscriber_count = int(x.crypto_subscriber_count)
        cryptocurrency.comments_per_hour = x.crypto_comments_per_hour
        cryptocurrency.posts_per_hour = x.crypto_posts_per_hour
        cryptocurrency.save()

    return True

