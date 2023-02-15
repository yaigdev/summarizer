import discord
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
from urlextract import URLExtract
import libsql_client
from typing import List
from dataclasses import dataclass
import traceback
import modal

image = modal.Image.debian_slim()
image = image.pip_install_from_requirements("requirements.txt")

stub = modal.Stub("yaig-summarizer", image=image)

def skip_channel(channel):
    if channel.name in ["introduce-yourself, twitter-handles", "Lounge"]:
            return True

    channels = [discord.CategoryChannel, discord.StageChannel]
    if any(map(lambda x: isinstance(channel, x), channels)):
        return True

    return False

def count_reactions(message: discord.Message):
    count = 0
    for r in message.reactions:
        count += r.count
    return count

async def write_messages(client, url, messages: List[discord.Message]):
    stmt = "INSERT OR IGNORE INTO messages VALUES(?, ?, ?, ?, ?, ?)"
    async with libsql_client.Client(url) as client:
        stmts = []
        for message in messages:
            stmt_obj = (stmt, (message.id, message.content, message.channel.name, message.author.name, count_reactions(message), message.created_at.timestamp()))
            stmts.append(stmt_obj)

        await client.batch(stmts)

async def scrape_messages(client, libsql_url: str):
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
    await write_messages(client, libsql_url, messages)
    print(f"Finished writing messages")

@stub.function(
    secret=modal.Secret.from_name("summarizer"),
    schedule=modal.Period(days=1)
)
def run():
    load_dotenv()
    intents = discord.Intents.default()
    intents.message_content = True
    token = os.getenv("DISCORD_API_TOKEN")
    libsql_url = os.getenv("LIBSQL_URL")
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            await scrape_messages(client, libsql_url)
        except Exception as e:
            traceback.print_exc()
            sys.exit(1)

        await client.close()

    client.run(token=token)

if __name__ == "__main__":
    with stub.run():
        run()