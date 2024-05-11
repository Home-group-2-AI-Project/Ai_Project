import os
import openai
import emoji
import re


import pandas as pd

from dotenv import load_dotenv

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler


from slack_sdk.oauth.installation_store.file import FileInstallationStore
from slack_sdk.oauth.state_store.file import FileOAuthStateStore


from flask import Flask, request

from slack_utils.open_ai_connection import OpenAIConnection
from slack_utils.get_channels import get_channels
from slack_utils.model import Model
from slack_utils.control_data import (
    get_user_only_chanel,
    get_resume_conversation,
    get_user_all_channels,
    get_sentiment_all_channel,
    get_sentiment_one_channel,
    get_top_5_sentiment_one_channel
)

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

# oauth settings with all required parameters


bolt_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    
    
)

openai_connection = OpenAIConnection()
channels = get_channels(bolt_app)
model = Model()


################################################################################
# bolt_app events slack bolt --------------------------------------------------------
################################################################################


@bolt_app.event("message")
def handle_message(event, say,logger):
    print(f"este el login {logger}")
    channel_id = event["channel"]
    user_id = event["user"]
    #print(bolt_app.client.users_info(user='user_id'))
    #user_name = bolt_app.client.users_info(user=user_id)
    #display_name_normalized = user_name["user"]["real_name"] 
    team_id = event["team"]
    print(f"team_id: {team_id}")
    text = event["text"]
    ts = event["event_ts"]
    text = emoji.demojize(text)
    text = re.sub(r'http\S+|www.\S+', '', text)
    text = re.sub(r':[a-zA-Z0-9_+-]*:', '', text)
    text = re.sub(r'\W+', ' ', text)

    if bolt_app.client.auth_test()["user_id"] != user_id:
        print(f'in channel {channel_id}')
        print(f'user {user_id} said: {text}')
        #print(event)
        #print(bolt_app.client.conversations_list(types="public_channel",team_id=team_id))
        #print(f'probando esto: {display_name_normalized}')
        try:
            directory = 'app/slack_config/data_messages'
            if not os.path.exists(directory):
                os.makedirs(directory)
            channel_info = bolt_app.client.conversations_info(
                channel="channel_id")
            channel_name = channel_info["channel"]["name"]
            csv_file_path = f'app/slack_config/data_messages/{team_id}_channel_{channel_name}_messages.csv'
            existing_data = pd.read_csv(csv_file_path)
            if ('subtype' not in event or event['subtype'] != 'channel_join') and 'bot_id' not in event:
                channel_info = bolt_app.client.conversations_info(
                    channel=channel_id)
                channel_name = channel_info["channel"]["name"]
                text_tranlated = openai_connection.traducir_texto([text])[0]
                text = text_tranlated.translate(
                    {ord(c): None for c in "!@#$%^&*()[]{};:,./<>?|`~-=_+'\""})
                new_row = pd.DataFrame(
                    [{'channel': channel_name, 'user': user_id, 'text': text, 'ts': ts}])
                updated_data = pd.concat(
                    [new_row, existing_data], ignore_index=True, sort=False)
                updated_data.to_csv(csv_file_path, index=False)
            return
        except Exception as e:
            print(f"Error opening file for channel {channel_id}: {e}")
            print(f"Getting messages for channel {channel_id}")
            result = bolt_app.client.conversations_history(channel=channel_id)

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
                        channel_info = bolt_app.client.conversations_info(
                            channel=channel_id)
                        channel_name = channel_info["channel"]["name"]
                        mensajes.append(
                            {'channel': channel_name, 'user': user, 'text': text, 'ts': ts})
                        # print("pase por aqui")
                    else:
                        print("Mensaje no contiene información de usuario:", mensaje)
                channel_info = bolt_app.client.conversations_info(
                    channel=channel_id)
                channel_name = channel_info["channel"]["name"]

                textos = [mensaje['text'] for mensaje in mensajes]
                textos_traducidos = openai_connection.traducir_texto(textos)
                textos_limpios = [texto.translate(
                    {ord(c): None for c in "!@#$%^&*()[]{};:,./<>?|`~-=_+'\""}) for texto in textos_traducidos]
                print(textos_limpios)
                for i in range(len(mensajes)):
                    mensajes[i]['text'] = textos_limpios[i]

                df = pd.DataFrame(mensajes)
                df.to_csv(
                    f'app/slack_config/data_messages/{team_id}_channel_{channel_name}_messages.csv', index=False)
            else:
                print(
                    f"Error getting messages for channel {channel_id}: {result['error']}")


