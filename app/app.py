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



load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

openai_connection = OpenAIConnection()
channels = get_channels(app)

################################################################################
# app events slack bolt --------------------------------------------------------
################################################################################


@app.event("message")
def handle_message(event, say):
    channel_id = event["channel"]
    user_id = event["user"]
    user_name = app.client.users_info(user=user_id)
    display_name_normalized = user_name["user"]["real_name"]
    text = event["text"]
    ts = event["event_ts"]
    text = emoji.demojize(text)
    text = re.sub(r'http\S+|www.\S+', '', text)
    text = re.sub(r':[a-zA-Z0-9_+-]*:', '', text)
    text = re.sub(r'\W+', ' ', text)
    
    if app.client.auth_test()["user_id"] != user_id:
        print(f'in channel {channel_id}')
        print(f'user {user_id} said: {text}')
        print(f'probando esto: {display_name_normalized}')
        try:
            directory = 'app/slack_utils/data_messages'
            if not os.path.exists(directory):
                os.makedirs(directory)
            csv_file_path = f'app/slack_utils/data_messages/channel_{channel_id}_messages.csv'
            existing_data = pd.read_csv(csv_file_path)
            if ('subtype' not in event or event['subtype'] != 'channel_join') and 'bot_id' not in event:
                new_row = pd.DataFrame(
                    [{'channel': channel_id, 'user': user_id, 'text': text, 'ts': ts}])
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
                        mensajes.append(
                            {'channel': channel_id, 'user': user, 'text': text, 'ts': ts})
                        print("pase por aqui")                       
                    else:
                        print("Mensaje no contiene información de usuario:", mensaje)
                df = pd.DataFrame(mensajes)
                df.to_csv(
                    f'app/slack_utils/data_messages/channel_{channel_id}_messages.csv', index=False)
            else:
                print(
                    f"Error getting messages for channel {channel_id}: {result['error']}")


@app.event("app_home_opened")
def update_home_tab(client, event, logger):

    try:
        print(f"pase por aquí y le di click soy {event['user']}")
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
                        "type": "divider"
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
                            "text": ":five: En esta opcion, podras obtener Top(5) sentimientos mas manejados en cierto canal, por todos los usuarios."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":six: En esta opcion, podras obtener un resumen de cierta cantidad de mensajes en cierto canal, para darte un contexto de lo que hablan los usuarios."
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
                                "text": "Seleccionar"
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
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opcion :five:"
                                    },
                                    "value": "value-4"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opcion :six:"
                                    },
                                    "value": "value-5"
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
#region Actions
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
            channel=body["user"]["id"], text="Seleccionaste la opción 1" )

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
                            "type": "users_select",
                            "placeholder": {
                                "type": "plain_text",
                                        "text": "Selecciona un usuario"
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
    elif selected_option == "value-4":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opcion 5"
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
                        "text": " Aqui podras obtener un resuemn de cierta cantidad de mensajes, para obtener un contexto de la conversacion"
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
                            "action_id": "actionId-5"
                        }
                    ]
                }
            ],
            "type": "modal",
            "callback_id": "option_five",
        })
    elif selected_option == "value-5":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opcion 5"
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
                        "text": " Aqui podras obtener el Top *5* sentimientos mas manejado en cierto canal."
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_text_input-action"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Escribe un numero de mensajes a analizar entre *5* y *200* "
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
                            "action_id": "actionId-6"
                        }
                    ]
                }
            ],
            "type": "modal",
            "callback_id": "option_six",
        })
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
    selected_user_two = body["view"]["state"]["values"]["AAWCp"]["actionId-3"]["selected_user"]
    print(selected_user_two)
    return selected_user_two

@app.action("actionId-4")
def handle_some_action_option_four(ack, body):
    ack()
    selected_channel_four = body["view"]["state"]["values"]["Lh2Uo"]["actionId-4"]["selected_channel"]
    print(selected_channel_four)
    return selected_channel_four

@app.action("actionId-5")
def handle_some_action_option_five(ack, body):
    ack()  
    selected_channel_five = body['view']['state']['values']['omv1w']['actionId-5']['selected_channel']
    print(selected_channel_five)
    return selected_channel_five

@app.action("actionId-6")
def handle_some_action_option_six(ack, body):
    ack()
    selected_channel_six = body["view"]["state"]["values"]["qjcrh"]["actionId-6"]["selected_channel"]
    print(selected_channel_six)
    return selected_channel_six

@app.action("plain_text_input-action")
def handle_some_action_option_six_label(ack, body,client):
    ack()    
    try:
        #si el input es un numero entre 5 y 200 lo guardamos en una variable y lo retornamos
        input_number = body["view"]["state"]["values"]["nLBoM"]["plain_text_input-action"]["value"]
        input_number = int(input_number)
        print(input_number)
        return input_number # retorna el numero de mensajes a analizar
    except ValueError:  # Raised when converting text to a number fails
        # Open the modal again with an error message
        client.views_open(trigger_id=body["trigger_id"], view={
            "title": {
                "type": "plain_text",
                "text": "¡Error!"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Por favor, introduce un número de mensajes para analizar. Solo se permiten números entre 5 y 200."
                    }
                }
            ],
            "type": "modal",
            "callback_id": "error_modal"  # New callback_id for error modal
        })
        return None  # retorna None si el input no es un numero entre 5 y 200

################################################################################
# app views slack bolt ---------------------------------------------------------
################################################################################

#region Views
@app.view("option_one")
def handle_view_submission_events_option_one(ack, body,client):
    ack()
    print(body)
    # obtenemos los datos del canal y del usuario y lo guardamos en una variable la cual se retornara para ser enviada al modelo IA
    information_options = handle_some_action_zero(
        ack, body), handle_some_action_one(ack, body)
    user_info = client.users_info(user=information_options[1])
    real_name = user_info["user"]["real_name"]
    print(f"estoy imprimiendo: {real_name}")
    
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    print(user_id)
    return information_options, user_id , real_name


@app.view("option_two")
def handle_view_submission_events_option_two(ack, body,client):
    ack()
    information_options_two = handle_some_action_option_two(ack, body)
    print(f'Usuario seleccionado: {information_options_two}')
    #obtener el nombre del usuario que ha sido seleccionado en el formulario
    user_info_two = client.users_info(user=information_options_two)
    real_name_two = user_info_two["user"]["real_name"]
    print(f"estoy imprimiendo: {real_name_two}")
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    print(user_id)
    return information_options_two, user_id , real_name_two


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

@app.view("option_five")
def handle_view_submission_events_option_five(ack, body):
    ack()
    information_options_five = handle_some_action_option_five(ack, body)
    print(f'Canal seleccionado: {information_options_five}')
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    print(user_id)
    return information_options_five, user_id
errors = {}
@app.view("option_six")
def handle_view_submission_events_option_six(ack, body, client):
    ack()
    information_options_six = handle_some_action_option_six(ack, body), handle_some_action_option_six_label(ack, body, client)
    print(information_options_six)
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]        
    # retorna el canal seleccionado y el numero de mensajes a analizar en la variable information_options_six
    # y el id del usuario que ha enviado el formulario
    return information_options_six, user_id 

################################################################################
# flask app --------------------------------------------------------------------
################################################################################

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route('/sentiment', methods=['Post'])
def sentiment():
    data = request.form
    user_name = data.get('user_name')
    app.client.chat_postMessage(channel=data.get(user_name))
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
    flask_app.run(debug=True)
