import discord
import requests
import os
import asyncio

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL_SERVER_1 = os.getenv('WEBHOOK_URL_SERVER_1')
WEBHOOK_URL_SERVER_2 = os.getenv('WEBHOOK_URL_SERVER_2')
WEBHOOK_URL_SERVER_3 = os.getenv('WEBHOOK_URL_SERVER_3')

CHANNEL_ID_SERVER_1 = int(os.getenv('CHANNEL_ID_SERVER_1'))
CHANNEL_ID_SERVER_2 = int(os.getenv('CHANNEL_ID_SERVER_2'))
CHANNEL_ID_SERVER_3 = int(os.getenv('CHANNEL_ID_SERVER_3'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

client = discord.Client(intents=intents)

message_map = {}  # {source_message_id: [(webhook_url, message_id), ...]}


def send_webhook(url, username, avatar_url, content, reply_to=None):
    try:
        data = {"username": username, "avatar_url": avatar_url, "content": content}
        if reply_to:
            data["embeds"] = [
                {
                    "description": f"Réponse à : {reply_to}",
                    "color": 3447003,  # Optional embed color
                }
            ]
        result = requests.post(url, json=data)
        result.raise_for_status()
        return result.json().get("id")
    except Exception as e:
        print(f"Error sending webhook to {url}: {e}")
        return None


def send_file_webhook(url, username, avatar_url, file_url, content, reply_to=None):
    try:
        data = {
            "username": username,
            "avatar_url": avatar_url,
            "content": content,
            "embeds": [{"image": {"url": file_url}}],
        }
        if reply_to:
            data["embeds"].insert(0, {"description": f"Réponse à : {reply_to}"})
        result = requests.post(url, json=data)
        result.raise_for_status()
        return result.json().get("id")
    except Exception as e:
        print(f"Error sending file webhook to {url}: {e}")
        return None


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(update_status())


async def update_status():
    while True:
        latency = round(client.latency * 1000)
        total_users = sum(guild.member_count for guild in client.guilds)
        await client.change_presence(
            activity=discord.Game(f"Ping: {latency}ms | Users: {total_users}")
        )
        await asyncio.sleep(20)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    webhook_urls = []
    if message.channel.id == CHANNEL_ID_SERVER_1:
        webhook_urls = [WEBHOOK_URL_SERVER_2, WEBHOOK_URL_SERVER_3]
    elif message.channel.id == CHANNEL_ID_SERVER_2:
        webhook_urls = [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_3]
    elif message.channel.id == CHANNEL_ID_SERVER_3:
        webhook_urls = [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_2]

    reply_to = None
    if message.reference and message.reference.message_id in message_map:
        reply_to = f"{message.reference.resolved.content}"

    if webhook_urls:
        sent_messages = []
        for url in webhook_urls:
            if message.attachments:
                for attachment in message.attachments:
                    msg_id = send_file_webhook(
                        url,
                        message.author.display_name,
                        str(message.author.avatar.url),
                        attachment.url,
                        message.content,
                        reply_to,
                    )
                    if msg_id:
                        sent_messages.append((url, msg_id))
            else:
                msg_id = send_webhook(
                    url,
                    message.author.display_name,
                    str(message.author.avatar.url),
                    message.content,
                    reply_to,
                )
                if msg_id:
                    sent_messages.append((url, msg_id))

        if sent_messages:
            message_map[message.id] = sent_messages


@client.event
async def on_message_delete(message):
    if message.id in message_map:
        for url, msg_id in message_map[message.id]:
            try:
                requests.delete(f"{url}/messages/{msg_id}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to delete message {msg_id} from webhook: {e}")
        del message_map[message.id]


@client.event
async def on_message_edit(before, after):
    if after.id in message_map:
        for url, msg_id in message_map[after.id]:
            try:
                data = {"content": after.content}
                requests.patch(f"{url}/messages/{msg_id}", json=data)
            except requests.exceptions.RequestException as e:
                print(f"Failed to edit message {msg_id} from webhook: {e}")


@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in message_map:
        for url, msg_id in message_map[reaction.message.id]:
            try:
                emoji = reaction.emoji
                requests.put(f"{url}/messages/{msg_id}/reactions/{emoji}/@me")
            except requests.exceptions.RequestException as e:
                print(f"Failed to add reaction {emoji} to message {msg_id}: {e}")


@client.event
async def on_reaction_remove(reaction, user):
    if reaction.message.id in message_map:
        for url, msg_id in message_map[reaction.message.id]:
            try:
                emoji = reaction.emoji
                requests.delete(f"{url}/messages/{msg_id}/reactions/{emoji}/@me")
            except requests.exceptions.RequestException as e:
                print(f"Failed to remove reaction {emoji} from message {msg_id}: {e}")


client.run(BOT_TOKEN)
