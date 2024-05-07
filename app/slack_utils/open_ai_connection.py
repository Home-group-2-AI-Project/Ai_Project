import os
import openai
from langdetect import detect

from dotenv import load_dotenv


class OpenAIConnection:
    """
    Esta clase se encarga de realizar las peticiones a la API de OpenAI
    """

    def __init__(self):
        load_dotenv()
        self.client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )

    def chat_gpt(self, mensaje):
        """
        Esta función recibe un texto y devuelve una respuesta generada por el modelo
        """

        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente de bot en slack que se encarga de responder a los usuarios."},
                {"role": "user", "content": mensaje}
            ]
        )

        response_text = respuesta.choices[0].message.content
        return response_text

    def resumen_sentimientos_usuario_canal(self, nombre_usuario, canal, resultados, mensajes=None):
        """
        Esta función recibe el nombre de un usuario, los resultados obtenidos
        por el modelo de clasificacion y algunos mensajes de ejemplo del usuario.
        Devuelve un resumen de los sentimnientos del usuario.
        """

        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un bot de slack y vamos a analizar los sentimientos de {nombre_usuario} en el canal {canal}."},
                {"role": "user", "content": f"Dame un resumen con los resultados que te voy a proporcionar sobre los sentimientos de {nombre_usuario} en el canal {canal}."},
                {"role": "user", "content": f"Los resultados son los siguientes: {resultados}"},
                {"role": "user", "content": f"Mensajes de ejemplo de esta persona son estos: {mensajes}"},
                {"role": "user", "content": f"Dame una respuesta bien estructurada y saca tus conclusiones con los datos proporcionados y los mensajes que te proporcioné sobre las interacciones de la persona. Recuerda que los resultados se obtienen despues de pasar por un modelo de clasificacion de sentimientos."}
            ]
        )

        response_text = respuesta.choices[0].message.content
        return response_text

    def resumen_sentimientos_usuario_general(self, nombre_usuario, resultados, mensajes=None):
        """
        Esta función recibe el nombre de un usuario, los resultados obtenidos
        por el modelo de clasificacion y algunos mensajes de ejemplo del usuario.
        Devuelve un resumen de los sentimientos en general del usuario.
        """

        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un bot de slack y vamos a analizar los sentimientos de {nombre_usuario}."},
                {"role": "user", "content": f"Dame un resumen con los resultados que te voy a proporcionar sobre los sentimientos de {nombre_usuario}."},
                {"role": "user", "content": f"Los resultados son los siguientes: {resultados}"},
                {"role": "user", "content": f"Mensajes de ejemplo de esta persona son estos: {mensajes}"},
                {"role": "user", "content": f"Dame una respuesta bien estructurada y saca tus conclusiones con los datos proporcionados y los mensajes que te proporcioné sobre las interacciones de la persona en todos los canales en los que esta. Recuerda que los resultados se obtienen despues de pasar por un modelo de clasificacion de sentimientos."}
            ]
        )

        response_text = respuesta.choices[0].message.content
        return response_text

    def resumen_sentimientos_canal(self, canal, resultados):
        """
        Esta función recibe el nombre de un canal, los resultados obtenidos por
        el modelo de clasificacion sobre algunos ejemplos del canal.
        Devuelve un resumen de los sentimnientos del canal.
        """

        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un bot de slack y vamos a analizar los sentimientos del canal {canal}."},
                {"role": "user", "content": f"Dame un resumen con los resultados que te voy a proporcionar sobre los sentimientos del canal {canal}."},
                {"role": "user", "content": f"Los resultados son los siguientes: {resultados}"},
                {"role": "user", "content": f"Dame una respuesta bien estructurada y saca tus conclusiones con los datos proporcionados y los mensajes que te proporcioné sobre las interacciones del canal. Recuerda que los resultados se obtienen despues de pasar por un modelo de clasificacion de sentimientos."}
            ]
        )

        response_text = respuesta.choices[0].message.content
        return response_text

    def resumen_top_usuarios(self, canal, resultados):
        """
        Esta función recibe los resultados obtenidos por  el modelo de
        clasificacion sobre los top usuarios clasificados con sentimientos.
        """

        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un bot de slack y vamos a analizar los usuarios que mas representan ciertos sentimientos en un el canal {canal}."},
                {"role": "user", "content": f"Dame un resumen con los resultados que te voy a proporcionar sobre los sentimientos de los usuarios en el canal {canal}."},
                {"role": "user", "content": f"Los resultados son los siguientes: {resultados}"},
                {"role": "user", "content": f"Dame una respuesta bien estructurada y saca tus conclusiones con los datos proporcionados sobre los usuarios en el canal. Recuerda que los resultados se obtienen despues de pasar por un modelo de clasificacion de sentimientos. Brinda un mensaje a cada usuario que represente el sentimiento que mas predomina en sus mensajes."}
            ]
        )

        response_text = respuesta.choices[0].message.content
        return response_text

    def resumen_contexto_ultimos_mensajes(self, canal, mensajes):
        """
        Esta función recibe los mensajes de un canal y devuelve un resumen
        de lo que se esta hablando en estos mensajes.
        """

        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Eres un bot de slack y vamos a analizar los mensajes del canal {canal}."},
                {"role": "user", "content": f"Los mensajes son los siguientes: {mensajes}"},
                {"role": "user", "content": "Dame una respuesta bien estructurada y saca tus conclusiones y un resumen de lo que se está hablando en este hilo de conversación."}
            ]
        )

        response_text = respuesta.choices[0].message.content
        return response_text
    
    def traducir_texto(self, textos):
        """
        Esta función recibe una lista de textos y devuelve una lista de traducciones al inglés
        """

        traducciones = []
        for texto in textos:
            # Detectar el idioma del texto
            respuesta = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that translates text into English."},
                    {"role": "user", "content": "PREGUNTA: " + texto}
                ]
            )

            response_text = respuesta.choices[0].message.content

            if response_text.startswith("QUESTION:"):
                traduccion = response_text.split(": ", 1)[1]
            else:
                traduccion = texto  # Mantener el texto original si no es una respuesta esperada
            traducciones.append(traduccion)

        return traducciones
    
    def traducir_un_texto(self, texto):
        """
        Esta función recibe un texto y devuelve la traducción al inglés
        """
        # Detectar el idioma del texto
        respuesta = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that translates text into English."},
                {"role": "user", "content": "PREGUNTA: " + texto}
            ]
        )

        response_text = respuesta.choices[0].message.content
        if response_text.startswith("QUESTION:"):
            traduccion = response_text.split(": ", 1)[1]
        else:
            traduccion = texto  # Mantener el texto original si no es una respuesta esperada

        return traduccion
