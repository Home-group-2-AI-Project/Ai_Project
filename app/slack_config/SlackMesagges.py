import os
from pathlib import Path
import re
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import pandas as pd
import emoji

env_path = Path('.') / '.env' # Path to .env file
load_dotenv(dotenv_path=env_path) # Load the .env file
app = App(
    token=os.environ['SLACK_TOKEN'],
    signing_secret=os.environ['SIGNING_SECRET']
)

def get_channels(app):
    try:
        result = app.client.conversations_list(types="public_channel")
        if result['ok']:
            all_channels = result['channels']
            channel_info_list = []
            for channel in all_channels:
                channel_info = {
                    'name_normalized': channel['name_normalized'],
                    'id': channel['id'],
                }
                channel_info_list.append(channel_info)
            return channel_info_list
        else:
            print(f"Error getting channels: {result['error']}")
            return []  # Return empty list on error
    except Exception as e:
        print(f"Error: {e}")

channels = get_channels(app)

@app.event("message")
def handle_message(event, say):
    channel_id = event["channel"]
    user_id = event["user"]
    text = event["text"]
    ts = event["event_ts"]
    text = emoji.demojize(text)
    text = re.sub(r'http\S+|www.\S+', '', text)
    text = re.sub(r':[a-zA-Z0-9_+-]*:', '', text)
    text = re.sub(r'\W+', ' ', text)
    if app.client.auth_test()["user_id"] != user_id:
        print(f'in channel {channel_id}')
        try:
            directory = 'app/slack_config/Data_messages'
            if not os.path.exists(directory):
                os.makedirs(directory)
            csv_file_path = f'app/slack_config/Data_messages/channel_{channel_id}_messages.csv'
            existing_data = pd.read_csv(csv_file_path)         
            if ('subtype' not in event or event['subtype'] != 'channel_join') and 'bot_id' not in event:
                new_row = pd.DataFrame([{'channel': channel_id,'user': user_id, 'text': text, 'ts': ts}])
                updated_data = pd.concat([new_row,existing_data], ignore_index=True, sort=False)
                updated_data.to_csv(csv_file_path, index=False)
            return
        except Exception as e:
            print(f"Error opening file for channel {channel_id}: {e}")
            print(f"Getting messages for channel {channel_id}")
            result = app.client.conversations_history(channel=channel_id)
        
            if result['ok']:
                conversation_history = result["messages"]
                mensajes = []
                for mensaje in conversation_history:
                    if 'user' in mensaje and ('subtype' not in mensaje or mensaje['subtype'] != 'channel_join') and 'bot_id' not in mensaje:
                        user = mensaje['user']
                        text = mensaje['text']
                        ts = mensaje['ts']
                        text = emoji.demojize(text)
                        text = re.sub(r'http\S+|www.\S+', '', text)
                        text = re.sub(r':[a-zA-Z0-9_+-]*:', '', text)
                        text = re.sub(r'\W+', ' ', text)
                        mensajes.append({'channel': channel_id, 'user': user, 'text': text, 'ts': ts})
                    else:
                        print("Mensaje no contiene información de usuario:", mensaje)                        
                df = pd.DataFrame(mensajes)
                df.to_csv(f'app/slack_config/Data_messages/channel_{channel_id}_messages.csv', index=False)
            else:
                print(f"Error getting messages for channel {channel_id}: {result['error']}")
           

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route('/slack/events', methods=['POST'])
def slack_events():
    return handler.handle(request)

@flask_app.route('/sentiment',methods=['Post'])
def sentiment():
    data = request.form
    user_name = data.get('user_name')
    print(f"Received a message from user {user_name}")
    print(data)
    return "Hola, ¿en qué te puedo ayudar?", 200

if __name__ == '__main__':
    flask_app.run(debug=True)
    
