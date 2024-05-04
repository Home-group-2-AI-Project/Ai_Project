import os
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import pandas as pd

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

    # ckeck reply
    if 'thread_ts' in event and event['thread_ts'] != ts:
        print('Este mensaje es una respuesta en un hilo.')
    else:
        print('Este mensaje no es una respuesta en un hilo.')

    if app.client.auth_test()["user_id"] != user_id:
        print(f'in channel {channel_id}')
        try:
            directory = 'app/slack_config/Data_messages'
            if not os.path.exists(directory):
                os.makedirs(directory)
            csv_file_path = f'app/slack_config/Data_messages/channel_{channel_id}_messages.csv'
            existing_data = pd.read_csv(csv_file_path)         
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
                    if 'user' in mensaje:
                        user = mensaje['user']
                        text = mensaje['text']
                        ts = mensaje['ts']

                        mensajes.append({'channel': channel_id, 'user': user, 'text': text, 'ts': ts})
                        app.client.chat_postMessage(channel=channel_id, text=f"Mensaje guardado: {text}")
                    else:
                        print("Mensaje no contiene información de usuario:", mensaje)                        
                df = pd.DataFrame(mensajes)
                df.to_csv(f'app/slack_config/Data_messages/channel_{channel_id}_messages.csv', index=False)
            else:
                print(f"Error getting messages for channel {channel_id}: {result['error']}")
           
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    
    try:
        # views.publish is the method that your app uses to push a view to the Home tab
        client.views_publish(
            # the user that opened your app's app home
            user_id=event["user"],
            # the view object that appears in the app home
            view={
                "type": "home",
                "callback_id": "home_view",

                # body of the view
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Bot IA encargado de los sentimientos y otras tareas :computer: *Lee la descripcion de uso*, "
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: *Descripcion*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "En las siguientes secciones aparecereran distintas configuraciones, en las cuales tu podras escoger que es lo que quieres que nuestra IA de sentimientos analice,* No te preocupes, cada una de ellas tendran un breve resumen de lo que hacen.*"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": " :one: En esta seccion, podras obtener un resumen de los sentimientos de un usuario en cierto canal(se tendran en cuenta todos los mensajes que el usuario haya enviado)."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":two: En esta seccion, podras obtener un resumen de los sentimientos de un usuario en todos los canales(se tendran en cuenta todos los mensajes que el usuario haya enviado)."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":three: En esta seccion, podras obtener un resumen de los sentimientos de un usuario todos los canales."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":four: En esta seccion, podras obtener un resumen general de los sentimientos de un canal en especifico."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Selecciona una opcion de la lista que acabas de ver"
                        },
                        "accessory": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select an item"
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opcion :one:"
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opcion :two:"
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opcion :three:"
                                    },
                                    "value": "value-2"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opcion :four"
                                    },
                                    "value": "value-3"
                                }
                            ],
                            "action_id": "static_select-action"
                        }
                    }                
                ]
            }
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")
        
       
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route('/slack/events', methods=['POST'])
def slack_events():
    return handler.handle(request)

@flask_app.route('/sentiment',methods=['Post'])
def sentiment(client):
    data = request.form
    user_name = data.get('user_name')
    client.chat_postMessage(channel=data.get(user_name))
    print(f"Received a message from user {user_name}")
    print(data)
    return "", 200

@flask_app.route('/slack/open_modal', methods=['POST'])
def modals():
    return handler.handle(request)

@app.action("static_select-action")
def static_select(ack, body, client):
    ack()
    selected_option = body["actions"][0]["selected_option"]["value"]
    print(f"Opción seleccionada: {selected_option}")
    if selected_option == "value-0":
        client.views_open(trigger_id=body["trigger_id"], 
                         view={
    "title": {
		"type": "plain_text",
		"text": "Opcion 1"
	},
	"submit": {
		"type": "plain_text",
		"text": "Submit"
	},
	"blocks": [
        {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": " Aqui podras obtener un resumen de los sentimientos de un usuario en cierto canal *se tendran en cuenta todos los mensajes que el usuario haya enviado*."
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "channels_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Selecciona un canal"
					},
					"action_id": "actionId-0"
				},
				{
					"type": "users_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Selecciona un usuario"
					},
					"action_id": "actionId-1"
				}
			]
		}
	],
	"type": "modal"
    })
            
            
        client.chat_postMessage(channel=body["user"]["id"], text="Seleccionaste la opción 1")
    elif selected_option == "value-1":
        client.chat_postMessage(channel=body["user"]["id"], text="Seleccionaste la opción 2")
    elif selected_option == "value-2":
        client.chat_postMessage(channel=body["user"]["id"], text="Seleccionaste la opción 3")
    elif selected_option == "value-3":
        client.chat_postMessage(channel=body["user"]["id"], text="Seleccionaste la opción 4")
    else:
        client.chat_postMessage(channel=body["user"]["id"], text="No se seleccionó ninguna opción")
@app.action("button-action")
def button_click(ack, body, client):
    ack()
    client.chat_postMessage(text = 'prueba') #esto imprime un mensaje, pero lo imprime en el chat del propio bot
    print(body)
if __name__ == '__main__':
    flask_app.run(debug=True)
    