@bolt_app.event("app_home_opened")
def update_home_tab(client, event, logger):

    try:
        print(f"pase por aquí y le di click soy {event['user']}")
        # views.publish is the method that your bolt_app uses to push a view to the Home tab
        client.views_publish(
            # the user that opened your bolt_app's bolt_app home
            user_id=event["user"],
            # the view object that appears in the bolt_app home
            view={
                "type": "home",
                "callback_id": "home_view",

                # body of the view
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Bot IA encargado de los sentimientos y otras tareas :computer: *Lee la descripción de uso*."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":white_check_mark: *Descripción*."
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": " :large_green_circle: En las siguientes secciones aparecerán distintas configuraciones, en las cuales tú podrás escoger qué es lo que quieres que nuestra IA de sentimientos analice. *No te preocupes, cada una de ellas tendrá un breve resumen de lo que hacen*."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": " :large_green_circle: Primero tendrás que seleccionar una de las opciones, posterior a eso y a llenar los datos correspondientes, en la sección de *Mensajes* de la parte superior, encontrarás tu respuesta. *Tranquilo, este es un chat privado entre tú y el bot :robot_face:*."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": ":one: En esta opción, podrás obtener un resumen de los sentimientos de un usuario en cierto canal (se tendrán en cuenta todos los mensajes que el usuario haya enviado)."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":two: En esta opción, podrás obtener un resumen de los sentimientos de un usuario en todos los canales (se tendrán en cuenta todos los mensajes que el usuario haya enviado)."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":three: En esta opción, podrás obtener un resumen de los sentimientos de todos los canales en general."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":four: En esta sección, podrás obtener un resumen general de los sentimientos de un canal en específico."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":five: En esta opción, podrás obtener *Top(5)* sentimientos más manejados en cierto canal, por todos los usuarios."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":six: En esta opción, podrás obtener un resumen de cierta cantidad de mensajes en cierto canal, para darte un contexto de lo que hablan los usuarios."
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Selecciona una opción de la lista que acabas de ver."
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
                                        "text": "Opción :one:"
                                    },
                                    "value": "value-0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opción :two:"
                                    },
                                    "value": "value-1"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opción :three:"
                                    },
                                    "value": "value-2"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opción :four:"
                                    },
                                    "value": "value-3"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opción :five:"
                                    },
                                    "value": "value-4"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Opción :six:"
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
# bolt_app commands slack bolt ------------------------------------------------------
################################################################################
# region Commands


@bolt_app.command("/chatgpt")
def command_chat_gpt(ack, say, command):
    # Acknowledge the command right away
    ack()

    # Extract the user's message
    text = command['text']

    reply = openai_connection.chat_gpt(text)

    # Post the user's message and the response back to the same channel
    say(f"*Respuesta:* {reply}\n----------------")


@bolt_app.command("/sentiment")
def command_sentimientos(ack, command, client):
    ack()
    texts = "Hola, soy un bot de análisis de sentimientos, para poder ayudarte necesito que te dirigas a la parte inferior izquierda de tu slack en donde encontraras las posibles opciones que puedo ofrecerte."
    print(f"Received a message from user {texts}")
    return client.chat_postMessage(channel=command['channel_id'], text=texts, as_user=True)


@bolt_app.command("/usuario-canal")
def command_resumen_sentimientos_usuario_canal(ack, say, command):

    ack()

    text = command['text']
    usuario, canal = text.split(" ")

    pass


@bolt_app.command("/usuario-general")
def command_resumen_sentimientos_usuario_general(ack, say, command):

    ack()

    text = command['text']
    usuario = text

    pass


@bolt_app.command("/canal")
def command_resumen_sentimientos_canal(ack, say, command):

    ack()

    text = command['text']
    canal = text

    pass


@bolt_app.command("/top-canal")
def resumen_top_canal(ack, say, command):

    ack()

    text = command['text']
    canal = text

    pass


@bolt_app.command("/resumen")
def resumen_contexto_canal(ack, say, command):

    ack()

    text = command['text']
    canal, numero_mensajes = text.split(" ")

    pass

################################################################################
# bolt_app actions slack bolt -------------------------------------------------------
################################################################################
# region Actions


