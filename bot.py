import discord
import requests
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL_SERVER_1 = os.getenv('WEBHOOK_URL_SERVER_1')
WEBHOOK_URL_SERVER_2 = os.getenv('WEBHOOK_URL_SERVER_2')
CHANNEL_ID_SERVER_1 = int(os.getenv('CHANNEL_ID_SERVER_1'))
CHANNEL_ID_SERVER_2 = int(os.getenv('CHANNEL_ID_SERVER_2'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

def send_webhook(url, username, avatar_url, content):
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": content
    }
    result = requests.post(url, json=data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == CHANNEL_ID_SERVER_1:
        send_webhook(WEBHOOK_URL_SERVER_2, message.author.display_name, str(message.author.avatar.url), message.content)
    elif message.channel.id == CHANNEL_ID_SERVER_2:
        send_webhook(WEBHOOK_URL_SERVER_1, message.author.display_name, str(message.author.avatar.url), message.content)

client.run(BOT_TOKEN)
