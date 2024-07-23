import sys
import json
import pytz
from datetime import datetime
from multiprocessing import Pool, cpu_count, Manager
from database.session import create_db_session, create_tables
from models import Tweet, User, PopularHashtag, TweetHashTag
from core.config import ALLOWED_LANGUAGES

utc = pytz.UTC

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

def extract_popular_hashtags() -> list[str]:
    hashtags = []
    with open("src/etl/dataset/popular_hashtags.txt", "r", encoding='utf-8') as f:
        hashtags = f.readlines()
    hashtags = [hashtag.strip() for hashtag in hashtags]
    print(f"Total valid hashtags parsed: {len(hashtags)}")
    return hashtags

def extract_unique_users(tweets):
    users = {}
    for tweet in tweets:
        user_data = tweet.get('user', {})
        user_id = user_data.get('id_str') or user_data.get('id')
        screen_name = user_data.get('screen_name')
        users[user_id] = screen_name

        retweeted_status = tweet.get('retweeted_status', {})
        if retweeted_status:
            retweeted_user_data = retweeted_status.get('user', {})
            retweeted_user_id = retweeted_user_data.get('id_str') or retweeted_user_data.get('id')
            retweeted_screen_name = retweeted_user_data.get('screen_name')
            users[retweeted_user_id] = retweeted_screen_name
    return users

def save_users_chunk_to_database(users_chunk):
    session = create_db_session()
    new_users = [User(id=user_id, user_id=user_id, screen_name=screen_name) for user_id, screen_name in users_chunk.items()]

    try:
        session.bulk_save_objects(new_users)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving users: {e}")
    finally:
        session.close()

def save_hashtags_chunk_to_database(hashtags_chunk):
    session = create_db_session()

    # Fetch existing hashtags
    existing_hashtags = session.query(PopularHashtag).filter(PopularHashtag.hashtag.in_(hashtags_chunk)).all()
    existing_hashtag_set = {hashtag.hashtag for hashtag in existing_hashtags}

    # Prepare list for new hashtags
    new_hashtags = [PopularHashtag(hashtag=hashtag) for hashtag in hashtags_chunk if hashtag not in existing_hashtag_set]

    # Bulk insert new hashtags
    try:
        if new_hashtags:
            session.bulk_save_objects(new_hashtags)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving hashtags: {e}")
    finally:
        session.close()

def save_tweets_chunk_to_database(tweets_chunk):
    session = create_db_session()
    new_tweets = []
    new_hashtags = []

    for tweet in tweets_chunk:
        tweet_id = tweet.get('id_str') or tweet.get('id')
        text = tweet.get('text')
        in_reply_to_user_id = tweet.get('in_reply_to_user_id_str') or tweet.get('in_reply_to_user_id')
        user_data = tweet.get('user', {})
        retweeted_status = tweet.get('retweeted_status', {})
        created_at = datetime.strptime(tweet.get('created_at'), '%a %b %d %H:%M:%S %z %Y')
        hashtags = tweet.get('entities', {}).get('hashtags', [])
        hashtags = [hashtag.get('text') for hashtag in hashtags]
        lang = tweet.get('lang')

        user_id = user_data.get('id_str') or user_data.get('id')
        retweeted_user_id = retweeted_status.get('user', {}).get('id_str') or retweeted_status.get('user', {}).get('id')

        tweet_entry = Tweet(
            id=tweet_id,
            tweet_id=tweet_id,
            text=text,
            in_reply_to_user_id=in_reply_to_user_id,
            user_id=user_id,
            created_at=created_at,
            retweeted_status=retweeted_status,
            retweeted_status_lang=retweeted_status.get('lang', None),
            retweet_original_user_id=retweeted_user_id,
            lang=lang
        )
        new_tweets.append(tweet_entry)
        for hashtag in hashtags:
            new_hashtags.append(TweetHashTag(hashtag=hashtag, tweet=tweet_entry, tweet_id=tweet_id))

    # Bulk insert new tweets and hashtags
    try:
        if new_tweets:
            session.bulk_save_objects(new_tweets)
        if new_hashtags:
            session.bulk_save_objects(new_hashtags)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving data: {e}")
    finally:
        session.close()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def parallel_save(data, save_function):
    num_chunks = cpu_count()
    chunk_size = len(data) // num_chunks
    data_chunks = list(chunks(data, chunk_size))
    total_chunks = len(data_chunks)
    print(f"Spawning {total_chunks} processes to load data")

    pool = Pool(processes=num_chunks)
    try:
        pool.map(save_function, data_chunks)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print("Process interrupted by user. Terminating pool...")
        pool.terminate()
        pool.join()
        sys.exit(0)

def parallel_save_dict(data_dict, save_function):
    num_chunks = cpu_count()
    chunk_size = len(data_dict) // num_chunks
    data_chunks = [dict(list(data_dict.items())[i:i + chunk_size]) for i in range(0, len(data_dict), chunk_size)]
    total_chunks = len(data_chunks)
    print(f"Spawning {total_chunks} processes to load data")

    pool = Pool(processes=num_chunks)
    try:
        pool.map(save_function, data_chunks)
        pool.close()
        pool.join()
    except KeyboardInterrupt:
        print("Process interrupted by user. Terminating pool...")
        pool.terminate()
        pool.join()
        sys.exit(0)

def load_to_database(tweets):
    users = extract_unique_users(tweets)
    parallel_save_dict(users, save_users_chunk_to_database)

    parallel_save(tweets, save_tweets_chunk_to_database)

if __name__ == '__main__':
    try:
        create_tables()
        tweets = extract_tweets_data()
        load_to_database(tweets)

        hashtags = extract_popular_hashtags()
        parallel_save(hashtags, save_hashtags_chunk_to_database)
    except KeyboardInterrupt:
        print("Process interrupted by user")
        sys.exit(0)