@bolt_app.action("static_select-action")
def static_select(ack, body, client):
    ack()
    selected_option = body["actions"][0]["selected_option"]["value"]
    print(f"Opción seleccionada: {selected_option}")
    if selected_option == "value-0":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opción 1"
            },
            "submit": {
                "type": "plain_text",
                "text": "Enviar"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Aquí podrás obtener un resumen de los sentimientos de un usuario en cierto canal. *Se tendrán en cuenta todos los mensajes que el usuario haya enviado.*"
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

    elif selected_option == "value-1":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opción 2"
            },
            "submit": {
                "type": "plain_text",
                "text": "Enviar"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Aquí podrás obtener un resumen de los sentimientos de un usuario en todos los canales. *Se tendrán en cuenta todos los mensajes que el usuario haya enviado.*"
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

    elif selected_option == "value-2":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opción 3"
            },
            "submit": {
                "type": "plain_text",
                "text": "Enviar"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": " Aquí podrás obtener un resumen de los sentimientos en todos los canales. *Se tendrán en cuenta un límite de 100 mensajes por canal.*"
                    }
                }
            ],
            "type": "modal",
            "callback_id": "option_three",
        })

    elif selected_option == "value-3":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opción 4"
            },
            "submit": {
                "type": "plain_text",
                "text": "Enviar"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": " Aquí podrás obtener un resumen general de los sentimientos de un canal específico. *Se tendrán en cuenta 200 mensajes para hacer este análisis.*"
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

    elif selected_option == "value-4":
        client.views_open(trigger_id=body["trigger_id"],
                          view={
            "title": {
                "type": "plain_text",
                "text": "Opción 5"
            },
            "submit": {
                "type": "plain_text",
                "text": "Enviar"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": " Aquí podrás obtener un resumen de cierta cantidad de mensajes, para obtener un contexto de la conversación."
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
                "text": "Opción 6"
            },
            "submit": {
                "type": "plain_text",
                "text": "Enviar"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": " Aquí podrás obtener el Top *5* sentimientos más manejados en cierto canal."
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
                        "text": "Escribe un número de mensajes a analizar entre *5* y *200*"
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

# region bolt_actions


@bolt_app.action("actionId-0")
def handle_some_action_zero(ack, body, client):
    ack()
    print(body)
    # canal que el usuario ha seleccionado
    selected_channel = body["view"]["state"]["values"]["Z7U2a"]["actionId-0"]["selected_channel"]
    channel_info = client.conversations_info(channel=selected_channel)
    channel_name = channel_info["channel"]["name"]
    print(channel_name)
    return channel_name


@bolt_app.action("actionId-1")
def handle_some_action_one(ack, body):
    ack()
    # usuario que el usuario ha seleccionado
    selected_user = body["view"]["state"]["values"]["Z7U2a"]["actionId-1"]["selected_user"]
    print(selected_user)
    return selected_user


@bolt_app.action("actionId-3")
def handle_some_action_option_two(ack, body):
    ack()
    # canal que el usuario ha seleccionado
    selected_user_two = body["view"]["state"]["values"]["eVKQH"]["actionId-3"]["selected_user"]
    print(selected_user_two)
    return selected_user_two


@bolt_app.action("actionId-4")
def handle_some_action_option_four(ack, body, client):
    ack()

    selected_channel_four = body["view"]["state"]["values"]["7PqfP"]["actionId-4"]["selected_channel"]
    channels_info_four = client.conversations_info(
        channel=selected_channel_four)
    channel_name_four = channels_info_four["channel"]["name"]
    print(channel_name_four)
    return channel_name_four


@bolt_app.action("actionId-5")
def handle_some_action_option_five(ack, body, client):
    ack()

    selected_channel_five = body['view']['state']['values']['rw6ER']['actionId-5']['selected_channel']
    channels_info_five = client.conversations_info(
        channel=selected_channel_five)
    channel_name_five = channels_info_five["channel"]["name"]
    print(channel_name_five)
    return channel_name_five


@bolt_app.action("actionId-6")
def handle_some_action_option_six(ack, body, client):
    ack()
    selected_channel_six = body["view"]["state"]["values"]["k8wqP"]["actionId-6"]["selected_channel"]
    channels_info_six = client.conversations_info(channel=selected_channel_six)
    channel_name_six = channels_info_six["channel"]["name"]
    print(channel_name_six)
    return channel_name_six


@bolt_app.action("plain_text_input-action")
def handle_some_action_option_six_label(ack, body, client):
    ack()
    try:
        # si el input es un numero entre 5 y 200 lo guardamos en una variable y lo retornamos
        input_number = body["view"]["state"]["values"]["AYvxe"]["plain_text_input-action"]["value"]
        input_number = int(input_number)
        print(input_number)
        return input_number  # retorna el numero de mensajes a analizar
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
# bolt_app views slack bolt ---------------------------------------------------------
################################################################################

# region Views


@bolt_app.view("option_one")
def handle_view_submission_events_option_one(ack, body, client):
    ack()
    # obtenemos los datos del canal y del usuario y lo guardamos en una variable la cual se retornara para ser enviada al modelo IA
    information_options = handle_some_action_zero(
        ack, body, client), handle_some_action_one(ack, body)
    user_info = client.users_info(user=information_options[1])
    real_name = user_info["user"]["real_name"]
    print(f"estoy imprimiendo: {real_name}")
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    user_info_submit = client.users_info(user=user_id)
    user_submit_real_name = user_info_submit["user"]["real_name"]
    team_id = body["user"]["team_id"]
    print(team_id)
    option_one_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hola {user_submit_real_name}, te escribo con la respuesta a la solicitud que creaste. :hand:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Recuerda que seleccionaste la opción: *Número :one:*, con estos datos: -canal: {information_options[0]}, -usuario: {real_name}."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "En esta respuesta, podrás obtener un resumen de los sentimientos de un usuario en cierto canal (se tendrán en cuenta todos los mensajes que el usuario haya enviado)."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "En base a tu selección se obtuvo:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ""
            }
        }
    ]

    # Enviar el mensaje y capturar el resultado de get_user_only_chanel()
    response = get_user_only_chanel(
        information_options[1], information_options[0],team_id)
    # Actualizar el bloque con el resultado
    option_one_blocks[-1]["text"]["text"] = response

    # Enviar el mensaje con los bloques actualizados
    client.chat_postMessage(channel=user_id, text="hola",
                            blocks=option_one_blocks, as_user=True)


@bolt_app.view("option_two")
def handle_view_submission_events_option_two(ack, body, client):
    ack()
    information_options_two = handle_some_action_option_two(ack, body)
    print(f'Usuario seleccionado: {information_options_two}')
    # obtener el nombre del usuario que ha sido seleccionado en el formulario
    user_info_two = client.users_info(user=information_options_two)
    real_name_two = user_info_two["user"]["real_name"]
    print(f"estoy imprimiendo: {real_name_two}")
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    team_id = body["user"]["team_id"]
    user_info_submit_two = client.users_info(user=user_id)
    user_submit_real_name_two = user_info_submit_two["user"]["real_name"]
    print(user_id)
    option_two_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hola {user_submit_real_name_two}, te escribo con la respuesta a la solicitud que creaste. :hand:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Recuerda que seleccionaste la opción: *Número :two:*, con estos datos: -canal: {information_options_two} ."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "En esta respuesta, podrás obtener un resumen de los sentimientos de un usuario en todos los canales *se tendrán en cuenta todos los mensajes que el usuario haya enviado*."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "En base a tu selección se obtuvo:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ""
            }
        }
    ]
    print(f"Usuario seleccionado: {information_options_two}")
    response = get_user_all_channels(information_options_two,team_id)
    # Actualizar el bloque con el resultado
    option_two_blocks[-1]["text"]["text"] = response

    # Enviar el mensaje con los bloques actualizados
    client.chat_postMessage(channel=user_id, text="hola",
                            blocks=option_two_blocks, as_user=True)


