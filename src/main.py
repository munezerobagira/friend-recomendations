
from fastapi import FastAPI
from enum import Enum
from services.ranking_service import RankingService
from database import create_db_session
app = FastAPI()

class TweetType(str, Enum):
    reply="reply"
    retweet="retweet"
    both="both"

@app.get("/")
def ping():
    return {"ping": "pong"}
@app.get("/q2")
def recomendended_users(user_id:int,type:TweetType, phrase: str, hashtag: str):
    session=create_db_session()
    ranking_service=RankingService(session)
    recomendended_users=ranking_service.get_recommended_users(user_id,type.value,phrase,hashtag)
    return recomendended_users