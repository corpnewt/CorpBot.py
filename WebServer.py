from flask import Flask
import urllib
from chatterbot import ChatBot

app = Flask(__name__)

chatBot = ChatBot('Pooter', trainer='chatterbot.trainers.ChatterBotCorpusTrainer')
chatBot.train('chatterbot.corpus.english')

@app.route('/chat/<chatsay>')
def chat(chatsay):
    # With Pooter, only allow content to go through - no empty messages
    msg = str(chatBot.get_response(urllib.parse.unquote(chatsay)))
    return msg