@bolt_app.view("option_three")
def handle_view_submission_events_option_three(ack, body, client):
    ack()
    option = 3
    team_id = body["user"]["team_id"]
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    user_info_submit_three = client.users_info(user=user_id)
    user_submit_real_name_three = user_info_submit_three["user"]["real_name"]
    print(user_id)
    option_three_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hola {user_submit_real_name_three}, te escribo con la respuesta a la solicitud que creaste. :hand:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Recuerda que seleccionaste la opción: *Número :three:*."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "En esta respuesta, podrás obtener un *resumen de los sentimientos de todos los canales en general*."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "En base a tu selección se obtuvo:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ""
            }
        }
    ]

    response = get_sentiment_all_channel(team_id)
    option_three_blocks[-1]["text"]["text"] = response
    client.chat_postMessage(channel=user_id, text="hola",
                            blocks=option_three_blocks, as_user=True)


@bolt_app.view("option_four")
def handle_view_submission_events_option_four(ack, body, client):
    ack()
    team_id = body["user"]["team_id"]
    information_options_four = handle_some_action_option_four(
        ack, body, client)
    print(f'Canal seleccionado: {information_options_four}')
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    user_info_submit_four = client.users_info(user=user_id)
    user_submit_real_name_four = user_info_submit_four["user"]["real_name"]
    print(user_id)
    option_four_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hola {user_submit_real_name_four}, te escribo con la respuesta a la solicitud que creaste. :hand:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Recuerda que seleccionaste la opción: *Número :four:*,con estos datos: -canal:{information_options_four}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "En esta respuesta, podrás obtener un *resumen general de los sentimientos de un canal en específico*."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "En base a tu selección se obtuvo:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ""
            }
        }
    ]

    response = get_sentiment_one_channel(information_options_four,team_id)
    option_four_blocks[-1]["text"]["text"] = response
    client.chat_postMessage(channel=user_id, text="hola",
                            blocks=option_four_blocks, as_user=True)


