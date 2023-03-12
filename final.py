import slack 
import os
from dotenv import load_dotenv
from datetime import date
import time
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import pandas as pd
import cohere
from cohere.classify import Example
import json
import itertools

# show how to use /commands inside of slack 

env_path = ".env"
load_dotenv(env_path)

# intiate the app
app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],"/slack/events",app) # all events sent to this endpoint

# initiate client
client= slack.WebClient(os.environ['SLACK_BOT_TOKEN'])
# grab bot id
BOT_ID = client.api_call("auth.test")['user_id']

# store user id and messages sent
message_counts = {} 
reaction_counts = {}
dictScoreCount = {}
dictClient = {}
topThree = sorted(dictScoreCount.items(), key=lambda x:x[1]) 

# store to check if people have done first few tasks
welcome_messages = {}
send_messages = {}
pt_messages = {}

# set a class so welcome message is sent as a DM
class WelcomeTask:
    START_TEXT = {
        'type': 'section',
        'text':{
            'type':'mrkdwn',
            'text':(
                'Welcome to this channel dedicated to helping black businessowners like you! '
                '*Get started by completing the following tasks:*'
            )
        }
    }

    POINT_TEXT = {
        'type': 'section',
        'text':{
            'type':'mrkdwn',
            'text':(
                f'Point update!'
            )
        }
    } 

    DIVIDER={'type':'divider'}

    def __init__(self,channel,user):
        self.channel = channel 
        self.user = user
        self.icon_emoji = ':robot_face:'
        self.timestamp = "" # update when we send the original message
        self.ReactCompleted = False # change to true when the user has completed the task
        self.MessageCompleted = False

    def get_message(self): #return message to use start text and divider
        return {
            'ts':self.timestamp,
            'channel':self.channel,
            'username':'Welcome!',
            'icon_emoji': self.icon_emoji,
            'blocks':[
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task(),
                self._get_message_task(),
                self.DIVIDER
            ]
        }
    
    # return points in DM's
    def get_pts(self): #return message to use start text and divider
        return {
            'ts':self.timestamp,
            'channel':self.channel,
            'username':'Update!',
            'icon_emoji': self.icon_emoji,
            'blocks':[
                self.POINT_TEXT,
                #self.DIVIDER,
                self._get_point_task()
            ]
        }

    def _get_reaction_task(self): # private method
        checkmark = ':white_check_mark:'
        if not self.ReactCompleted:
            checkmark = ':white_large_square:'
        
        text = f'{checkmark} *React to any message in a channel*'

        return {'type':'section','text':{'type':'mrkdwn','text':text}}

    def _get_message_task(self):
        checkmark = ':white_check_mark:'
        if not self.MessageCompleted:
            checkmark = ':white_large_square:'
        
        text = f'{checkmark} *Send a message to a channel that is more than 100 characters.*'

        return {'type':'section','text':{'type':'mrkdwn','text':text}}


    def _get_point_task(self):
        pts = dictScoreCount.get(self.user,0)
        text = f'*You have {pts} point(s) so far*'
        return {'type':'section','text':{'type':'mrkdwn','text':text}} 

# wrapper for welcome message to keep track of channel and user
# sends a welcome message when they join
def send_welcome_message(channel, user):
    welcome = WelcomeTask(channel,user)
    message = welcome.get_message()
    response = client.chat_postMessage(**message) #unpack operator for dictionaries
    welcome.timestamp= response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {} # store channels
    welcome_messages[channel][user] = welcome # store each of the users we sent a welcome message to

    

# send DM to user's when they gain points
def send_point_verification(channel, user):
    welcome = WelcomeTask(channel, user)
    pts = welcome.get_pts()
    response = client.chat_postMessage(**pts)
    welcome.timestamp = response['ts']
    welcome.points = response['points']

    if channel not in pt_messages:
        pt_messages[channel] = {} # store channels
    pt_messages[channel][user] = welcome # store each of the users we sent a welcome message to
    #print(welcome)

    # if channel not in send_messages:
    #     send_messages[channel] = {} # store channels
    # send_messages[channel][user] = welcome # store each of the users we sent a welcome message to

    # if channel not in welcome_messages:
    #     welcome_messages[channel] = {} # store channels
    # welcome_messages[channel][user] = welcome # store each of the users we sent a welcome message to


########## CLIENT FUNCTIONS #########

