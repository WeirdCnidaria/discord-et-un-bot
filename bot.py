import discord
from deck.deck import Deck
from os import environ
from dotenv import load_dotenv

# Getting the bot API key from the .env file
load_dotenv()
API_KEY = environ["DISCORD_API_KEY"]

deck = Deck()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "!newdeck":
        deck = Deck()
    elif message.content == "!draw":
        deck.draw()
    elif message.content == "!clear":
        deck.clear_hand()
    elif message.content == "!reshuffle":
        deck.reshuffle()
    elif message.content == "!hand":
        for card in deck.played_cards:
            await message.channel.send(card.suit + " " +  card.rank)

client.run(API_KEY)
