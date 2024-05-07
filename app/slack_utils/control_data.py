from collections import Counter
import os
import pandas as pd

from model import Model
from open_ai_connection import OpenAIConnection

model = Model()
gpt = OpenAIConnection()

# obtener todos los mensajes de un usuario en un canal
def get_user_only_chanel(user_id, channel_name):
    df = get_menssages_only_chanel(channel_name)
    df = df[df['user'] == user_id]
    messages = df['text'].tolist()
    
    response = gpt.traducir_texto(messages)

    #result = model.predict(messages)
    
    #sentiment_percentages = sentiemnt_count(result)
    #print(sentiment_percentages)
    print(response)

#obtener todos los mensajes de un usuario en todos los canales
def get_user_all_channels(user_id):
    df = get_all_channel()
    df = df[df['user'] == user_id]
    messages = df['text'].tolist()

    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    print(sentiment_percentages)
    print(result)

#obtener el sentimiento de todos los mensajes de todos los canales
def get_sentiment_all_channel():
    df = get_all_channel()
    messages = df['text'].tolist()

    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    print(sentiment_percentages)
    print(result)

#obtener el sentimiento de todos los mensajes de un canal
def get_sentiment_one_channel(channel_name):
    df = get_menssages_only_chanel(channel_name)
    messages = df['text'].tolist()

    result = model.predict(messages)
    sentiment_percentages = sentiemnt_count(result)
    print(sentiment_percentages)

    print(result)
#obtener el top 5 de sentimientos de todos los mensajes de un canal
def get_top_5_sentiment_one_channel(channel_name):
    df = get_menssages_only_chanel(channel_name)
    messages = df['text'].tolist()

    result = model.predict(messages)

    sentiments = [sentiment for _, sentiment in result]
    sentiment_counts = Counter(sentiments)
    top_5_sentiments = sentiment_counts.most_common(5)

    print(top_5_sentiments)

#obtener resumen de la conversacion de un canal
def get_resume_conversation(channel_name, countMessages):
    if countMessages < 5 or countMessages > 200:
        print("El número de mensajes debe ser mayor a 5 y menor a 200")
        return
    df = get_menssages_only_chanel(channel_name)
    df = df.head(countMessages)
    messages = df['text'].tolist()
    print(messages)


def get_menssages_only_chanel(channel_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, f'../slack_config/Data_messages/channel_{channel_name}_messages.csv')
    df = pd.read_csv(csv_path)
    return (df)

def get_all_channel():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, f'../slack_config/Data_messages')
    channel_names = [name.replace('channel_', '').replace('_messages.csv', '') for name in os.listdir(csv_path)]
    
    all_messages = pd.DataFrame()
    for channel_name in channel_names:
        df = pd.read_csv(os.path.join(csv_path, f'channel_{channel_name}_messages.csv'))
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
    get_user_only_chanel('U070C5QQS5U', 'varios')
    #get_user_all_channels('U071GEQ4J13')
    #get_sentiment_all_channel()
    #get_top_5_sentiment_one_channel('varios')
    #get_sentiment_one_channel('varios')
    #get_resume_conversation('varios', 6)