# make a function that will send a welcome message when a user joins
@slack_event_adapter.on('member_joined_channel') #function has bot collcet information on message from user
def member_join_channel(payload):
    print("member joined channel")
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user') #Tito will establish user's NAME rather than ID
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    text = event.get('text')

    #if channel_id == "C04T3JPMCGG":
    if channel_id == "C04T3HULG56": # tito's channel 
        client.chat_postMessage(channel=channel_id, text='Hello ' + userinfo +' hope you enjoy your stay')
        send_welcome_message(f"@{user_id}",userinfo)


# function to track reaction specifically for the intro channel 
@slack_event_adapter.on('reaction_added') # use to handle on "reaction" event
def reaction_added_intro(payLoad):
    print("updating react info")
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('item',{}).get('channel') # give you the channel id
    user_id = event.get('user') # get the user id 
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    text = event.get('text') #grab text

    if f'@{user_id}' not in welcome_messages:
        return 
    
    welcome = welcome_messages[f'@{user_id}'][userinfo]
    if welcome.ReactCompleted is not True:
        print("Updating React Task")
        # if user_id != None and BOT_ID!= user_id and channel_id != f'@{user_id}':
        #     if user_id in reaction_counts:
        #         reaction_counts[user_id] +=1
        #         dictScoreCount[user_id]+=1
        #     else:
        #         reaction_counts[user_id] = 1
        #         dictScoreCount[user_id] = 1 
        
        welcome = welcome_messages[f'@{user_id}'][userinfo]
        welcome.ReactCompleted = True
        #welcome.channel = channel_id # change channel for welcome message
        message = welcome.get_message()
        #updated_message = client.chat_update(**message)
        response = client.chat_postMessage(**message)

        #send_point_verification(f"@{user_id}",user_id)


# function to track reaction specifically for the intro channel 
@slack_event_adapter.on('message') # use to handle on "reaction" event
def message_added_intro(payLoad):
    print("Updating Message Task")
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('item',{}).get('channel') # give you the channel id
    user_id = event.get('user') # get the user id 
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    text = event.get('text') #grab text

    if f'@{user_id}' not in welcome_messages:
        return 
    
    if len(text)> 50:

        welcome = welcome_messages[f'@{user_id}'][userinfo]
        if welcome.MessageCompleted is not True:
            # if user_id != None and BOT_ID!= user_id and channel_id != f'@{user_id}':
            #     if user_id in reaction_counts:
            #         reaction_counts[user_id] +=1
            #         dictScoreCount[user_id]+=1
            #     else:
            #         reaction_counts[user_id] = 1
            #         dictScoreCount[user_id] = 1 
            
            welcome = welcome_messages[f'@{user_id}'][userinfo]
            welcome.MessageCompleted = True
            #welcome.channel = channel_id # change channel for welcome message
            message = welcome.get_message()
            #updated_message = client.chat_update(**message)
            response = client.chat_postMessage(**message)
            print("finished updating message task")

            #send_point_verification(f"@{user_id}",user_id)

# function to track when they use a react emoji to a message
@slack_event_adapter.on('reaction_added') # use to handle on "reaction" event
def reaction_added(payLoad):
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('item',{}).get('channel') # give you the channel id
    user_id = event.get('user') # get the user id 
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    
    #print(client.users_info(user=user_id).get('user'))
    text = event.get('text') #grab text

    if userinfo != None and BOT_ID!= user_id and channel_id == "C04T3HULG56":
        if userinfo in reaction_counts:
            reaction_counts[userinfo] +=1
        else:
            reaction_counts[userinfo] = 1
        
        if userinfo in dictScoreCount:
            dictScoreCount[userinfo] +=1
        else:
            dictScoreCount[userinfo] = 1
    
        #t = time.localtime()
        #current_time = time.strftime("%H:%M:%S",t) # format time
        #strDate = str(date.today())+str(current_time)
        #print(userinfo)
        #print(dictScoreCount)
        send_point_verification(f"@{user_id}",userinfo)
    print('done')

# function to track if they react to polls --> check if they access the poll within a certain timeframe

# make the bot dm to ask them about their preferences (i noticed you like x would you be interested in y?) -> give info to slalom employees


