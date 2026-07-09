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
tree = discord.app_commands.CommandTree(client)

@tree.command(
    name = "new_deck",
    description = "Makes a new deck"
)
async def new_deck(interaction):
    global deck
    deck = Deck()
    await interaction.response.send_message("Deck reset")

@tree.command(
    name = "draw",
    description = "Draw a card"
)
async def draw(interaction):
    global deck
    deck.draw()
    await interaction.response.send_message(f"Drawn {deck.played_deck[-1].rank} of {deck.played_deck[-1].suit}")

@tree.command(
    name = "clear",
    description = "Discard all drawn cards"
)
async def clear(interaction):
    global deck
    deck.clear_hand()
    await interaction.response.send_message("Cards cleared")

@tree.command(
    name = "reshuffle",
    description = "Reshuffle discarded cards back into the deck"
)
async def reshuffle(interaction):
    global deck
    deck.reshuffle()
    await interaction.response.send_message("Deck reshuffled")

@tree.command(
    name = "hand",
    description = "Shows drawn cards"
)
async def test(interaction):
    global deck
    message_string = str()
    for card in deck.played_deck:
        message_string += card.rank.capitalize() + " of " + card.suit + "\n"
    message_string = message_string[:-1]
    if message_string == "":
        message_string = "The hand is empty"
    await interaction.response.send_message(message_string)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

#@client.event
#async def on_message(message):
#    if message.author == client.user:
#        return
#
#    global deck
#    if message.content == "!newdeck":
#        deck = Deck()
#    elif message.content == "!draw":
#        deck.draw()
#    elif message.content == "!clear":
#        deck.clear_hand()
#    elif message.content == "!reshuffle":
#        deck.reshuffle()
#    elif message.content == "!hand":
#        for card in deck.played_deck:
#            await message.channel.send(card.suit + " " +  card.rank)

client.run(API_KEY)
