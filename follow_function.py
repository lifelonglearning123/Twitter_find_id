import tweepy, json, os, requests
from random import randint,choice
from time import sleep
import pandas as pd
from datetime import datetime,timedelta
from configparser import ConfigParser
from datetime import datetime

abspath = os.path.abspath(__file__)
path = os.path.dirname(abspath)
config  = ConfigParser(interpolation=None)
config.read(os.path.join(path,'config.ini'))

def get_tweepy_client():
    keys = config['apivalues']
    consumer_key = keys.get('consumer_key')
    consumer_secret = keys.get('consumer_secret')
    access_token = keys.get('access_token')
    access_token_secret = keys.get('access_token_secret')
    bt = keys.get('bearer_token')
    client = tweepy.Client(bearer_token=bt,consumer_key=consumer_key, consumer_secret= consumer_secret, access_token=access_token, access_token_secret= access_token_secret)
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

def get_cursor_connection():
    import sqlite3
    db_connection = sqlite3.connect(database=os.path.join(path, 'follow.db'))
    cur = db_connection.cursor()

    return cur, db_connection


def get_count():
    file = open(os.path.join(path, 'count.txt'), 'r')
    count = int(file.read())
    file.close()
    return count


def update_count(count):
    newCount = count + 1
    file = open(os.path.join(path, 'count.txt'), 'w')
    file.write(str(newCount))
    file.close()


def save_my_followers_ids(client, me):
    my_followers = client.get_users_followers(me.id, max_results=1000, user_auth=True)
    my_followers_id_list = [x.id for x in my_followers.data]
    with open(os.path.join(path, me.username + '.json'), 'w') as file:
        json.dump(my_followers_id_list, file, indent=4)



# New followers will receive a welcome msg
def welcome_message(client, me):
    print('\n\n Send weclome message to new followers')
    api = get_tweepy_api()
    followers = client.get_users_followers(me.id, max_results=150, user_auth=True)
    follower_ids = [x.id for x in followers.data]
    follower_usernames = [x.username for x in followers.data]
    if me.username + '.json' in os.listdir(path):
        with open(os.path.join(path, me.username + '.json'), 'r') as file:
            old_ids = json.load(file)
    else:
        save_my_followers_ids(client, me)
        with open(os.path.join(path, 'log.csv'), 'a') as file:
            print(
                "script have no record of previous followers since it probably ran first time so will send dms to new followers in next iteration")
        return

    flag = False
    # sheet_url = "https://docs.google.com/spreadsheets/d/18wj4qw9FiliqFNP2LLGuf5rMhF1bFcF7FF7E9fbc66E/edit#gid=0"
    # url_1 = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    # df = pd.read_csv(url_1)

    # msg = df.loc[0,'Message']

    print('Below is a list of new followers who have received welcome messages from us.\n\n ')
    for i, follower_id in enumerate(follower_ids):
        if follower_id not in old_ids:
            with open(os.path.join(path, 'log.csv'), 'a') as file:
                file.write(
                    f'\"Welcome Message sent to a new follower\", \"{follower_usernames[i]}\", {datetime.today().replace(microsecond=0)}\n')
            api.send_direct_message(follower_id, text="Thanks for following @macaws.ai! We're excited to help you elevate your social media and SEO game. #AI #automation #socialmediamarketing #SEO")
            print(follower_usernames[i])
            old_ids.append(follower_id)
            flag = True
            sleep(randint(5, 15))
    if flag:
        with open(os.path.join(path, me.username + '.json'), 'w') as file:
            json.dump(old_ids, file, indent=4)
    else:
        print('There have been no new followers detected since the last time this script was run.')


def follow_bot(client, me):
    print('\n\n Currently in follow function')
    conn, db_connection = get_cursor_connection()
    count = get_count()

    conn.execute("""SELECT TwitterID, Follower_Of from Twitter_Ids where id = ? limit 1""", (count,))
    x = conn.fetchall()

    try:
        user = client.get_user(id=int(x[0][0]), user_fields=['profile_image_url', 'description', 'public_metrics'],
                               user_auth=True)[0]
        with open(os.path.join(path, me.username + '.json'), 'r') as f:
            my_followers_id_list = json.load(f)
        following_me = user.id in my_followers_id_list
        d = datetime.now() - timedelta(days=100)
        tweets = client.get_users_tweets(user.id, start_time=d, user_auth=True)
        posted_in_100_days = bool(tweets[3]['result_count'])
        default_profile_image = 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'
    except Exception as e:
        print(e)
        update_count(count)
        db_connection.close()
        return
    # If it is ready following me or it does not fit one of 3 criteria it will not follow
    if (not posted_in_100_days) and (user.profile_image_url == default_profile_image) and (
            user.public_metrics['followers_count'] > 1) or (following_me):
        with open(os.path.join(path, 'log.csv'), 'a') as file:
            file.write(
                f'\"Not following One of the conditions did not meet\", \"{user.username}\", {datetime.today().replace(microsecond=0)}\n')
            print("one of the criteria did not meet, so not following: ", user.username)
        update_count(count)
    else:
        try:
            client.follow_user(user.id)
            conn.execute("""INSERT INTO Followed_Ids (TwitterID, Follower_Of) VALUES (?,?)""", (user.id, x[0][1]))
            update_count(count)
            db_connection.commit()
            with open(os.path.join(path, 'log.csv'), 'a') as file:
                file.write(f'\"followed:\", \"{user.username}\", {datetime.today().replace(microsecond=0)}\n')
            print("followed: ", user.username)
        except Exception as e:
            print(e)
            update_count(count)
    db_connection.close()


if __name__ ==  '__main__':
    i=1
    #get_tweepy_client calls on Tweepy API
    client = get_tweepy_client()
    #me captures client data
    me = client.get_me().data
    while True:
        keys = config['genvalues']
        tweet_interval = keys.get('tweet_interval_minutes')
        retweet_interval = keys.get('retweet_interval_minutes')
        i+=1
        welcome_message(client,me) #Send welcome message if there is someone new following
        if i%2==0:
            follow_bot(client,me)


        #Can't use retweet as we can't control the content of followers.
        #if i%retweet_mode==0:
        #   retweet(client)

        sleep(randint(100,140))
        if i>1000:
            i=0
