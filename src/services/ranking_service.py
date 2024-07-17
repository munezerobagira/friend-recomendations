import math
from sqlalchemy import  ScalarResult, or_
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models import User, Tweet,PopularHashtag



class RankingService:
    def __init__(self, session:Session):
        self.session: Session=session

    def get_user(self, user_id: int)->User:
        user=self.session.scalars(select(User).where(User.user_id==f"{user_id}")).first()
        return user
    def get_reply(self, user_id: int):

        reply_tweets=self.session.scalars(select(Tweet).where(Tweet.in_reply_to_user_id != None).where(
            or_(Tweet.user_id ==f"{user_id}",Tweet.in_reply_to_user_id==f"{user_id}")
        )).all()
        return reply_tweets
       
    def get_retweets(self, user_id: int):
        retweets=self.session.scalars(select(Tweet).where(Tweet.retweet_original_user_id != None).where(
            or_(Tweet.user_id ==f"{user_id}",Tweet.retweet_original_user_id==f"{user_id}")
        )).all()
        return retweets
    def calculate_interaction_score(self,retweets:ScalarResult[Tweet], replies: ScalarResult[Tweet], user_id:int)->dict[int, int]:
        user_id=str(user_id)
        interaction_score={}
        retweets_user=[tweet.user_id if tweet.user_id != user_id else tweet.retweet_original_user_id for  index, tweet in enumerate(retweets)]
        replies_user=[tweet.user_id if tweet.user_id!=user_id else tweet.in_reply_to_user_id for  index, tweet in enumerate(replies)]
        print(replies_user)
        all_user_from_retweets_and_reply=set(retweets_user+replies_user)
        for other_user_Id in all_user_from_retweets_and_reply:
            total_reply_interaction=len([tweet for tweet in replies if (tweet.user_id==other_user_Id and tweet.in_reply_to_user_id==user_id) or(tweet.user_id==user_id and tweet.in_reply_to_user_id==other_user_Id )])
            total_retweet_interaction=len([tweet for tweet in retweets if (tweet.user_id==other_user_Id and tweet.retweet_original_user_id==user_id) or(tweet.user_id==user_id and tweet.retweet_original_user_id==other_user_Id )])
            print(total_retweet_interaction, len(retweets))
            interaction_score[other_user_Id]= math.log(1+ 2*total_reply_interaction+total_retweet_interaction)
        return interaction_score
    def calculate_hashtag_score(self,user_id:str, excluded_hashtags=list[str])->dict[int, int]:
        user_hashtags =self.session.query(Tweet.hashtags).filter(Tweet.user_id == f"{user_id}").all()
        user_hashtags = [hashtag for sublist in user_hashtags for hashtag in sublist]
        user_hashtags = [hashtag.lower() for hashtag in user_hashtags if hashtag.lower() not in excluded_hashtags]
        
        if not user_hashtags:
            return 0
        matching_tweets =self. session.query(Tweet).filter(
            Tweet.hashtags.any(func.lower(func.json_extract(Tweet.hashtags, '$[*]')).in_(user_hashtags))
        ).all()
        
        # Step 3: Group tweets by user_id
        user_tweet_counts = {}
        for tweet in matching_tweets:
            for hashtag in tweet.hashtags:
                if hashtag.lower() in user_hashtags:
                    user_tweet_counts[tweet.user_id] = user_tweet_counts.get(tweet.user_id, 0) + 1
        
        # Step 4: Calculate hashtag scores for each user
        scores = {}
        for user, count in user_tweet_counts.items():
            if count > 10:
                score = 1 + math.log(1 + count - 10)
            else:
                score = 1
            scores[user] = score
        
        return scores
  
    def calculate_keyword_score(self,user_id, phrase, hashtag, tweet_type='both')->dict[int, int]:
    # Prepare the query for tweets based on type
        query = self.session.query(Tweet)
        
        if tweet_type == 'reply':
            query = query.filter(Tweet.in_reply_to_user_id.isnot(None))
        elif tweet_type == 'retweet':
            query = query.filter(Tweet.retweeted_status.isnot(None))
        elif tweet_type == 'both':
            query = query.filter(or_(Tweet.in_reply_to_user_id.isnot(None), Tweet.retweeted_status.isnot(None)))
        
        # Get tweets
        tweets = query.all()
        
        # Initialize score
        keyword_score = {}
        
        # Count phrase and hashtag occurrences
        for tweet in tweets:
            text = tweet.text.lower()
            hashtags = [h.lower() for h in tweet.hashtags]
            
            # Phrase matches
            phrase_matches = text.count(phrase.lower())
            keyword_score += phrase_matches
            
            # Hashtag matches
            hashtag_matches = hashtags.count(hashtag.lower())
            keyword_score += hashtag_matches

        return keyword_score
    def get_recommended_users(self, user_id:int,type:str, phrase: str, hashtag: str):
        user=self.get_user(user_id)
        retweets=self.get_retweets(user_id)
        replies=self.get_reply(user_id)
        interaction_score=self.calculate_interaction_score(retweets, replies, user_id)
        hashtag_score=self.calculate_hashtag_score(user_id, [hashtag])
        same_keywords_score=self.calculate_keyword_score(user_id, phrase, hashtag)
        interacted_users=[key for key in enumerate(interaction_score) ]
        same_hashtag_users=[key for key in enumerate(hashtag_score) ]
        same_keywords_user=[key for key in enumerate(same_keywords_score)]
        recomendable_user_id=set(interacted_users+same_hashtag_users+same_keywords_user)
        users=[
        ]
        for user_id in recomendable_user_id:
            user=self.get_user(user_id)
            score=interaction_score.get(user_id, 0)*hashtag_score.get(user_id, 0)*self.calculate_keyword_score(user_id, phrase, hashtag).get(user_id, 0)
            if user:
                users.append({"user": user.__dict__, "score": score})
        # sort user by score
        users=sorted(users, key=lambda x: x['score'], reverse=True)
        return users