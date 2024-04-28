import slack
import os 
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env' # Path to .env file
load_dotenv(dotenv_path=env_path) # Load the .env file
app = Flask(__name__) # Create a flask app
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN']) # Create a slack client
BOT_ID = client.api_call("auth.test")['user_id'] # Get the bot id

@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event',{})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text') # en este texto se encuentra el mensaje que el usuario envió
    info = client.team_info() # Obtener información del slack en general 

    if BOT_ID != user_id:
        client.chat_postMessage(channel=channel_id,text=text)
        #autenticated_user = client.oauth_v2_access(client_id=os.environ['CLIENT_ID'], client_secret=os.environ['CLIENT_SECRET'],code=os.environ['SLACK_TOKEN']) 
        all_user_list = client.admin_users_list(limit=40, team_id=['T070FSWLE2H'])  
        print(f"Mensaje recibido: {text} ")
        print(f"Autenticador: {all_user_list} ")
        
"""
@slack_event_adapter.on('message_metadata_posted')
def message_metadata_posted(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    # Verificar si el mensaje es del bot o si el mensaje no tiene un canal
    if not channel_id or BOT_ID == user_id:
        return
    autenticated_user = client.oauth_v2_access(client_id=os.environ['CLIENT_ID'], client_secret=os.environ['CLIENT_SECRET'])
    all_user_list = client.admin_users_list(limit=40)
    all_channels_response = client.admin_users_list(types="public_channel")
    if all_user_list['ok']:
        all_channels = all_user_list['users']
        print(f"Lista de canales públicos: {all_channels}") 

    # Imprimir el mensaje en la consola  
"""
if __name__ == '__main__':
    app.run(debug=True) # Run the app in debug mode
    
