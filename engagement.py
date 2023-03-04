import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])

# make a function that will send a welcome message when a user joins

BOT_ID = client.api_call("auth.test")['user_id']

@slack_event_adapter.on('member_joined_channel') #function has bot collcet information on message from user
def message(payload):
    print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user') #Tito will establish user's NAME rather than ID
    text = event.get('text')
    

    if channel_id == "C04T3JPMCGG":
        client.chat_postMessage(channel=channel_id, text='Hello ' + user_id +' hope you enjoy your stay')
    
    # if BOT_ID != user_id:
    #     client.conversations_join(channel='C04T3JPMCGG',text='Welcome!')
    
        # client.chat_postMessage(channel=channel_id, text='Hello ' + user_id +' hope you enjoy your stay')
    

if __name__ == "__main__":
    app.run(debug=True)




# make a function that will give them tasks to do 



# make a function that will give the users points when they do the tasks


# make a function that direct-messages the users with whether they earned points or not


# make a function that will show a leaderboard of who is winning if you use a certain command



# make a function that will ask users for the URL for their products, and post it to the channel of consumers 
# if they are in the top percentile




################### CONSUMERS SIDE ##########################

# make a function that will welcome them to the channel 


# make a function that will ask them to poll on what kind of products they would like to see

