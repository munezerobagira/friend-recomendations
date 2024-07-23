import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import math
from models import Base, User, Tweet, PopularHashtag, TweetHashTag
from services import RankingService
from datetime import datetime

@pytest.fixture(scope='module')
def engine():
    return create_engine('sqlite:///:memory:', echo=False)

@pytest.fixture(scope='module')
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='function')
def session(engine, tables):
    """Creates a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def populate_data(session: Session):
    user1 = User(id=1, user_id=1, screen_name='User1')
    user2 = User(id=2,user_id=2, screen_name='User2')
    user3 = User(id=3,user_id=3, screen_name='User3')

    tweet1 = Tweet(id=1, tweet_id=1, user_id=1, text='Hello World #python', created_at=datetime.now(), lang="en")
    tweet2 = Tweet(id=2,tweet_id=2, user_id=1, text='Reply to User2 #python', in_reply_to_user_id=2,created_at=datetime.now() ,lang="en" )
    tweet3 = Tweet(id=3,tweet_id=3, user_id=2, text='Retweet from User1', retweet_original_user_id=1, created_at=datetime.now(),  lang="en")
    tweet4 = Tweet(id=4,tweet_id=4, user_id=2, text='Hello Python #coding', created_at=datetime.now())
    tweet5 = Tweet(id=5,tweet_id=5, user_id=3, text='Reply to User1 #python', in_reply_to_user_id=1, created_at=datetime.now(), lang="en")

    hashtag1 = TweetHashTag(tweet_id=1, hashtag='python')
    hashtag2 = TweetHashTag(tweet_id=2, hashtag='python')
    hashtag3 = TweetHashTag(tweet_id=4, hashtag='coding')
    hashtag4 = TweetHashTag(tweet_id=5, hashtag='python')

    popular_hashtag1 = PopularHashtag(hashtag='python')
    popular_hashtag2 = PopularHashtag(hashtag='coding')

    session.add_all([user1, user2, user3, tweet1, tweet2, tweet3, tweet4, tweet5, hashtag1, hashtag2, hashtag3, hashtag4, popular_hashtag1, popular_hashtag2])
    session.commit()

@pytest.fixture(scope='function')
def data_session(session):
    populate_data(session)
    yield session

def test_interaction_score(data_session):
    service = RankingService(data_session)
    retweets = service.get_retweets(1)
    replies = service.get_reply(1)
    interaction_score = service.calculate_interaction_score(retweets, replies, 1)
   

    assert round(interaction_score.get("2", 0), 5) == round(math.log(1 + 2*1 + 1*1), 5)
    assert round(interaction_score.get("3", 0), 5) == round(math.log(1 + 2*1 + 0), 5)

def test_hashtag_score(data_session):
    service = RankingService(data_session)
    hashtag_score = service.calculate_hashtag_score(1, ['coding'])

    assert hashtag_score.get("2", 0) == 0  # because the user_1 doesn't have any common hashtag with user_2
    assert hashtag_score.get("3", 0) == 1  # Only one common hashtag 'python'

def test_keyword_score(data_session):
    service = RankingService(data_session)
    keyword_score = service.calculate_keyword_score('from', 'python', 'both')
    print("Keyword score", keyword_score)
    assert round(keyword_score.get("1", 0), 5) == round(1 + math.log(1+1), 5) # as 
    

# def test_final_ranking_score(data_session):
#     service = RankingService(data_session)
#     recommended_users = service.get_recommended_users(1, 'both', 'Hello', 'python')

#     assert len(recommended_users) == 2  # User 2 and User 3 should be recommended

#     for user in recommended_users:
#         assert 'user' in user
#         assert 'score' in user
#         assert user['score'] > 0
