import discord
import os
import asyncio

BOT_TOKEN = os.getenv('BOT_TOKEN')

CHANNEL_ID_SERVER_1 = int(os.getenv('CHANNEL_ID_SERVER_1'))
CHANNEL_ID_SERVER_2 = int(os.getenv('CHANNEL_ID_SERVER_2'))
CHANNEL_ID_SERVER_3 = int(os.getenv('CHANNEL_ID_SERVER_3'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)

channel_map = {
    CHANNEL_ID_SERVER_1: [CHANNEL_ID_SERVER_2, CHANNEL_ID_SERVER_3],
    CHANNEL_ID_SERVER_2: [CHANNEL_ID_SERVER_1, CHANNEL_ID_SERVER_3],
    CHANNEL_ID_SERVER_3: [CHANNEL_ID_SERVER_1, CHANNEL_ID_SERVER_2],
}


async def broadcast_message(source_channel_id, message_content):
    """
    Broadcasts a message to all other linked channels.
    """
    if source_channel_id not in channel_map:
        return

    for channel_id in channel_map[source_channel_id]:
        channel = client.get_channel(channel_id)
        if channel:
            await channel.send(message_content)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Handle reply
    if message.reference:
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        if replied_message:
            content = (
                f"**{message.author.display_name} replied to {replied_message.author.display_name}:**\n"
                f"> {replied_message.content}\n\n"
                f"{message.content}"
            )
            await broadcast_message(message.channel.id, content)
    else:
        # Broadcast regular messages (optional)
        pass


@client.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    content = (
        f"**{before.author.display_name} edited a message:**\n"
        f"Before: {before.content}\n"
        f"After: {after.content}"
    )
    await broadcast_message(before.channel.id, content)


@client.event
async def on_message_delete(message):
    if message.author.bot:
        return

    content = (
        f"**{message.author.display_name} deleted a message:**\n"
        f"Content: {message.content}"
    )
    await broadcast_message(message.channel.id, content)


client.run(BOT_TOKEN)
