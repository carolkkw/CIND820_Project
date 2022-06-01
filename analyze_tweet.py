#!/usr/bin/python3

# import libraries
import tweepy as tp
import pprint
import pandas as pd 
import matplotlib as mpl
import matplotlib.pyplot as plt
import json
from tweepy.streaming import Stream
import sys
import os
import string
import time
from tweepy import Stream
import nltk
from nltk.corpus import stopwords
import sys,tweepy,csv,re
from textblob import TextBlob

from bokeh.io import output_file, show
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum

from stop_words import get_stop_words

from textblob_fr import PatternTagger, PatternAnalyzer
from textblob_de import TextBlobDE

from bokeh.plotting import figure
from bokeh.io import output_notebook, show, curdoc
from bokeh.models import ColumnDataSource, Select
from bokeh.models.glyphs import Line
from bokeh.models.widgets import Tabs, Panel
from bokeh.layouts import row

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms,modes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

nltk.download('stopwords')
nltk.download('punkt')

class data:
    
    #Streams netflix and disney+ tweets in USA and Europ and stors it in a csv file
    def stream(self):
        
        geo_usa = "40.68908,-100.95860,1500km"
        geo_europe = "51.18348,10.03954,1200km"
        
        self.get_tweets("netflix", 140000, geo_usa, "europe", "en", "eng_usa")
        self.get_tweets("netflix", 140000, geo_europe, "europe", "en", "eng_europe")
        self.get_tweets("netflix", 140000, geo_europe, "europe", "fr", "fr_europe")
        self.get_tweets("netflix", 140000, geo_europe, "europe", "de", "ger_europe")
        self.get_tweets("netflix", 140000, geo_europe, "europe", "it", "it_europe")
        self.get_tweets("disneyplus", 140000, geo_usa, "europe", "en", "eng_usa")
        self.get_tweets("disneyplus", 140000, geo_europe, "europe", "en", "eng_europe")
        self.get_tweets("disneyplus", 140000, geo_europe, "europe", "fr", "fr_europe")
        self.get_tweets("disneyplus", 140000, geo_europe, "europe", "de", "ger_europe")
        self.get_tweets("disneyplus", 140000, geo_europe, "europe", "it", "it_europe")
    
    #Stream function
    def get_tweets(self, hashtag, count, geo, loc, lang, lang_loc):
        
        consumer_key = '5tAL60fZz0h2Njpew8VXCRTE7'
        consumer_secret = '30AeKoa6kJ3n8R1we0DcdSlKB01PbycSvNh7ERuazjELrHFFA6'
        access_token = '1531517732340080641-uaziVZ59u0fTZInYW7lpkIY80nO3BP'
        access_token_secret = 'dMHGnMxTfl6ihlxsfEKr8RUfV9e3RQrqCA3KKsQraCzBO'

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth,wait_on_rate_limit=True)	

    	#csvFile = open('df.csv', 'a', newline='')
	
	csvFile = open('df.csv')

        csvWriter = csv.writer(csvFile)

        for tweet in tweepy.Cursor(api.search,q="netflix", count=count, lang=lang, since="2022-04-01", until="2022-04-30", geocode=geo).items():
            print (tweet.created_at, tweet.text)
            csvWriter.writerow([tweet.created_at, tweet.text.encode('utf-8'), loc, hashtag, lang_loc])
    
    #import data from csv file
    def import_data(self):
        
        df = pd.read_csv("df.csv", names =["date", 'text', 'location', 'hashtag', 'lang_loc'])
        return df
    
    #preprocessing the dataframe 
    def data_preproc(self, df):
        
        df.lang_loc.fillna('eng_usa', inplace=True)
        df['date']=pd.to_datetime(df['date'])
        df=df.drop_duplicates(['text'])
        df.set_index('date', inplace=True)
        df=df.sort_values(by=['hashtag', 'date', 'location', 'lang_loc'])
        df = df.drop(df[df["lang_loc"]=="it_europe"].index)
        return df
    
    #preprocessing the tweets : removing stopwords and punctuation in each langage using text_process function bellow
    def new_text(self, df):
        
        new_text=[]
        
        for (tweet, lang_loc) in zip(df.text, df.lang_loc):
            
            if ((lang_loc == "eng_usa") | (lang_loc == "eng_europe")):
                new_tweet = self.text_process(tweet, "en")
                new_text.append(new_tweet)
                
            elif (lang_loc == "fr_europe"):
                new_tweet = self.text_process(tweet, "fr")
                new_text.append(new_tweet)
                
            elif (lang_loc == "it_europe"):
                new_tweet = self.text_process(tweet, "it")
                new_text.append(new_tweet)
                
            elif (lang_loc == "ger_europe"):
                new_tweet = self.text_process(tweet, "de")
                new_text.append(new_tweet)
                
        return new_text
    
    def text_process(self, mess, lang):
        
        stopwords=get_stop_words(lang)
        mess = [i for i in mess if i not in string.punctuation]
        mess = "".join(mess)
        mess = "".join(mess.split("b", 1))
        str1= " "
        return (str1.join([i for i in mess.split(" ") if (i.lower() not in stopwords)]))
    
    #calculate the polarity of each tweet in each langage
    def tweet_polarity(self, df):
        
        polarity = []
        for (tweet, lang) in zip(df.new_text, df["lang_loc"]):
            if ((lang == "eng_usa") | (lang == "eng_europe")):
                analysis = TextBlob(tweet)
                polarity.append(analysis.sentiment.polarity)
                
            elif (lang == "fr_europe"):
                analysis = TextBlob(tweet, pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
                polarity.append(analysis.sentiment[0])
                
            elif (lang == "ger_europe"):
                analysis = TextBlobDE(tweet)
                polarity.append(analysis.sentiment.polarity)
                        
        return polarity 

# Data Preparation
data=data()
df=data.import_data()
df=data.data_preproc(df)
df["new_text"]=data.new_text(df)
polarity=data.tweet_polarity(df)
df["tweet_polarity"] = polarity

# Tweet Encryption
key = os.urandom(32)
file = open('key.key', 'wb')  
file.write(key) 
file.close()
cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
aesEncryptor = cipher.encryptor()
tweets_encry=[]

for tweet in df["new_text"]:
    tweet_encry = tweet.encode("utf-16") + b"E" * (-len(tweet) % 16) 
    tweet_encry = aesEncryptor.update(tweet_encry)
    tweets_encry.append(tweet_encry)
    
df["text_encrypted"]=tweets_encry
df=df.drop(['text', 'new_text'], axis=1)
df.head()
df.info()
df.to_csv(r'df_prepared.csv')