# function to track how many times they make a message
@slack_event_adapter.on('message') # use to handle on "message" event
def message(payLoad):
    #print(payLoad)
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('channel') # give you the channel id
    user_id = event.get('user') # get the user id
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    text = event.get('text') #grab text

    if userinfo != None and BOT_ID!= user_id and channel_id=="C04T3HULG56" and len(text)>50:
        if userinfo in message_counts:
            message_counts[userinfo] +=1
        else:
            message_counts[userinfo] = 1

        if userinfo in dictScoreCount:
            dictScoreCount[userinfo] +=1
        else:
            dictScoreCount[userinfo] = 1

        #t = time.localtime()
        #current_time = time.strftime("%H:%M:%S",t) # format time
        #strDate = str(date.today())+str(current_time)
        send_point_verification(f"@{user_id}",userinfo)
    
        print('finished adding a point for a message')

# make a command so that the user can see how many messages they have sent
@app.route('/message-count',methods=['POST'])
def message_count():
    data = request.form # dictionary of key value pairs sent
    #print(data)
    user_id = data.get("user_id") # grab the user_id
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    channel_id = data.get('channel_id')
    strMessage = message_counts.get(userinfo,0) # get the user_id or else return 0
    numMessagePoints= message_counts.get(userinfo,0)*1
    client.chat_postMessage(channel=channel_id,text=f"You have written {strMessage} messages so far, and have gained {numMessagePoints} points from messages so far.")
    return Response(), 200


# make a command so that the user can see how many messages they have sent
@app.route('/score-count',methods=['POST'])
def score_count():
    data = request.form # dictionary of key value pairs sent
    #print(data)
    user_id = data.get("user_id") # grab the user_id
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    channel_id = data.get('channel_id')
    strMessage = message_counts.get(userinfo,0) # get the user_id or else return 0
    numMessagePoints= message_counts.get(userinfo,0)*1

    totalPoints= reaction_counts.get(userinfo,0)*1 + message_counts.get(userinfo,0)*2

    client.chat_postMessage(channel=channel_id,text=f"You have the following points: {totalPoints}")
    return Response(), 200



# function to help with formatting winners
def score_leader_format(lstUse, position):
    if position > len(lstUse)-1:
        text = f'*Everyone else has {0} points*'
        return {'type':'section','text':{'type':'mrkdwn','text':text}}
    else:
        userPoint = lstUse[position]
        text = f'*{userPoint[0]} is in position {3-position} with {userPoint[1]} points.*'
        return {'type':'section','text':{'type':'mrkdwn','text':text}}
    

# make a function that will show a leaderboard of who is winning if you use a certain command
@app.route('/score-leader',methods=['POST'])
def score_leader():

    # find unique individuals in the channel 
    topThree = sorted(dictScoreCount.items(), key=lambda x:x[1])
    #print(topThree)
    data = request.form
    #print(data)
 
    #noOne = data[2]
    #noTwo = data[1]
    #noThree = data[0]

    BEGIN_TEXT = {
        'type': 'section',
        'text':{
            'type':'mrkdwn',
            'text':(
                'Here are the top winners so far!'
            )
        }
    }

    DIVIDER={'type':'divider'}

    if len(topThree) == 1:
        text = f'*{topThree[0][0]} is in position {1} with {topThree[0][1]} points.*'
        text= {'type':'section','text':{'type':'mrkdwn','text':text}}
        finalVal = {
                'ts':"",
                'channel': data.get("channel_id"),
                'username':'Welcome!',
                'icon_emoji': "::trophy::",
                'blocks':[
                    BEGIN_TEXT,
                    DIVIDER,
                    text,
                    DIVIDER
                ]
            }
    elif len(topThree) == 2:
        text1 = f'*{topThree[0][0]} is in position {2} with {topThree[0][1]} points.*'
        text1= {'type':'section','text':{'type':'mrkdwn','text':text1}}

        text2 = f'*{topThree[1][0]} is in position {1} with {topThree[1][1]} points.*'
        text2= {'type':'section','text':{'type':'mrkdwn','text':text2}}

        finalVal = {
                'ts':"",
                'channel': data.get("channel_id"),
                'username':'Welcome!',
                'icon_emoji': "::trophy::",
                'blocks':[
                    BEGIN_TEXT,
                    DIVIDER,
                    text2,
                    text1,
                    DIVIDER
                ]
            }

    else:
        finalVal = {
                'ts':"",
                'channel': data.get("channel_id"),
                'username':'Welcome!',
                'icon_emoji': "::trophy::",
                'blocks':[
                    BEGIN_TEXT,
                    DIVIDER,
                    score_leader_format(topThree, 2),
                    score_leader_format(topThree, 1),
                    score_leader_format(topThree, 0),
                    DIVIDER
                ]
            }
    
    response = client.chat_postMessage(**finalVal)
    return Response(), 200
    


