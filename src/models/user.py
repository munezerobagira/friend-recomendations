from sqlalchemy import Column,  String, DateTime, Text, JSON, ForeignKey,Integer
from sqlalchemy.orm import relationship
from models import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    screen_name = Column(String, nullable=False)
    tweets = relationship('Tweet', back_populates='user')
    last_updated_at = Column(DateTime, nullable=True)
