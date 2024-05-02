import slack
import os 
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask,request,Response
from slackeventsapi import SlackEventAdapter
import pandas as pd

env_path = Path('.') / '.env' # Path to .env file
load_dotenv(dotenv_path=env_path) # Load the .env file
app = Flask(__name__) # Create a flask app
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN']) # Create a slack client
BOT_ID = client.api_call("auth.test")['user_id'] # Get the bot id

def get_channels():
    
    all_channels_response = client.conversations_list(types="public_channel")
    if all_channels_response['ok']:
        all_channels = all_channels_response['channels']
        #print(f"Lista de canales públicos: {all_channels}")
        channel_info_list = []
        for channel in all_channels:
            channel_info = {
                'name_normalized': channel['name_normalized'],
                'id': channel['id']
            }
            channel_info_list.append(channel_info)
        
        return channel_info_list
    else:
        print(f"Error getting channels: {all_channels_response['error']}")
        return []  # Return empty list on error


channels = get_channels()
print(channels)

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text') # en este texto se encuentra el mensaje que el usuario envió
    #info = client.team_info() # Obtener información del slack en general 
    conversation_history = []
    mensajes = []
     # Ensure it's a message from a user (not the bot itself) and avoid sensitive information
    if BOT_ID != user_id:
        # Iterate over each channel and get messages
        for channel_info in channels:
            channel_id = channel_info['id']
            channel_name = channel_info['name_normalized']  # Obtener el nombre del canal
            # Use conversations.history API call to get channel messages
            result = client.conversations_history(channel=channel_id)
            if result['ok']:
                conversation_history = result["messages"]
                mensajes = []
                for mensaje in conversation_history:
                    if 'user' in mensaje:
                        user = mensaje['user']
                        text = mensaje['text']
                        ts = mensaje['ts']
                    
                    # Agregar el nombre del canal al mensaje
                        mensajes.append({'channel_name': channel_name, 'user': user, 'text': text, 'ts': ts})
                    else:
                        print("Mensaje no contiene información de usuario:", mensaje)                        
                # Save messages to CSV
                    df = pd.DataFrame(mensajes)
                    df.to_csv(f'app/slack_config/Data_messages/channel_{channel_id}_messages.csv', index=False)
            else:
                print(f"Error getting messages for channel {channel_name}: {result['error']}")


@app.route('/sentiment',methods=['Post'])
def sentiment():
    data = request.form
    user_name = data.get('user_name')
    print(f"Received a message from user {user_name}")
    print(data)
    return Response(),200   

     
if __name__ == '__main__':
    app.run(debug=True) # Run the app in debug mode
    
