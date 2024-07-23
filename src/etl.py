import sys
import json
import pytz
from datetime import datetime
from multiprocessing import Pool, cpu_count, Manager
from database.session import create_db_session, create_tables
from models import Tweet, User, PopularHashtag, TweetHashTag

utc=pytz.UTC

def extract_tweets_data():
    tweets = []
    with open("src/etl/dataset/query2_ref.txt", "r") as f:
        for count, line in enumerate(f):
            try:
                data = json.loads(line)
                # Filter out malformed tweets
                tweet_id = data.get('id_str') or data.get('id')
                user_data = data.get('user', {})
                user_id = user_data.get('id_str') or user_data.get('id')
                created_at = data.get('created_at')
                text = data.get('text')
                hashtags = data.get('entities', {}).get('hashtags', [])
                if not (tweet_id and user_id and created_at and text):
                    raise ValueError("Malformed tweet")
                if not text.strip() or not hashtags:
                    raise ValueError("Malformed tweet")
                tweets.append(data)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Malformed tweet: {e}")

    print(f"Total valid tweets parsed: {len(tweets)}")
    return tweets
def extract_popular_hashtags()->list[str]:
    hashtags = []
    with open("src/etl/dataset/popular_hashtags.txt", "r",encoding='utf-8') as f:
        hashtags=f.readlines()

    print(f"Total valid hash parsed: {len(hashtags)}")
    return hashtags
def save_tweets_chunk_to_database(args):
    tweets_chunk, progress, total_chunks, lock = args
    total_tweets = len(tweets_chunk)
    session = create_db_session()

    for tweet in tweets_chunk:
        tweet_id = tweet.get('id_str') or tweet.get('id')
        text = tweet.get('text')
        in_reply_to_user_id = tweet.get('in_reply_to_user_id_str') or tweet.get('in_reply_to_user_id')
        user_data = tweet.get('user', {})
        retweeted_status = tweet.get('retweeted_status', {})
        created_at=datetime.strptime(tweet.get('created_at'), '%a %b %d  %H:%M:%S %z %Y')
        hashtags = tweet.get('entities', {}).get('hashtags', [])
        hashtags = [hashtag.get('text') for hashtag in hashtags] 

        user_id = user_data.get('id_str') or user_data.get('id')
        screen_name = user_data.get('screen_name')





        # Check if user exists in the database
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(id=user_id, user_id=user_id, screen_name=screen_name, last_updated_at=created_at)
            session.add(user)
            session.commit()
        else:
            if(user.screen_name != screen_name and utc.localize(user.last_updated_at)< created_at):
                user.screen_name = screen_name
                session.commit()
        if  not not retweeted_status:
            retweeted_user_data = retweeted_status.get('user', {})
            retweeted_user_id = retweeted_user_data.get('id_str') or retweeted_user_data.get('id')
            retweeted_user = session.query(User).filter_by(user_id=retweeted_user_id).first()
            if not retweeted_user:
                retweeted_user = User(id=retweeted_user_id, user_id=retweeted_user_id, screen_name=retweeted_user_data.get('screen_name'), last_updated_at=created_at)
                session.add(retweeted_user)
                session.commit()
            else:
                if(retweeted_user.screen_name != retweeted_user_data.get('screen_name') and utc.localize(retweeted_user.last_updated_at)< created_at):
                    retweeted_user.screen_name = retweeted_user_data.get('screen_name')
                    session.commit()
        # Create tweet entry
        tweet_entry = session.query(Tweet).filter_by(id=tweet_id).first()
        if not tweet_entry:
            tweet_entry = Tweet(
                id=tweet_id,
                tweet_id=tweet_id,
                text=text,
                in_reply_to_user_id=in_reply_to_user_id,
                user_id=user_id,
                created_at=created_at,
                retweeted_status=retweeted_status,
                retweeted_status_lang=retweeted_status.get('lang', None),
                retweet_original_user_id=retweeted_status.get('user', {}).get('id_str') or retweeted_status.get('user', {}).get('id')
            )

            session.add(tweet_entry)
            for hashtag in hashtags:
                tweet_entry.hashtags.append(TweetHashTag(hashtag=hashtag, tweet=tweet_entry))
            session.commit()
        
    session.close()
    # Update progress
    with lock:
        progress.value += 1
        print(f"Progress: {progress.value}/{total_chunks} chunks processed ({(progress.value / total_chunks) * 100:.2f}%)")
def save_hashtags_to_database(hashtags: list[str]):
    session = create_db_session()
    for hashtag in hashtags:
        hashtag_entry = session.query(PopularHashtag).filter_by(hashtag=hashtag).first()
        if not hashtag_entry:
            hashtag_entry = PopularHashtag(hashtag=hashtag)
            session.add(hashtag_entry)
            session.commit()
    session.close()
def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# Split tweets into chunks
def load_to_database(tweets: list):
    num_chunks = cpu_count()
    chunk_size = len(tweets) // num_chunks
    tweet_chunks = list(chunks(tweets, chunk_size))
    total_chunks = len(tweet_chunks)
    print(f"Spawning {total_chunks} processes to load data")

    # Use Manager to track progress and lock
    with Manager() as manager:
        progress = manager.Value('i', 0)
        lock = manager.Lock()
        args = [(chunk, progress, total_chunks, lock) for chunk in tweet_chunks]

        pool = Pool(processes=num_chunks)
        try:
            pool.map(save_tweets_chunk_to_database, args)  
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            print("Process interrupted by user. Terminating pool...")
            pool.terminate()
            pool.join()
            sys.exit(0)

        print("Data successfully loaded into the database.")

if __name__ == '__main__':
    try:
    
        create_tables()
        # tweets = extract_tweets_data()
        # load_to_database(tweets)

        hashtags = extract_popular_hashtags()
        save_hashtags_to_database(hashtags)
    except KeyboardInterrupt:
        Manager.shutdown()
        print("Process interrupted by user")
        sys.exit(0)
