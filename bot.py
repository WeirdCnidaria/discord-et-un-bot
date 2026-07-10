from os import environ
from dotenv import load_dotenv
import discord
from deck import Deck
from image_processing import create_hand_image

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
@discord.app_commands.describe(amount = "How many standard 52 card decks should be used")
async def new_deck(interaction, amount: int):
    global deck
    if amount < 1:
        amount = 1
        await interaction.response.send_message("Invalid amount. Using 1 deck instead")
    deck = Deck(deck_amount=amount)
    await interaction.response.send_message(f"Deck reset. Starting with {amount} deck(s) of cards")

#@tree.command(
#    name = "draw",
#    description = "Draw a card"
#)
#async def draw(interaction):
#    global deck
#    deck.draw()
#    await interaction.response.send_message(f"Drawn {deck.played_deck[-1].rank} of {deck.played_deck[-1].suit}")
#
#@tree.command(
#    name = "clear",
#    description = "Discard all drawn cards"
#)
#async def clear(interaction):
#    global deck
#    deck.clear_hand()
#    await interaction.response.send_message("Cards cleared")
#
#@tree.command(
#    name = "reshuffle",
#    description = "Reshuffle discarded cards back into the deck"
#)
#async def reshuffle(interaction):
#    global deck
#    deck.reshuffle()
#    await interaction.response.send_message("Deck reshuffled")
#
#@tree.command(
#    name = "hand",
#    description = "Shows drawn cards"
#)
#async def test(interaction):
#    global deck
#    await interaction.response.send_message(deck.hand_string())
#
#@tree.command(
#    name = "evaluate",
#    description = "Calculate the score on the cards"
#)
#@discord.app_commands.describe(cap = "The max score before a burst. In classic blackjack it's 21")
#async def evaluate(interaction, cap: int):
#    global deck
#    if cap < 2:
#        cap = 21
#        await interaction.response.send_message("Invalid cap. Setting the cap to 21")
#    evaluation = deck.evaluate(cap)
#    if evaluation > cap:
#        evaluation = "BURST"
#    await interaction.response.send_message(f"The score on the cards is {evaluation}")

class HandView(discord.ui.View):
    def __init__(self, cap):
        super().__init__(timeout=None)
        self.hand_image = None
        self.reshuffled = False
        self.cap = cap
    def make_embed(self):
        if self.reshuffled:
            embed = discord.Embed(title=f"Et Un test ------ {len(deck.table_deck)} 🃏 (Reshuffled)")
            self.reshuffled = False
        else:
            embed = discord.Embed(title=f"Et Un test ------ {len(deck.table_deck)} 🃏")
        if len(deck.played_deck) == 0:
            embed.description = "The hand is empty"
        else:
            buffer = create_hand_image(deck)
            hand_image = discord.File(buffer, filename="hand.png")
            self.hand_image = hand_image
            embed.set_image(url="attachment://hand.png")
            score = deck.evaluate(self.cap)
            if score >= self.cap:
                if score > self.cap:
                    score = "BURST"
                else:
                    score = str(score)
                    score += " (CRIT)"
                self.disable_buttons()
                deck.clear_hand()
            embed.add_field(name=f"Score: {score} ------ Cap: {self.cap}", value="")
        return embed
    def disable_buttons(self):
        for item in self.children:
            item.disabled = True
    
    @discord.ui.button(label="Draw")
    async def draw(self, interaction, button):
        deck.draw()
        if len(deck.table_deck) == 0:
            self.reshuffled = True
            deck.reshuffle()
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    @discord.ui.button(label="Pass")
    async def pass_test(self, interaction, button):
        self.disable_buttons()
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
        deck.clear_hand()

@tree.command(
    name = "test",
    description = "Do an ability test"
)
@discord.app_commands.describe(cap = "The max score before a burst. In classic blackjack it's 21")
async def test(interaction, cap: int):
    if cap < 2:
        interaction.response.send_message(f"Invalid cap: {cap}, test aborted")
    else:
        global deck
        for _ in range(2):
            deck.draw()
        embed = discord.Embed(title=f"Et Un test ------ {len(deck.table_deck)} 🃏")
        buffer = create_hand_image(deck)
        hand_image = discord.File(buffer, filename="hand.png")
        embed.set_image(url="attachment://hand.png")
        score = deck.evaluate(cap)
        view = HandView(cap)
        if score > cap:
            score = "BURST"
            view.disable_buttons()
        embed.add_field(name=f"Score: {score} ------ Cap: {cap}", value="")
        await interaction.response.send_message(embed=embed, file=hand_image, view=view)
        if score == "BURST":
            deck.clear_hand()

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(API_KEY)
