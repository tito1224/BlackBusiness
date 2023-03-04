import slack 
import os
from dotenv import load_dotenv
from datetime import date
import time
from flask import Flask
from slackeventsapi import SlackEventAdapter

# show how to use /commands inside of slack 

env_path = ".env"
load_dotenv(env_path)

# intiate the app
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],"/slack/events",app) # all events sent to this endpoint

# initiate client
client= slack.WebClient(os.environ['SLACK_BOT_TOKEN'])
