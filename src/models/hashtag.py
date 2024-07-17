from sqlalchemy import Column,  String, DateTime,Integer
from models import Base 
from datetime import datetime


class PopularHashtag(Base):
    __tablename__ = 'popular_hashtags'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hashtag = Column(String, nullable=False)
    last_updated_at = Column(DateTime, nullable=True, default=datetime.now)