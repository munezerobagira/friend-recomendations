import math
from sqlalchemy import and_ , or_, cast, String,Text
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models import User, Tweet,PopularHashtag, TweetHashTag
from core.config import ALLOWED_LANGUAGES
base_query = select(Tweet).where(Tweet.lang.in_(ALLOWED_LANGUAGES))

class RankingService:
    def __init__(self, session:Session):
        self.session: Session=session
    def get_popular_hashtags(self)->list[PopularHashtag]:
        
        popular_hashtags=self.session.scalars(select(PopularHashtag).order_by(PopularHashtag.id.desc())).all()
        return popular_hashtags

    def get_user(self, user_id: int)->User:
        user=self.session.query(User).filter(User.user_id==f"{user_id}").first()
        return user
    def get_reply(self, user_id: int)->list[Tweet]:
        reply_tweets=self.session.scalars(base_query.where(Tweet.in_reply_to_user_id != None).where(
            or_(Tweet.user_id ==f"{user_id}",Tweet.in_reply_to_user_id==f"{user_id}")
        )).all()
        print(reply_tweets)
        return reply_tweets
       
    def get_retweets(self, user_id: int)->list[Tweet]:
        retweets=self.session.scalars(base_query.where(Tweet.retweet_original_user_id != None).where(
            or_(Tweet.user_id ==f"{user_id}",Tweet.retweet_original_user_id==f"{user_id}")
        )).all()
        return retweets
    def calculate_interaction_score(self,retweets:list[Tweet], replies: list[Tweet], user_id:int)->dict[int, int]:

        user_id=str(user_id)
        interaction_score={}
        retweets_user=[tweet.user_id if tweet.user_id != user_id else tweet.retweet_original_user_id for  index, tweet in enumerate(retweets)]
        replies_user=[tweet.user_id if tweet.user_id!=user_id else tweet.in_reply_to_user_id for  index, tweet in enumerate(replies)]
        all_user_from_retweets_and_reply=set(retweets_user+replies_user)
        for other_user_Id in all_user_from_retweets_and_reply:
            total_reply_interaction=len([tweet for tweet in replies if (tweet.user_id==other_user_Id and tweet.in_reply_to_user_id==user_id) or(tweet.user_id==user_id and tweet.in_reply_to_user_id==other_user_Id )])
            total_retweet_interaction=len([tweet for tweet in retweets if (tweet.user_id==other_user_Id and tweet.retweet_original_user_id==user_id) or(tweet.user_id==user_id and tweet.retweet_original_user_id==other_user_Id )])
            print(total_retweet_interaction, len(retweets))
            interaction_score[other_user_Id]= math.log(1+ 2*total_reply_interaction+total_retweet_interaction)

        print(interaction_score)
        return interaction_score
    def calculate_hashtag_score(self,user_id:str, excluded_hashtags: list[str])->dict[int, int]:
        excluded_hashtags = [hashtag.lower() for hashtag in excluded_hashtags]
        tweet_with_hashtags =self.session.scalars(base_query.where(Tweet.user_id == f"{user_id}").where(TweetHashTag.hashtag.not_in(excluded_hashtags)).join(TweetHashTag)).all()
    
        user_hashtags = [hashtag.__dict__.get("hashtag") for tweet in tweet_with_hashtags for hashtag in tweet.hashtags]
        user_hashtags=list(set(user_hashtags))
        if not user_hashtags:
            return {}
    

        matching_tweets = self.session.query(Tweet).join(TweetHashTag).filter(TweetHashTag.hashtag.in_(user_hashtags)).all()
        
        user_tweet_counts = {}
        for tweet in matching_tweets:
            for hashtag in tweet.hashtags:
                if hashtag.__dict__.get("hashtag") in user_hashtags:
                    user_tweet_counts[tweet.user_id] = user_tweet_counts.get(tweet.user_id, 0) + 1
        
    
        scores = {}
        for user, count in user_tweet_counts.items():
            if count > 10:
                score = 1 + math.log(1 + count - 10)
            else:
                score = 1
            scores[user] = score
        
        return scores
  


    def calculate_keyword_score(self, phrase:str, hashtag:str, tweet_type='both') -> dict[int, int]:
        
        query = select(Tweet).join(TweetHashTag)
        
        if tweet_type == 'reply':
            query = query.where(Tweet.in_reply_to_user_id.isnot(None))
        elif tweet_type == 'retweet':
            query = query.where(Tweet.retweet_original_user_id.isnot(None))
        elif tweet_type == 'both':
            query = query.where(or_(Tweet.in_reply_to_user_id.isnot(None), Tweet.retweet_original_user_id.isnot(None)))
        
        query=query.where(or_(Tweet.text.contains(phrase), TweetHashTag.hashtag.ilike(f"%{hashtag}%"), ))
        tweets = self.session.scalars(query).all()
        print(len(tweets))
    
        keyword_scores ={} 
    
        def count_phrase_occurrences(text, phrase):
            count = 0
            start = 0
            while start < len(text):
                start = text.find(phrase, start)
                if start == -1:
                    break
                count += 1
                start += 1  # Move to the next character to allow overlapping matches
            return count
    
        for tweet in tweets:
            text = tweet.text
            hashtags = [h.__dict__.get("hashtag").lower() for h in tweet.hashtags]
        
            phrase_matches = count_phrase_occurrences(text, phrase)
            if phrase_matches > 0:
                keyword_scores[tweet.user_id] =keyword_scores.get(tweet.user_id,0) +phrase_matches
        
            hashtag_matches = hashtags.count(hashtag.lower())
            if hashtag_matches > 0:
                keyword_scores[tweet.user_id] = keyword_scores.get(tweet.user_id,0) +hashtag_matches
        for user, matches in keyword_scores.items():
            keyword_scores[user] = 1 + math.log(matches + 1)
        return dict((user, score) for user, score in keyword_scores.items() if score > 0)
    def get_recommended_users(self, user_id:int,type:str, phrase: str, hashtag: str):
        user=self.get_user(user_id)
        interaction_score={}
        hashtag_score={}
        if not user:
            return []
        
        retweets=self.get_retweets(user_id)
        replies=self.get_reply(user_id)
        popular_hashtags=self.get_popular_hashtags()
        if user:
            interaction_score=self.calculate_interaction_score(retweets, replies, user_id)
            hashtag_score=self.calculate_hashtag_score(user_id, [hashtag.hashtag for hashtag in popular_hashtags])
        same_keywords_score=self.calculate_keyword_score(phrase, hashtag)
        interacted_users=[key for key in enumerate(interaction_score) ]
        same_hashtag_users=[key for key in enumerate(hashtag_score) ]
        same_keywords_user=[key for key in enumerate(same_keywords_score)]
        recomendable_user_id=set(interacted_users+same_hashtag_users+same_keywords_user)
        users=[]
        for index,user_id in recomendable_user_id:
            user=self.get_user(user_id)
            score=interaction_score.get(user_id, 0)*hashtag_score.get(user_id, 0)*self.calculate_keyword_score(user_id, phrase, hashtag).get(user_id, 0)
            if user:
                users.append({"user": user.__dict__, "score": score})
        # sort user by score
        users=sorted(users, key=lambda x: x['score'], reverse=True)
        return users