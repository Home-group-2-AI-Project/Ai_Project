import os
import openai
import emoji
import re


import pandas as pd

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from slack_utils.open_ai_connection import OpenAIConnection
from slack_utils.get_channels import get_channels
from slack_utils.model import Model

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

openai_connection = OpenAIConnection()
channels = get_channels(app)
model = Model()

################################################################################
# app events slack bolt --------------------------------------------------------
################################################################################


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
            directory = 'app/slack_utils/data_messages'
            if not os.path.exists(directory):
                os.makedirs(directory) 
            channel_info = app.client.conversations_info(channel=channel_id)
            channel_name = channel_info["channel"]["name"]
            csv_file_path = f'app/slack_config/data_messages/channel_{channel_name}_messages.csv'
            existing_data = pd.read_csv(csv_file_path)
            if ('subtype' not in event or event['subtype'] != 'channel_join') and 'bot_id' not in event:
                channel_info = app.client.conversations_info(channel=channel_id)
                channel_name = channel_info["channel"]["name"]
                text_tranlated = openai_connection.traducir_texto([text])[0]
                text = text_tranlated.translate({ord(c): None for c in "!@#$%^&*()[]{};:,./<>?|`~-=_+'\""})
                new_row = pd.DataFrame(
                    [{'channel': channel_name, 'user': user_id, 'text': text, 'ts': ts}])
                updated_data = pd.concat(
                    [new_row, existing_data], ignore_index=True, sort=False)
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
                        channel_info = app.client.conversations_info(channel=channel_id)
                        channel_name = channel_info["channel"]["name"]
                        mensajes.append(
                            {'channel': channel_name, 'user': user, 'text': text, 'ts': ts})
                    else:
                        print("Mensaje no contiene información de usuario:", mensaje)
                channel_info = app.client.conversations_info(channel=channel_id)
                channel_name = channel_info["channel"]["name"]
                

                textos = [mensaje['text'] for mensaje in mensajes]
                textos_traducidos = openai_connection.traducir_texto(textos)
                textos_limpios = [texto.translate({ord(c): None for c in "!@#$%^&*()[]{};:,./<>?|`~-=_+'\""}) for texto in textos_traducidos]
                for i in range(len(mensajes)):
                    mensajes[i]['text'] = textos_limpios[i]

                df = pd.DataFrame(mensajes)
                df.to_csv(
                    f'app/slack_config/data_messages/channel_{channel_name}_messages.csv', index=False)
            else:
                print(
                    f"Error getting messages for channel {channel_id}: {result['error']}")


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
                            "text": " :one: En esta opción, podras obtener un resumen de los sentimientos de un usuario en cierto canal(se tendran en cuenta todos los mensajes que el usuario haya enviado)."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":two: En esta opción, podras obtener un resumen de los sentimientos de un usuario en todos los canales(se tendran en cuenta todos los mensajes que el usuario haya enviado)."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":three: En esta opción, podras obtener un resumen de los sentimientos de todos los canales en general."
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
                                        "text": "Opcion :four:"
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

################################################################################
# app commands slack bolt ------------------------------------------------------
################################################################################


@app.command("/chatgpt")
def command_chat_gpt(ack, say, command):
    # Acknowledge the command right away
    ack()

    # Extract the user's message
    text = command['text']

    reply = OpenAIConnection.chat_gpt(text)

    # Post the user's message and the response back to the same channel
    say(f"*Respuesta:* {reply}\n----------------")


@app.command("/usuario-canal")
def command_resumen_sentimientos_usuario_canal(ack, say, command):

    ack()

    text = command['text']
    usuario, canal = text.split(" ")

    pass


@app.command("/usuario-general")
def command_resumen_sentimientos_usuario_general(ack, say, command):

    ack()

    text = command['text']
    usuario = text

    pass


@app.command("/canal")
def command_resumen_sentimientos_canal(ack, say, command):

    ack()

    text = command['text']
    canal = text

    pass


@app.command("/top-canal")
def resumen_top_canal(ack, say, command):

    ack()

    text = command['text']
    canal = text

    pass


@app.command("/resumen")
def resumen_contexto_canal(ack, say, command):

    ack()

    text = command['text']
    canal, numero_mensajes = text.split(" ")

    pass

