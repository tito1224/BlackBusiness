import slack 
import os
from dotenv import load_dotenv
from datetime import date
import time
from flask import Flask


env_path = ".env"
load_dotenv(env_path)

# initiate client
client= slack.WebClient(os.environ['SLACK_BOT_TOKEN'])

# get bot to send a message

#client.chat_postMessage(channel="test",text="HELLOOOO")

# get the bot to tell you the time

t = time.localtime()
current_time = time.strftime("%H:%M:%S",t) # format time
client.chat_postMessage(channel="test",text="The current date is" + str(date.today())+str(current_time))