# make a function that will ask users for the URL for their products, and post it to the channel of consumers 
# if they are in the top percentile



################### CONSUMERS SIDE ##########################

# make a function that will welcome them to the channel 


# make a function that will ask them to poll on what kind of products they would like to see

########## COHERE ###########

# make a function that will classify user questions
api_key = "eumHnf6tBVTk5wxNoRuRnYJQzbqwU00VNRQzL6mu"
co  = cohere.Client(api_key)

# set up example questions
examples=[
  Example("What hours are is the store open for?", "Operations"),
  Example("Is the store open on weekends?", "Operations"),
  Example("Is the store open after five pm on a saturday?", "Operations"),
  Example("How do I return a product", "Refunds   "),
  Example("Your product is horrible, and I want a refund", "Refunds   "),
  Example("I accidentally ordered the wrong thing. How do I get a refund", "Refunds   "),
  Example("Do you do catering", "Catering  "),
  Example("Can I sign up for to receive catering for my daughter's birthday", "Catering  "),
  Example("Will I be able to make purchases in bulk?", "Catering  "),
  Example("Is it possible to get discounts?", "Promotions"),
  Example("Do you guys have any discounts? This stuff is kind of expensive.", "Promotions"),
  Example("I have a coupon - how can I use this?", "Promotions")
  #Example("How do I check my claim status?", "Filing a claim and viewing status"),
  #Example("When will my claim be reimbursed?", "Filing a claim and viewing status"),
  #Example("I filed my claim 2 weeks ago but I still haven’t received a deposit for it.", "Filing a claim and viewing status"),
  #Example("I want to cancel my policy immediately! This is nonsense.", "Cancelling coverage"),
  #Example("Could you please help my end my insurance coverage? Thank you.",
  #"Cancelling coverage"),
  #Example("Your service sucks. I’m switching providers. Cancel my coverage.", "Cancelling coverage"),
  #Example("Hello there! How do I cancel my coverage?", "Cancelling coverage"),
  #Example("How do I delete my account?", "Cancelling coverage")
  ]

# function to track how many times they make a message
@slack_event_adapter.on('message') # use to handle on "message" event
def customer_messages(payLoad):
    event = payLoad.get('event',{}) # look for key event inside payload/data
    channel_id = event.get('channel') # give you the channel id
    user_id = event.get('user') # get the user id
    ts = event.get('ts')
    #convoresult = client.conversations_replies(channel=channel_id, ts = ts)
    #client_thread_id = convoresult.get('messages')[0].get('client_msg_id')
    #print(client_thread_id)
    userinfo = client.users_info(user=user_id).get('user').get('real_name')
    text = event.get('text') #grab text

    lstTopOwners = []
    print('topthree are')
    print(dictScoreCount)
    topPeople = sorted(dictScoreCount.items(), key=lambda x:x[1]) 
    for individual in topPeople:
        ind = individual[0]
        lstTopOwners.append(ind)
    lstTopOwners = [i.lower() for i in lstTopOwners]
    print(lstTopOwners)
    
    # if "question" in text.lower() and text.lower() not in lstTopOwners and BOT_ID!=user_id:
    #     client.chat_postMessage(channel=channel_id,thread_ts = ts,text=f"Hey {userinfo}! Thanks so much for your question. Please tag the owners so they can respond accordingly. Remember to use the word: 'question' and mention the owners in your query.")
    # elif "question" in text.lower() and text.lower() in lstTopOwners and BOT_ID!=user_id:
        
    if "question" in text.lower():
        inputs = [text]
        if channel_id == "C04SBHMK76H" and user_id != BOT_ID:
            dictClient[ts] = [userinfo,text]

            response = co.classify(
                model ='large',
                inputs = inputs,
                examples=examples
            )

            valClassification = response.classifications
            d = dict(itertools.zip_longest(*[iter(valClassification)] * 2, fillvalue=""))
            d = list(map(str,d))
            d = str(d[0].split())
            cat = d[33:43]

            userinfo = client.users_info(user=user_id).get('user').get('real_name')
            client.chat_postMessage(channel=channel_id,thread_ts = ts,text=f"Hey {userinfo}! You asked a question pertaining to #{cat}. A message will be sent shortly to the owners.")
        
        

        




if __name__ == "__main__":
    app.run(debug=True)