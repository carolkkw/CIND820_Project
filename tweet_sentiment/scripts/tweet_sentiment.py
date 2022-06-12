#!/usr/bin/python3

import os
import csv
import json
import argparse
import logging
import logging.config

from enum import Enum
from textblob import TextBlob

# User Defined Classes
from tweet_data import TweetData, TweetDB
from parameters import Parameters

log = logging.getLogger('TweetSentiment')
parameters = Parameters.get_parameter_obj('TweetSentiment')

class Execute() :
    """
    This class responsible for calling the right function based on the user
    action list.
    """
    tweet_db_obj = None
    tweet_data_obj = None

    class CmdList(Enum) :
        GET = 1
        APPEND = 2
        ANALYZE = 3

    @staticmethod
    def _get_tweets() :
        log.debug("GET TWEETS")
        print(Execute.tweet_data_obj.get_recent_tweets())

    @staticmethod
    def _append_tweets() :
        log.debug("APPEND TWEETS")
        tweet_db.append(Execute.tweet_data_obj.get_recent_tweets())

    @staticmethod
    def _analyze_tweets() :
        log.debug("ANALYZE TWEETS")
        TweetSentiment.export(Execute.tweet_db_obj)

    @classmethod
    def init (cls, tweet_db_obj, tweet_data_obj) :
        cls.tweet_db_obj = tweet_db_obj
        cls.tweet_data_obj = tweet_data_obj

    @staticmethod
    def run(command_list) :
        # Look up table for the corresponding function based on action
        execute_table = {
            Execute.CmdList.GET : Execute._get_tweets,
            Execute.CmdList.APPEND : Execute._append_tweets,
            Execute.CmdList.ANALYZE : Execute._analyze_tweets,
        }

        for cmd in command_list :
            log.info("EXECUTE ACTION - %s", cmd)
            execute_function = Execute.CmdList[cmd]
            execute_table[execute_function]()

class TweetSentiment() :
    class ExportFormat(Enum) :
        CSV = 0
        JSON = 1

    @staticmethod
    def _export_json(data, filename, fields, encoding) :
        log.debug("EXPORT JSON")
        values = lambda key : [ item[key] for item in data ]
        db_export = { x : values(x) for x in fields }
        with open(filename, "w", encoding=encoding) as json_file :
            json.dump(db_export, json_file)

    @staticmethod
    def _export_csv(data, filename, fields, encoding="ascii") :
        """
        This method export the Tweet with Sentiment value in CSV format
        """
        log.debug("EXPORT CSV")
        with open(filename, "w", encoding=encoding) as csv_file :
            db_export = csv.DictWriter(csv_file, fieldnames=fields)
            db_export.writeheader()
            for item in data :
                db_export.writerow(item)

    @staticmethod
    def export(tweet_db_obj) :
        export_format = parameters.export['format']
        export_file = os.path.expandvars(parameters.export['file'])
        export_fields = parameters.export['fields']
        export_encoding = parameters.export['encoding']
        log.info("EXPORT TWEET (%s) export_file=%s", export_format, export_file)

        export_function = {
            TweetSentiment.ExportFormat.CSV : TweetSentiment._export_csv,
            TweetSentiment.ExportFormat.JSON : TweetSentiment._export_json
        }

        db_data = tweet_db_obj.get()
        for item in db_data :
            textblob = TextBlob(item['text'])
            item['polarity'] = textblob.sentiment.polarity
            item['subjectivity'] = textblob.sentiment.subjectivity
        export_format = TweetSentiment.ExportFormat[export_format]
        export_function[export_format](
            db_data,
            export_file,
            export_fields,
            export_encoding)


if __name__ == "__main__" :
    # Parsing Configuration
    parser = argparse.ArgumentParser(
                description="Getting Tweet and assign polarity")
    parser.add_argument(
                "--verbose",
                help="Turn on logging",
                action="store_true")
    parser.add_argument(
                "--log-level", "--log_level",
                help="Specify the verbose level",
                action="store", type=str, default="INFO")
    parser.add_argument(
                "--log-config", "--log_config",
                help="Specify the logging configuration file",
                action="store", type=str)
    parser.add_argument(
                "--db",
                help="Specific the location of tweet database",
                action="store", type=str, default="${DATA_PATH}/tweets_db.json")
    parser.add_argument(
                "--config",
                help="Specific the configuration files",
                action="store",
                type=str, default="${ETC_PATH}/config.json" )
    parser.add_argument(
                "--action",
                help="Specific the action for the script",
                choices=["GET", "APPEND", "ANALYZE"],
                action="append")
    parser.add_argument(
                "--sim-tweet", "--sim_tweet",
                help="Simulate return from Twitter API",
                action="store_true")

    args = parser.parse_args()

    # Loading parameters
    parameters.load(os.path.expandvars(args.config))

    # Setup logging
    if args.verbose :
        if args.log_config is None :
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                level=args.log_level)
        else :
            try :
                log_file_name = os.path.expandvars(parameters.log_file)
                logging.config.fileConfig(
                    args.log_config,
                    defaults={ 'log_file_name' : log_file_name } )
                log.info("Log filename: %s", log_file_name)
                log.info("Using Log Configuration File: %s", args.log_config)

            except Exception as exception :
                log.warning("Cannot load log configuration \"%s\"", args.log_config)

    # Create TweetData and Tweet Database object
    tweet_data = TweetData.get_tweet_obj(args.sim_tweet)
    tweet_db = TweetDB(os.path.expandvars(args.db))

    Execute.init(tweet_db, tweet_data)
    Execute.run(args.action)
