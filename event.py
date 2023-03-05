import slack 
import os
from dotenv import load_dotenv
from datetime import date
import time
from flask import Flask
from slackeventsapi import SlackEventAdapter

# ngrok http 5000 
# it expires in two hours!!!
env_path = ".env"
load_dotenv(env_path)

# intiate the app
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],"/slack/events",app) # all events sent to this endpoint

# initiate client
client= slack.WebClient(os.environ['SLACK_BOT_TOKEN'])

# make a function that will send a message upon a command
@slack_event_adapter.on('message') # use to handle on "message" event
def message(payLoad):
    print(payLoad) # this is the info that the api returns to us 
    # payLoad variable is data that the slack api sends to us
    
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('channel') # give you the channel id
    user_id = event.get('user') # get the user id 
    text = event.get('text') #grab text

    # check if user id is equal to bot id that way the bot doesn't end up replying to itself
    BOT_ID = client.api_call("auth.test")['user_id']

    if BOT_ID != user_id:
        # echo back to user what they send us 
        client.chat_postMessage(channel=channel_id,text=text)

# message_counts = {}
# @slack_event_adapter.on('message') # use to handle on "message" event
# def message(payLoad):
#     print(payLoad) # this is the info that the api returns to us 
#     # payLoad variable is data that the slack api sends to us
    
#     event = payLoad.get('event',{}) # look for key event inside payload/data
#     channel_id = event.get('channel') # give you the channel id
#     user_id = event.get('user') # get the user id 
#     text = event.get('text') #grab text

#     if user_id in message_counts:
#         message_counts[user_id] +=1
#     else:
#         message_counts[user_id] = 1
#    print('done')

if __name__ == "__main__":
    app.run(debug=True)