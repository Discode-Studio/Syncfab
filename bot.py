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
intents.reactions = True

client = discord.Client(intents=intents)

# Map messages across servers: {source_message_id: [(webhook_url, message_id), ...]}
message_map = {}


def send_webhook(url, username, avatar_url, content, embed=None):
    """
    Sends a message using a webhook and returns the ID of the message sent.
    """
    try:
        data = {"username": username, "avatar_url": avatar_url, "content": content}
        if embed:
            data["embeds"] = [embed]
        result = requests.post(url, json=data)
        result.raise_for_status()
        return result.json().get("id")
    except Exception as e:
        print(f"Error sending webhook to {url}: {e}")
        return None


def edit_webhook_message(url, message_id, content):
    """
    Edits a webhook message.
    """
    try:
        data = {"content": content}
        requests.patch(f"{url}/messages/{message_id}", json=data)
    except Exception as e:
        print(f"Error editing message {message_id}: {e}")


def delete_webhook_message(url, message_id):
    """
    Deletes a webhook message.
    """
    try:
        requests.delete(f"{url}/messages/{message_id}")
    except Exception as e:
        print(f"Error deleting message {message_id}: {e}")


def react_to_webhook_message(url, message_id, emoji, action="add"):
    """
    Adds or removes a reaction from a webhook message.
    """
    try:
        if action == "add":
            requests.put(f"{url}/messages/{message_id}/reactions/{emoji}/@me")
        elif action == "remove":
            requests.delete(f"{url}/messages/{message_id}/reactions/{emoji}/@me")
    except Exception as e:
        print(f"Error managing reaction {emoji} on message {message_id}: {e}")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Determine which webhooks to send to
    webhook_urls = []
    if message.channel.id == CHANNEL_ID_SERVER_1:
        webhook_urls = [WEBHOOK_URL_SERVER_2, WEBHOOK_URL_SERVER_3]
    elif message.channel.id == CHANNEL_ID_SERVER_2:
        webhook_urls = [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_3]
    elif message.channel.id == CHANNEL_ID_SERVER_3:
        webhook_urls = [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_2]

    # Send message via webhooks
    sent_messages = []
    for url in webhook_urls:
        embed = None
        if message.reference and message.reference.message_id in message_map:
            referenced_message = message_map[message.reference.message_id][0]
            embed = {"description": f"Réponse à : {referenced_message}"}

        msg_id = send_webhook(
            url,
            username=message.author.display_name,
            avatar_url=str(message.author.avatar.url),
            content=message.content,
            embed=embed,
        )
        if msg_id:
            sent_messages.append((url, msg_id))

    if sent_messages:
        message_map[message.id] = sent_messages


@client.event
async def on_message_edit(before, after):
    if after.id in message_map:
        for url, msg_id in message_map[after.id]:
            edit_webhook_message(url, msg_id, after.content)


@client.event
async def on_message_delete(message):
    if message.id in message_map:
        for url, msg_id in message_map[message.id]:
            delete_webhook_message(url, msg_id)
        del message_map[message.id]


@client.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in message_map:
        for url, msg_id in message_map[reaction.message.id]:
            react_to_webhook_message(url, msg_id, reaction.emoji, action="add")


@client.event
async def on_reaction_remove(reaction, user):
    if reaction.message.id in message_map:
        for url, msg_id in message_map[reaction.message.id]:
            react_to_webhook_message(url, msg_id, reaction.emoji, action="remove")


client.run(BOT_TOKEN)
