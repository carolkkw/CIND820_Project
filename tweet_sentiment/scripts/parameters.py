#!/usr/bin/python3
import os
import json
import logging

log = logging.getLogger('TweetSentiment')

class Parameters() :
    para_obj = {}

    @classmethod
    def get_parameter_obj(cls, name) :
        if name not in Parameters.para_obj :
            Parameters.para_obj[name] = Parameters(name)
        return Parameters.para_obj[name]

    def __init__(self, name) :
        self._name = name

    def load(self, filename_str) :
        """
        This is the function that load the JSON file and store them as an attribute of the object
        """
        filename = os.path.expandvars(filename_str)
        log.info("Loading %s parameters from: %s", self._name, filename)

        with open(filename, encoding="ascii") as json_file :
            json_data = json.load(json_file)

        for item in json_data.items() :
            setattr(self, item[0], item[1])
