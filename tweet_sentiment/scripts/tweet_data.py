#!/usr/bin/python3

# System modules
import os
import re
import logging

# import libraries
import pandas as pd
import tweepy
from tinydb import TinyDB, Query

# User libraries
from parameters import Parameters

log = logging.getLogger('TweetSentiment')
parameters = Parameters.get_parameter_obj('TweetSentiment')

class TweetData:
    @classmethod
    def get_tweet_obj(cls, sim_tweet) :
        log.debug("get_tweet_obj sim_tweet=%s", sim_tweet)
        tweet_data_obj = None
        if sim_tweet :
            tweet_data_obj = TweetDataSim()
        else :
            tweet_data_obj = TweetDataLive()

        return tweet_data_obj

    def __init__(self) :
        """
        Class Constructor
        """
        log.debug("Creating TweetData object")

    def get_recent_tweets(self) :
        query_list = parameters.tweet_data['query_list']
        max_size = parameters.tweet_data['max_result']
        result = pd.DataFrame()
        for query in query_list :
            tweet_fetch = self._get_recent_tweets(query, max_size)
            result = pd.concat([result, tweet_fetch], ignore_index=True)
        return result

class TweetDataLive(TweetData) :
    def __init__(self) :
        super().__init__()
        log.info("Createing Tweepy Client")
        live_tweet_parameters = parameters.tweet_data['live_tweet']
        oauth_parameters = Parameters.get_parameter_obj('oauth')
        oauth_parameters.load(live_tweet_parameters['oauth_config'])

        # Create the client if it is not created.
        self._client = tweepy.Client(
                            bearer_token=oauth_parameters.bearer_token,
                            consumer_key=oauth_parameters.consumer_key,
                            consumer_secret=oauth_parameters.consumer_secret,
                            access_token=oauth_parameters.access_token,
                            access_token_secret=oauth_parameters.access_token_secret)


    def _get_recent_tweets(self, query, max_size) :
        live_tweet_parameters = parameters.tweet_data['live_tweet']
        log.info("TweetDataLive._get_recent_tweets(): %s (max_size=%d)", query, max_size)
        # Base on the max_result, use the appropriate API (no page or page)
        data_frame = None

        if max_size <= live_tweet_parameters['page_limit'] :
            tweets = self._client.search_recent_tweets(
                query=query,
                tweet_fields=live_tweet_parameters['fields'],
                max_results=max_size)
            data_frame = pd.DataFrame(tweets.data, columns=[ 'id', 'text'])
            data_frame.insert(
                loc=0,
                column='created_at',
                value=[ tweet.created_at for tweet in tweets.data ])
        else :
            tweets = tweepy.Paginator(
                            self._client.search_recent_tweets,
                            query=query,
                            tweet_fields=live_tweet_parameters['fields'],
                            max_results=live_tweet_parameters['page_limit']).flatten(limit=max_size)
            data_frame = pd.DataFrame(tweets)

        # Convert to JSON time string for TinyDB
        data_frame['created_at'] = data_frame['created_at'].dt.strftime("%m/%d/%Y %H:%M")
        data_frame['query'] = pd.Series([ query for i in range(len(data_frame.index))])

        return data_frame

class TweetDataSim(TweetData) :
    def _get_recent_tweets(self, query, max_size) :
        """
        The function simulate the Tweeter API return from a local file.
        """
        sim_tweet_parameters = parameters.tweet_data['sim_tweet']
        filename = os.path.expandvars(sim_tweet_parameters['file'])
        fields = sim_tweet_parameters['fields']
        log.info("TweetDataSim._get_recent_tweets() from filename %s : %s (max_size=%d)",
            filename,
            query,
            max_size)
        data_frame = pd.read_csv(filename, names=fields)
        result_df = data_frame.loc[data_frame['query'] == query]
        result = result_df.head(max_size)
        log.debug(result)
        return result

class TweetDB() :
    """
    This class handle the tweet database
    """
    @staticmethod
    def update_query_str(query_str) :
        def transform(doc) :
            log.debug("Update doc 'query' with query_str: %s %s", query_str, doc)
            if not re.search(query_str, doc['query']) :
                log.debug("Appending query string")
                doc['query'] = doc['query'] + "; " + query_str
            else :
                log.debug("Matching query string.  Do nothing")

        return transform

    def __init__(self, db_file) :
        """
        Constructor for TweetDB
        """
        log.debug("Creating TweetDB Object")
        self._db = TinyDB(db_file)

    def append(self, dataframe) :
        """
        This function get the tweet using the TweetData class, and append new
        tweet in TinyDB.

        If the tweet already exist, the function append the value of query in
        the query column

        For each tweet
            If tweet id exist, append query string in query field
                If the query field not exist
                    append the query string
                Else
                    do nothing
            Else
                add the tweet in the db
        """
        log.info("TweetDB.append")
        no_record_add = 0
        no_record = len(dataframe)
        query = Query()

        for index, row in dataframe.iterrows() :
            log.debug("Searching DB for %s", row['id'])
            result = self._db.search(query.id == row['id'])
            if len(result) :
                self._db.update(TweetDB.update_query_str(row['query']), query.id == row['id'])
            else :
                add_record = {
                    "created_at" : row['created_at'],
                    "id" : row['id'],
                    "text" : row['text'],
                    "query" : row['query']
                }
                log.debug("Add Record %s", add_record)
                no_record_add = no_record_add + 1
                self._db.insert(add_record)
        log.info("TweetDB.append %d/%d records added", no_record_add, no_record)

    def get(self) :
        log.debug("TweetDB.get")
        return self._db.all().copy()
