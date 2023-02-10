import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import List

import discord
import libsql_client
import modal
from dotenv import load_dotenv
from urlextract import URLExtract

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_API_TOKEN")
client = discord.Client(intents=intents)

stub = modal.Stub("yaig-summarizer")

def skip_channel(channel):
    if channel.name in ["introduce-yourself, twitter-handles", "Lounge"]:
            return True

    channels = [discord.CategoryChannel, discord.StageChannel]
    if any(map(lambda x: isinstance(channel, x), channels)):
        return True

    return False

async def write_messages(url, messages: List[discord.Message]):
    stmt = "INSERT INTO messages VALUES(?, ?, ?, ?, ?)"
    async with libsql_client.Client(url) as client:
        stmts = []
        for message in messages:
            stmt_obj = (stmt, (int(message.id), message.content, message.author.name, "", int(message.created_at.timestamp())))
            print(stmt_obj)
            stmts.append(stmt_obj)

        await client.batch(stmts)

async def store_interesting_messages():
    channels = client.get_all_channels()
    yesterday = datetime.today() - timedelta(days=1)
    extractor = URLExtract()
    messages = []
    print("Looping through channels...")
    for channel in channels:
        if skip_channel(channel):
            continue

        channel_obj = client.get_channel(channel.id)        
        try:
            async for message in channel_obj.history(after=yesterday):
                urls = extractor.find_urls(message.content)
                if(len(urls) > 0) or (len(message.reactions) > 0):
                    messages.append(message)

        except discord.errors.Forbidden:
            # Cannot find a easy way to test if a channel is private.
            continue

    print(f"Writing {len(messages)} messages to sql...")
    await write_messages(os.getenv("LIBSQL_URL"), messages)
    print(f"Finished writing messages")


@client.event
async def on_ready():
    try:
        await store_interesting_messages()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

    # Quit the discord bot
    sys.exit(0)

@stub.function
def run():
    client.run(token=token)

@stub.local_entrypoint
def main():
    run()