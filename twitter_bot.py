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
    db_connection = sqlite3.connect(database = os.path.join(path,'follow.db'))
    cur = db_connection.cursor()

    return cur,db_connection

def get_count():
    file = open( os.path.join(path,'count.txt'), 'r')
    count = int(file.read())
    file.close()
    return count
def update_count(count):
    newCount = count + 1
    file = open(os.path.join(path,'count.txt'), 'w')
    file.write(str(newCount))
    file.close()

def save_my_followers_ids(client,me):
        my_followers = client.get_users_followers(me.id,max_results=1000,user_auth=True)
        my_followers_id_list =  [x.id for x in my_followers.data]
        with open(os.path.join(path,me.username+'.json'), 'w') as file:
            json.dump(my_followers_id_list,file,indent=4)
            

#New followers will receive a welcome msg
def welcome_message(client,me):
    print('\n\n Send weclome message to new followers')
    api = get_tweepy_api()
    followers = client.get_users_followers(me.id,max_results=150,user_auth=True)
    follower_ids= [x.id for x in followers.data]
    follower_usernames = [x.username for x in followers.data]
    if me.username+'.json' in os.listdir(path):
        with open(os.path.join(path,me.username+'.json'),'r') as file:
            old_ids = json.load(file)
    else:
        save_my_followers_ids(client,me)
        with open(os.path.join(path,'log.csv'), 'a') as file:
            file.write(f"\"Script have no record of previous followers since it probably ran first time so will send dms to new followers in next iteration\", {datetime.today().replace(microsecond=0)}\n")
        print("script have no record of previous followers since it probably ran first time so will send dms to new followers in next iteration")
        return

    flag =False
    sheet_url = "https://docs.google.com/spreadsheets/d/18wj4qw9FiliqFNP2LLGuf5rMhF1bFcF7FF7E9fbc66E/edit#gid=0"
    url_1 = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    df = pd.read_csv(url_1)

    msg = df.loc[0,'Message']

    print('Below is a list of new followers who have received welcome messages from us.\n\n ')
    for i, follower_id in enumerate(follower_ids):
        if follower_id not in old_ids:
            with open(os.path.join(path,'log.csv'), 'a') as file:
                file.write(f'\"Welcome Message sent to a new follower\", {datetime.today().replace(microsecond=0)}\n')
            api.send_direct_message(follower_id,text=msg)
            print(follower_usernames[i])
            old_ids.append(follower_id)
            flag = True
            sleep(randint(5,15))
    if flag:
        with open(os.path.join(path,me.username+'.json'),'w') as file:
            json.dump(old_ids,file,indent=4)
    else:
        print('There have been no new followers detected since the last time this script was run.')
        

def follow_bot(client,me):
    print('\n\n Currently in follow function')
    conn, db_connection = get_cursor_connection()
    count = get_count()

    conn.execute("""SELECT TwitterID, Follower_Of from Twitter_Ids where id = ? limit 1""", (count,))
    x = conn.fetchall()
    
    try:
        user = client.get_user(id = int(x[0][0]),user_fields =  ['profile_image_url','description','public_metrics'],user_auth=True)[0]     
        with open(os.path.join(path,me.username+'.json'), 'r') as f:
            my_followers_id_list = json.load(f)
        following_me = user.id in my_followers_id_list
        d =datetime.now() - timedelta(days=100)
        tweets = client.get_users_tweets(user.id,start_time = d,user_auth=True)
        posted_in_100_days = bool(tweets[3]['result_count'])
        default_profile_image  = 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'
    except Exception as e:
        print(e)
        update_count(count)    
        db_connection.close()
        return
    #If it is ready following me or it does not fit one of 3 criteria it will not follow
    if (not posted_in_100_days) and (user.profile_image_url == default_profile_image) and (user.public_metrics['followers_count']>1) or (following_me):
        with open(os.path.join(path,'log.csv'), 'a') as file:
            file.write(f'\"Not following One of the conditions did not meet\", \"{user.username}\", {datetime.today().replace(microsecond=0)}\n')
            print("one of the criteria did not meet, so not following: " ,user.username)
        update_count(count)
    else:    
        try:
            client.follow_user(user.id)
            conn.execute("""INSERT INTO Followed_Ids (TwitterID, Follower_Of) VALUES (?,?)""", (user.id,x[0][1]))
            update_count(count)
            db_connection.commit()
            with open(os.path.join(path,'log.csv'), 'a') as file:
                file.write(f'\"followed:\", \"{user.username}\", {datetime.today().replace(microsecond=0)}\n')
            print("followed: ",user.username)
        except Exception as e:
            print(e)
            update_count(count)
    db_connection.close()

