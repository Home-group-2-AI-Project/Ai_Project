from collections import Counter
import os
import pandas as pd

from slack_utils.model import Model
from slack_utils.open_ai_connection import OpenAIConnection
model = Model()
gpt = OpenAIConnection()
# obtener todos los mensajes de un usuario en un canal
def get_user_only_chanel(user_id, channel_name,team_id):
    df = get_menssages_only_chanel(channel_name,team_id)
    df = df[df['user'] == user_id]
    messages = df['text'].tolist()
    last_messages = messages[-5:]
    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    response = gpt.resumen_sentimientos_usuario_canal(user_id, channel_name, sentiment_percentages, last_messages)
    print(response)
    return response

#obtener todos los mensajes de un usuario en todos los canales
def get_user_all_channels(user_id,team_id):
    df = get_all_channel(team_id)
    df = df[df['user'] == user_id]
    messages = df['text'].tolist()
    last_messages = messages[-5:]
    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    response = gpt.resumen_sentimientos_usuario_general(sentiment_percentages, last_messages)
    return response

#obtener el sentimiento de todos los mensajes de todos los canales
def get_sentiment_all_channel(team_id):
    df = get_all_channel(team_id)
    messages = df['text'].tolist()
    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    response = gpt.resumen_sentimientos_todos_canales_general(sentiment_percentages)
    print(response) 
    return response

#obtener el sentimiento de todos los mensajes de un canal
def get_sentiment_one_channel(channel_name,team_id):
    df = get_menssages_only_chanel(channel_name,team_id)
    messages = df['text'].tolist()
    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    response = gpt.resumen_sentimientos_canal(channel_name, sentiment_percentages)
    print(response)
    return response

#obtener el top 5 de sentimientos de todos los mensajes de un canal
def get_top_5_sentiment_one_channel(channel_name,team_id):
    df = get_menssages_only_chanel(channel_name,team_id)
    messages = df['text'].tolist()

    result = model.predict(messages)

    sentiments = [sentiment for _, sentiment in result]
    sentiment_counts = Counter(sentiments)
    top_5_sentiments = sentiment_counts.most_common(5)
    response = gpt.resumen_top_5_sentimientos_canal(channel_name, top_5_sentiments)
    print(response)
    return response

#obtener resumen de la conversacion de un canal
def get_resume_conversation(channel_name, countMessages,team_id):
    if countMessages < 5 or countMessages > 200:
        print("El número de mensajes debe ser mayor a 5 y menor a 200")
        return
    df = get_menssages_only_chanel(channel_name,team_id)
    df = df.head(countMessages)
    messages = df['text'].tolist()
    response = gpt.resumen_contexto_ultimos_mensajes(channel_name, messages)
    return response


def get_menssages_only_chanel(channel_name,team_id):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, f'../slack_config/Data_messages/{team_id}_channel_{channel_name}_messages.csv')
    df = pd.read_csv(csv_path)
    return (df)

def get_all_channel(team_id):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, f'../slack_config/Data_messages')
    channel_names = [name.replace('channel_', '').replace('_messages.csv', '') for name in os.listdir(csv_path) if name.endswith('_messages.csv') and not name.endswith('.gitkeep_messages.csv')]
    
    all_messages = pd.DataFrame()
    for channel_name in channel_names:
        df = pd.read_csv(os.path.join(csv_path, f'{team_id}_channel_{channel_name}_messages.csv'))
        all_messages = pd.concat([all_messages, df]) 

    return (all_messages)

def sentiemnt_count(result_model):
    sentiments = [sentiment for _, sentiment in result_model]

    # Calcular el total de mensajes después de la predicción
    total_messages = len(sentiments)
    # Contar las ocurrencias de cada sentimiento
    sentiment_counts = Counter(sentiments)
    # Calcular el porcentaje de cada sentimiento
    sentiment_percentages = {sentiment: count / total_messages * 100 for sentiment, count in sentiment_counts.items()}

    return sentiment_percentages

if __name__ == '__main__':
    get_user_only_chanel('U070C5QQS5U', 'U070C5QQS5U')
    #get_user_all_channels('U071GEQ4J13')
    #get_sentiment_all_channel()
    #get_sentiment_one_channel('varios')
    #get_top_5_sentiment_one_channel('varios')
    get_resume_conversation('varios', 6)