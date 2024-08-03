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
    # Format correct de la signature pour éviter les embeds
    signature = "-# sent from [{}](<{}>)".format(username, url)
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": "{}\n\n{}".format(content, signature)
    }
    result = requests.post(url, json=data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)

def send_file_webhook(url, username, avatar_url, file_url, content):
    # Format correct de la signature pour éviter les embeds
    signature = "# sent from [{}]({})".format(username, url)
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": "{}\n\n{}".format(content, signature),
        "embeds": [{
            "image": {
                "url": file_url
            }
        }]
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

    target_webhook_url = None
    if message.channel.id == CHANNEL_ID_SERVER_1:
        target_webhook_url = WEBHOOK_URL_SERVER_2
    elif message.channel.id == CHANNEL_ID_SERVER_2:
        target_webhook_url = WEBHOOK_URL_SERVER_1

    if target_webhook_url:
        username = message.author.display_name
        avatar_url = str(message.author.avatar.url)
        if message.attachments:
            for attachment in message.attachments:
                send_file_webhook(target_webhook_url, username, avatar_url, attachment.url, message.content)
        else:
            send_webhook(target_webhook_url, username, avatar_url, message.content)

client.run(BOT_TOKEN)