@bolt_app.view("option_five")
def handle_view_submission_events_option_five(ack, body, client):
    ack()
    team_id = body["user"]["team_id"]
    information_options_five = handle_some_action_option_five(
        ack, body, client)
    print(f'Canal seleccionado: {information_options_five}')
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    user_info_submit_five = client.users_info(user=user_id)
    user_submit_real_name_five = user_info_submit_five["user"]["real_name"]

    print(user_id)
    option_five_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hola {user_submit_real_name_five}, te escribo con la respuesta a la solicitud que creaste. :hand:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Recuerda que seleccionaste la opción: *Número cinco*, con estos datos: -canal:{information_options_five}."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "En esta respuesta, podrás obtener *Top(5) sentimientos más manejados en cierto canal, por todos los usuarios*."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "En base a tu selección se obtuvo:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ""
            }
        }
    ]

    response = get_top_5_sentiment_one_channel(information_options_five,team_id)
    option_five_blocks[-1]["text"]["text"] = response
    client.chat_postMessage(channel=user_id, text="hola",
                            blocks=option_five_blocks, as_user=True)


errors = {}


@bolt_app.view("option_six")
def handle_view_submission_events_option_six(ack, body, client):
    ack()
    team_id = body["user"]["team_id"]
    information_options_six = handle_some_action_option_six(
        ack, body, client), handle_some_action_option_six_label(ack, body, client)
    print(information_options_six)
    count = information_options_six[1]
    # obtenemos el id del usuario que ha enviado el formulario
    user_id = body["user"]["id"]
    user_info_submit_six = client.users_info(user=user_id)
    user_submit_real_name_six = user_info_submit_six["user"]["real_name"]
    option_six_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Hola {user_submit_real_name_six}, te escribo con la respuesta a la solicitud que creaste. :hand:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Recuerda que seleccionaste la opción: *Número :six:*, con estos datos: -canal{information_options_six} y -numero de mensajes: {count}."
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"En esta respuesta, podrás obtener un *resumen de cierta cantidad de mensajes {count} en cierto canal, para darte un contexto de lo que hablan los usuarios*."
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "En base a tu selección se obtuvo:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": ""
            }
        }
    ]

    # y el id del usuario que ha enviado el formulario
    response = get_resume_conversation(
        information_options_six[0], information_options_six[1],team_id)
    option_six_blocks[-1]["text"]["text"] = response
    client.chat_postMessage(channel=user_id, text="hola",
                            blocks=option_six_blocks, as_user=True)


################################################################################
# flask bolt_app --------------------------------------------------------------------
################################################################################
# region Flaskapp
app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)


@app.route('/sentiment', methods=['Post'])
def sentiment():
    return handler.handle(request)


@app.route('/slack/open_modal', methods=['POST'])
def modals():
    return handler.handle(request)


@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


@app.route("/slack/commands", methods=["POST"])
def slack_commands():
    return handler.handle(request)


@app.route("/slack/install", methods=["GET"])
def install():
    return handler.handle(request)


@app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)


@app.route("/chatgpt", methods=["POST"])
def chatgpt():
    return handler.handle(request)


@app.route("/test", methods=["GET"])
def test_endpoint():
    return "This is a test endpoint"


if "__main__" == __name__:
    #app.run(debug=True)
    app.run(port=3000, host="0.0.0.0")
