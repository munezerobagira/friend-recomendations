
from sqlalchemy import Column,  String, DateTime, Text, JSON, ForeignKey, Integer
from models import Base
from sqlalchemy.orm import relationship
class Tweet(Base):
    __tablename__ = 'tweets'
    id = Column(String, primary_key=True)
    in_reply_to_user_id=Column(String, nullable=True)
    tweet_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False)
    text = Column(Text, nullable=False)
    lang = Column(String, nullable=True)
    user_id = Column(String, ForeignKey('users.id'))
    user= relationship("User", back_populates="tweets")
    retweet_original_user_id = Column(String, nullable=True)
    retweeted_status = Column(JSON)
    retweeted_status_lang = Column(String, nullable=True)
    hashtags = relationship("TweetHashTag", back_populates="tweet")
class TweetHashTag(Base):
    __tablename__ = 'tweet_hashtags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(String, ForeignKey('tweets.id'))
    hashtag = Column(String, nullable=False)
    tweet = relationship("Tweet", back_populates="hashtags")