################################################################################
# app actions slack bolt -------------------------------------------------------
################################################################################


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
            "type": "modal",
            "callback_id": "option_one"
        })

        client.chat_postMessage(
            channel=body["user"]["id"], text="Seleccionaste la opción 1")

    elif selected_option == "value-1":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opcion 2"
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
                        "text": " Aqui podras obtener un resumen de los sentimientos de un usuario en todos los canales *se tendran en cuenta todos los mensajes que el usuario haya enviado*."
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
                            "action_id": "actionId-3"
                        }
                    ]
                }
            ],
            "type": "modal",
            "callback_id": "option_two",
        })

        client.chat_postMessage(
            channel=body["user"]["id"], text="Seleccionaste la opción 2")
    elif selected_option == "value-2":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opcion 3"
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
                        "text": " Aqui podras obtener un resumen de los sentimientos en todos los canales *se tendran en cuenta en limite de 100 mensajes por canal*."
                    }
                }
            ],
            "type": "modal",
            "callback_id": "option_three",
        })
        client.chat_postMessage(
            channel=body["user"]["id"], text="Seleccionaste la opción 3")
    elif selected_option == "value-3":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opcion 4"
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
                        "text": " Aqui podras obtener un resumen general de los sentimientos de un canal en especifico. *se tendran en cuenta 200 mensajes para hacer este analisis*."
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
                            "action_id": "actionId-4"
                        }
                    ]
                }
            ],
            "type": "modal",
            "callback_id": "option_four",
        })
        client.chat_postMessage(
            channel=body["user"]["id"], text="Seleccionaste la opción 4")
    else:
        client.chat_postMessage(
            channel=body["user"]["id"], text="No se seleccionó ninguna opción")


@app.action("actionId-0")
def handle_some_action_zero(ack, body):
    ack()
    # canal que el usuario ha seleccionado
    selected_channel = body["view"]["state"]["values"]["DIUt4"]["actionId-0"]["selected_channel"]
    print(selected_channel)
    return selected_channel


@app.action("actionId-1")
def handle_some_action_one(ack, body):
    ack()
    # usuario que el usuario ha seleccionado
    selected_user = body["view"]["state"]["values"]["DIUt4"]["actionId-1"]["selected_user"]
    print(selected_user)
    return selected_user


@app.action("actionId-3")
def handle_some_action_option_two(ack, body):
    ack()
    # canal que el usuario ha seleccionado
    selected_channel_two = body["actions"][0]["selected_channel"]
    print(selected_channel_two)
    return selected_channel_two


@app.action("actionId-4")
def handle_some_action_option_four(ack, body):
    ack()
    selected_channel_four = body["view"]["state"]["values"]["Lh2Uo"]["actionId-4"]["selected_channel"]
    print(selected_channel_four)
    return selected_channel_four

################################################################################
# app views slack bolt ---------------------------------------------------------
################################################################################


@app.view("option_one")
def handle_view_submission_events_option_one(ack, body):
    ack()
    print(body)
    # obtenemos los datos del canal y del usuario y lo guardamos en una variable la cual se retornara para ser enviada al modelo IA
    information_options = handle_some_action_zero(
        ack, body), handle_some_action_one(ack, body)
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    
    print(information_options)
    print(user_id)
    return information_options, user_id


@app.view("option_two")
def handle_view_submission_events_option_two(ack, body):
    ack()
    information_options_two = body["view"]["state"]["values"]["esL3U"]["actionId-3"]["selected_channel"]
    print(f'Canal seleccionado: {information_options_two}')
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    print(user_id)
    return information_options_two, user_id


@app.view("option_three")
def handle_view_submission_events_option_three(ack, body):
    ack()
    option = 3
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    print(user_id)

    return option, user_id


@app.view("option_four")
def handle_view_submission_events_option_four(ack, body):
    ack()
    information_options_four = handle_some_action_option_four(ack, body)
    print(f'Canal seleccionado: {information_options_four}')
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    print(user_id)
    return information_options_four, user_id


################################################################################
# flask app --------------------------------------------------------------------
################################################################################

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route('/sentiment', methods=['Post'])
def sentiment(client):
    data = request.form
    user_name = data.get('user_name')
    client.chat_postMessage(channel=data.get(user_name))
    print(f"Received a message from user {user_name}")
    print(data)
    return "Hola, ¿en qué te puedo ayudar?", 200


@flask_app.route('/slack/open_modal', methods=['POST'])
def modals():
    return handler.handle(request)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@flask_app.route("/slack/commands", methods=["POST"])
def slack_commands():
    return handler.handle(request)


@flask_app.route("/slack/install", methods=["GET"])
def install():
    return handler.handle(request)


@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)


if "__main__" == __name__:
    flask_app.run(port=3000)
