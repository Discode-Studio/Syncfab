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


def send_webhook(url, username, avatar_url, content, files=None):
    try:
        data = {"username": username, "avatar_url": avatar_url, "content": content}
        files_to_send = []

        if files:
            for file in files:
                files_to_send.append(('file', (file.filename, file.fp, file.content_type)))

        headers = {}
        response = requests.post(url, data=data, files=files_to_send, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending webhook to {url}: {e}")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    # Commande "sn!talk" réservée à l'utilisateur avec l'ID spécifié
    if isinstance(message.channel, discord.DMChannel) and message.author.id == 659349596534734856:
        if message.content.startswith("sn!talk"):
            args = message.content.split()
            if len(args) < 4:
                await message.channel.send("Usage : `sn!talk (serverid) (channelid) (message)`")
                return

            server_id = int(args[1])
            channel_id = int(args[2])
            msg_content = " ".join(args[3:])

            guild = client.get_guild(server_id)
            if not guild:
                await message.channel.send("Serveur introuvable.")
                return

            channel = guild.get_channel(channel_id)
            if not channel:
                await message.channel.send("Salon introuvable.")
                return

            try:
                await channel.send(msg_content)
                await message.channel.send("Message envoyé avec succès.")
            except Exception as e:
                await message.channel.send(f"Erreur lors de l'envoi du message : {e}")
                return

    # Gestion des webhooks
    if message.channel.id in webhook_map:
        files = []

        if message.attachments:
            for attachment in message.attachments:
                # Téléchargez chaque pièce jointe et stockez-la temporairement
                file = await attachment.to_file()
                files.append({
                    "filename": file.filename,
                    "fp": file.fp,
                    "content_type": attachment.content_type
                })

        for webhook_url in webhook_map[message.channel.id]:
            if message.reference:
                # Gestion des réponses avec mention
                replied_message = await message.channel.fetch_message(message.reference.message_id)
                if replied_message:
                    content = (
                        f"**{message.author.mention} replied to {replied_message.author.mention}:**\n"
                        f"> {replied_message.content}\n\n"
                        f"{message.content}"
                    )
                else:
                    content = f"{message.content}"
            else:
                # Message normal
                content = f"{message.content}"

            send_webhook(webhook_url, message.author.display_name, str(message.author.avatar.url), content, files)


@client.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    if before.channel.id in webhook_map:
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
        for channel_id in webhook_map[message.channel.id]:
            target_channel = discord.utils.get(client.get_all_channels(), id=channel_id)
            if target_channel:
                await target_channel.send(
                    f"**{message.author.display_name} deleted a message:**\nContent: {message.content}"
                )


client.run(BOT_TOKEN)
