import discord
import requests
import os
import asyncio

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL_SERVER_1 = os.getenv('WEBHOOK_URL_SERVER_1')
WEBHOOK_URL_SERVER_2 = os.getenv('WEBHOOK_URL_SERVER_2')
WEBHOOK_URL_SERVER_3 = os.getenv('WEBHOOK_URL_SERVER_3')  # Webhook du serveur 3

CHANNEL_ID_SERVER_1 = int(os.getenv('CHANNEL_ID_SERVER_1'))
CHANNEL_ID_SERVER_2 = int(os.getenv('CHANNEL_ID_SERVER_2'))
CHANNEL_ID_SERVER_3 = int(os.getenv('CHANNEL_ID_SERVER_3'))  # ID du channel du serveur 3

SERVER_NAME_1 = "Elite AstroToilet"
INVITE_LINK_1 = "https://discord.com/invite/GDdAgRuPFs"

SERVER_NAME_2 = "BlugrayGuy"
INVITE_LINK_2 = "https://discord.com/invite/8cvwaUACK9"

SERVER_NAME_3 = "GoofYZ's Little Sigma"
INVITE_LINK_3 = "https://discord.gg/WjPm5Eq78U"  # Remplace par le lien d'invitation

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)

message_map = {}  # Dictionnaire pour mapper les messages entre les serveurs

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
    return result.json().get("id")  # Retourne l'ID du message

def send_file_webhook(url, username, avatar_url, file_url, content):
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": content,
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
    return result.json().get("id")  # Retourne l'ID du message

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(update_status())

async def update_status():
    while True:
        latency = round(client.latency * 1000)
        total_users = sum(guild.member_count for guild in client.guilds)
        await client.change_presence(activity=discord.Game(f'Ping: {latency}ms | Users: {total_users}'))
        await asyncio.sleep(20)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Bloquer les mentions @everyone et @here sauf pour les modérateurs
    if any(mention in message.content for mention in ["@everyone", "@here"]) and not message.author.guild_permissions.administrator:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, you are not allowed to use @everyone or @here mentions.", delete_after=10)
        return

    # Synchronisation des messages entre les trois serveurs
    if message.channel.id == CHANNEL_ID_SERVER_1:
        webhook_urls = [WEBHOOK_URL_SERVER_2, WEBHOOK_URL_SERVER_3]
    elif message.channel.id == CHANNEL_ID_SERVER_2:
        webhook_urls = [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_3]
    elif message.channel.id == CHANNEL_ID_SERVER_3:
        webhook_urls = [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_2]
    else:
        return

    for url in webhook_urls:
        if message.attachments:
            for attachment in message.attachments:
                message_id = send_file_webhook(url, message.author.display_name, str(message.author.avatar.url), attachment.url, message.content)
        else:
            message_id = send_webhook(url, message.author.display_name, str(message.author.avatar.url), message.content)
        message_map[message.id] = (url, message_id)

@client.event
async def on_message_delete(message):
    if message.id in message_map:
        url, msg_id = message_map[message.id]
        try:
            requests.delete(f"{url}/messages/{msg_id}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to delete message {msg_id} from webhook: {e}")
        del message_map[message.id]

client.run(BOT_TOKEN)
