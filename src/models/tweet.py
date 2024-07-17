
from sqlalchemy import Column,  String, DateTime, Text, JSON, ForeignKey
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
    hashtags = Column(JSON)

