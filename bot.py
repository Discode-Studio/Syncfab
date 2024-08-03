import discord
import requests
import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL_SERVER_1 = os.getenv('WEBHOOK_URL_SERVER_1')
WEBHOOK_URL_SERVER_2 = os.getenv('WEBHOOK_URL_SERVER_2')
CHANNEL_ID_SERVER_1 = int(os.getenv('CHANNEL_ID_SERVER_1'))
CHANNEL_ID_SERVER_2 = int(os.getenv('CHANNEL_ID_SERVER_2'))

# Ajouter les variables pour le nom du serveur et le lien d'invitation
SERVER_NAME_1 = "BlugrayGuy"
INVITE_LINK_1 = "https://discord.com/invite/8cvwaUACK9"

SERVER_NAME_2 = "Elite AstroToilet"
INVITE_LINK_2 = "https://discord.com/invite/GDdAgRuPFs"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

def send_webhook(url, username, avatar_url, content, server_name, invite_link):
    # Formater la signature avec le nom du serveur et le lien d'invitation
    signature = f"-# sent from [{server_name}](<{invite_link}>)"
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": f"{content}\n{signature}"
    }
    result = requests.post(url, json=data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)

def send_file_webhook(url, username, avatar_url, file_url, content, server_name, invite_link):
    # Formater la signature avec le nom du serveur et le lien d'invitation
    signature = f"-# sent from [{server_name}](<{invite_link}>)"
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": f"{content}\n{signature}",
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

    if message.channel.id == CHANNEL_ID_SERVER_1:
        send_webhook(WEBHOOK_URL_SERVER_2, message.author.display_name, str(message.author.avatar.url), message.content, SERVER_NAME_2, INVITE_LINK_2)
    elif message.channel.id == CHANNEL_ID_SERVER_2:
        send_webhook(WEBHOOK_URL_SERVER_1, message.author.display_name, str(message.author.avatar.url), message.content, SERVER_NAME_1, INVITE_LINK_1)

client.run(BOT_TOKEN)
