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

# Mapping des webhooks
webhook_map = {
    CHANNEL_ID_SERVER_1: [WEBHOOK_URL_SERVER_2, WEBHOOK_URL_SERVER_3],
    CHANNEL_ID_SERVER_2: [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_3],
    CHANNEL_ID_SERVER_3: [WEBHOOK_URL_SERVER_1, WEBHOOK_URL_SERVER_2],
}

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)


def send_webhook(url, username, avatar_url, content):
    try:
        data = {"username": username, "avatar_url": avatar_url, "content": content}
        result = requests.post(url, json=data)
        result.raise_for_status()
    except Exception as e:
        print(f"Error sending webhook to {url}: {e}")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in webhook_map:
        for webhook_url in webhook_map[message.channel.id]:
            # Synchroniser les messages normaux via webhook
            if message.reference:
                # Gestion des réponses
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                if replied_message:
                    content = (
                        f"**{message.author.display_name} replied to {replied_message.author.display_name}:**\n"
                        f"> {replied_message.content}\n\n"
                        f"{message.content}"
                    )
                else:
                    content = f"{message.content}"
            else:
                # Message normal
                content = f"{message.author.display_name}: {message.content}"

            send_webhook(webhook_url, message.author.display_name, str(message.author.avatar.url), content)


@client.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    if before.channel.id in webhook_map:
        # Annoncer les messages modifiés via le bot
        for channel_id in webhook_map[before.channel.id]:
            target_channel = discord.utils.get(client.get_all_channels(), id=channel_id)
            if target_channel:
                await target_channel.send(
                    f"**{before.author.display_name} edited a message:**\n"
                    f"Before: {before.content}\n"
                    f"After: {after.content}"
                )


@client.event
async def on_message_delete(message):
    if message.author.bot:
        return

    if message.channel.id in webhook_map:
        # Annoncer les messages supprimés via le bot
        for channel_id in webhook_map[message.channel.id]:
            target_channel = discord.utils.get(client.get_all_channels(), id=channel_id)
            if target_channel:
                await target_channel.send(
                    f"**{message.author.display_name} deleted a message:**\nContent: {message.content}"
                )


client.run(BOT_TOKEN)