def unfollow(client,me):
    print('\n\n in unfollow function')
    c, conn = get_cursor_connection()

    c.execute("""select ID, TwitterID from Followed_Ids where timestamp <= datetime('now', '-3 days') limit ? """, (5,))
    t = c.fetchall()
    for z in t:
        try:
            with open(os.path.join(path,me.username+'.json'), 'r') as f:
                my_followers_id_list = json.load(f)
            following_me = z[1] in my_followers_id_list
            if not following_me:
                with open(os.path.join(path,'log.csv'), 'a') as file:
                    file.write(f'\"unfollowing\", \"a user who is not following as back\", {datetime.today().replace(microsecond=0)}\n')
                print("This person with id "+z[1]+" is not following us back so unfollowing him")
                client.unfollow_user(target_user_id = z[1])
            else:
                print("this nice guy with ID "+z[1]+" is following us back so we gonna delete his name from followedIds without unfollowing him")
            c.execute("""Delete from Followed_Ids where id = ?""", (z[0],))
            conn.commit()
        except Exception as e:
            print("some error occured but going to delete this guy with id "+z[1]+" form followids anyway\n error is:  "+str(e))
            c.execute("""Delete from Followed_Ids where id = ?""", (z[0],))
            conn.commit()
        x = randint(0,20)
        print("sleeping for "+str(x)+" seconds")
        time.sleep(x)    
    conn.close()

def post_random_tweet_from_list(client):
    print('doing a tweet')
    sheet_url = "https://docs.google.com/spreadsheets/d/1VgDVQ6lgl0GQpm7w28AAZvA_wcsbigaqaf_ztDXn1LM/edit#gid=0"
    url_1 = sheet_url.replace('/edit#gid=', '/export?format=csv&gid=')
    df = pd.read_csv(url_1)
    tweet_texts = df.Tweets.to_list()
    tweet_text = choice(tweet_texts)
    with open(os.path.join(path,'log.csv'), 'a') as file:
        file.write(f'\"tweeting this\",\"{tweet_text}\", {datetime.today().replace(microsecond=0)}\n')
    client.create_tweet(text=tweet_text)

def retweet(client):
    with open(os.path.join(path,'log.csv'), 'a') as file:
        file.write(f'\"retweeting a tweet from home timeline\", {datetime.today().replace(microsecond=0)}\n')
    print('retweeting')
    tweets = client.get_home_timeline().data
    client.retweet(choice(tweets).id)

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
        #tweet_mode = int((int(tweet_interval)*60)/135)
        tweet_mode = int((int(tweet_interval)*60)/15)
        #retweet_mode = int((int(retweet_interval)*60)/135)
        retweet_mode = int((int(tweet_interval)*60)/15)
        i+=1
        welcome_message(client,me)
        if i%2==0:
            follow_bot(client,me)
        if i%15==0:
            client = get_tweepy_client()
            me = client.get_me().data
            unfollow(client,me)

        #if i%tweet_mode==0:
            #try:
                #post_random_tweet_from_list(client)
           #except:
                #pass

        #Can't use retweet as we can't control the content of followers.
        #if i%retweet_mode==0:
        #   retweet(client)

        sleep(randint(120,150))
        if i>1000:
            i=0
