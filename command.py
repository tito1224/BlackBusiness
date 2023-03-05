import slack 
import os
from dotenv import load_dotenv
from datetime import date
import time
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

# show how to use /commands inside of slack 

env_path = ".env"
load_dotenv(env_path)

# intiate the app
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],"/slack/events",app) # all events sent to this endpoint

# initiate client
client= slack.WebClient(os.environ['SLACK_BOT_TOKEN'])

# command to see how many messages a user sent
message_counts = {} # store user id and no messages sent
# ideally would put message counts in a database!!!

# check if user id is equal to bot id that way the bot doesn't end up replying to itself
BOT_ID = client.api_call("auth.test")['user_id']


# make a function that will send a message upon a command
@slack_event_adapter.on('message') # use to handle on "message" event
def message(payLoad):
    print(payLoad) # this is the info that the api returns to us 
    # payLoad variable is data that the slack api sends to us
    
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('channel') # give you the channel id
    user_id = event.get('user') # get the user id 
    text = event.get('text') #grab text

    if user_id in message_counts:
        message_counts[user_id] +=1
    else:
        message_counts[user_id] = 1
    print('done')

@app.route('/message-count',methods=['POST'])
def message_count():
    data = request.form # dictionary of key value pairs sent
    print(data)
    user_id = data.get("user_id") # grab the user_id
    channel_id = data.get('channel_id')
    strMessage = message_counts.get(user_id,0) # get the user_id or else return 0
    client.chat_postMessage(channel=channel_id,text=f"You have written {strMessage} messages so far.")
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True)