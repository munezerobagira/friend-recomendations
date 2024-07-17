
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
from core.config import DATABASE_URL
engine = create_engine(DATABASE_URL)

SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

def create_tables():
    Base.metadata.create_all(engine)
def create_db_session():
    session=Session()
    return session
