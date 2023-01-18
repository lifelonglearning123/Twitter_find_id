import tweepy, json, os, requests
from random import randint, choice
from time import sleep
import pandas as pd
from datetime import datetime, timedelta
from configparser import ConfigParser
from datetime import datetime

abspath = os.path.abspath(__file__)
path = os.path.dirname(abspath)
config = ConfigParser(interpolation=None)
config.read(os.path.join(path, 'config.ini'))


def get_tweepy_client():
    keys = config['apivalues']
    consumer_key = keys.get('consumer_key')
    consumer_secret = keys.get('consumer_secret')
    access_token = keys.get('access_token')
    access_token_secret = keys.get('access_token_secret')
    bt = keys.get('bearer_token')
    client = tweepy.Client(bearer_token=bt, consumer_key=consumer_key, consumer_secret=consumer_secret,
                           access_token=access_token, access_token_secret=access_token_secret)
    return client


def get_tweepy_api():
    keys = config['apivalues']
    consumer_key = keys.get('consumer_key')
    consumer_secret = keys.get('consumer_secret')
    access_token = keys.get('access_token')
    access_token_secret = keys.get('access_token_secret')
    auth01 = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth01.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth01, wait_on_rate_limit=True)
    return api


def post_random_tweet_from_list(client):
    print('Twitting')
    sheet_url = "https://docs.google.com/spreadsheets/d/1VgDVQ6lgl0GQpm7w28AAZvA_wcsbigaqaf_ztDXn1LM/edit#gid=0"
    url_1 = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    df = pd.read_csv(url_1)
    tweet_texts = df.Tweets.to_list()
    tweet_text = choice(tweet_texts)
    with open(os.path.join(path, 'log.csv'), 'a') as file:
        file.write(f'\"Tweeting \",\"{tweet_text}\", {datetime.today().replace(microsecond=0)}\n')
    client.create_tweet(text=tweet_text)



if __name__ == '__main__':
    # get_tweepy_client calls on Tweepy API
    client = get_tweepy_client()
    # me captures client data
    me = client.get_me().data
    try:
        post_random_tweet_from_list(client)
    except:
        pass

