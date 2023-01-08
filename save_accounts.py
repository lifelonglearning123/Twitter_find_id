import tweepy,os
import time
from configparser import ConfigParser

def get_tweepy_client(keys):
    consumer_key = keys.get('consumer_key')
    consumer_secret = keys.get('consumer_secret')
    access_token = keys.get('access_token')
    access_token_secret = keys.get('access_token_secret')
    bearer_token = keys.get('bearer_token')
    client = tweepy.Client(consumer_key=consumer_key, consumer_secret= consumer_secret, access_token=access_token, access_token_secret= access_token_secret,bearer_token=bearer_token)
    return client

def get_follower_ids(api, handle_ids):
    followerids =[]
    for handle_id in handle_ids:
        f_ids = []
        for user in tweepy.Paginator(client.get_users_followers,handle_id,max_results=1000,user_auth=True).flatten():
            f_ids.append(user.id)
            print(user.id)
            time.sleep(0.1)
            if len(f_ids) > 1000:
                break
        followerids.extend(f_ids)
    print ("total length of follower id list: ",len(followerids))
    return followerids

def get_cursor_connection(dbname):
    import sqlite3
    db_connection = sqlite3.connect(database = os.path.join(path,dbname))
    cur = db_connection.cursor()

    return cur,db_connection

def create_tables(cur):

    tbl1_sql = """ CREATE TABLE IF NOT EXISTS Followed_Ids (
                                        id integer PRIMARY KEY,
                                        TwitterID text NOT NULL,
                                        Follower_Of text,
                                        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    ); """
    cur.execute(tbl1_sql)
    print("created tables")


    tbl_sql = """ CREATE TABLE IF NOT EXISTS Twitter_Ids (
                                        id integer PRIMARY KEY,
                                        TwitterID text NOT NULL,
                                        Follower_Of text
                                    ); """
    cur.execute(tbl_sql)

def insertdata(followerids,cur):    
    for f_id in followerids:
        cur.execute("""INSERT INTO Twitter_Ids (TwitterID) VALUES (?)""", (f_id,))
    
def close_connection(connection):
    connection.commit()
    connection.close()
    

if __name__ == "__main__":

    abspath = os.path.abspath(__file__)
    path = os.path.dirname(abspath)
    config = ConfigParser(interpolation=None)
    config.read(os.path.join(path,'config.ini'))
    keys = config['genvalues']
    handles = keys.get('handles_to_extract_followers_off')
    dbname = 'follow.db'
    handles =[x.strip() for x in handles.split(',')]
    keys = config['apivalues']
    client = get_tweepy_client(keys)
    
    users  = client.get_users(usernames = handles).data
    handle_ids = [x.id for x in users]
    
#     tic = time.time()
    followerids = get_follower_ids(client, handle_ids)
#     toc = time.time()
#     print('secodns to get userids: ',toc-tic)
    
    cur,connection = get_cursor_connection(dbname)
    create_tables(cur)

    insertdata(followerids,cur)

    close_connection(connection)