import discord
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from urlextract import URLExtract

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_API_TOKEN")   
client = discord.Client(intents=intents)

def skip_channel(channel):
    if channel.name == "introduce-yourself":
            return True

    if isinstance(channel, discord.CategoryChannel) or isinstance(channel, discord.StageChannel):
            return True

    return False

@client.event
async def on_ready():
    channels = client.get_all_channels()
    yesterday = datetime.now() - timedelta(days=1)
    extractor = URLExtract()
    for channel in channels:
        if skip_channel(channel):
            continue

        print(channel.name)
        channel_obj = client.get_channel(channel.id)        
        try:
            async for message in channel_obj.history(after=yesterday):
                urls = extractor.find_urls(message.content)
                if(len(urls) > 0):
                    print(message.content)

        except discord.errors.Forbidden:
            continue

if __name__ == "__main__":    
    client.run(token=token)