from os import environ
from dotenv import load_dotenv
import discord
from deck import Deck, Decks
from image_processing import create_hand_image

# Getting the bot API key from the .env file
load_dotenv()
API_KEY = environ["DISCORD_API_KEY"]

decks = Decks()

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
    global decks
    if amount < 1:
        amount = 1
        await interaction.response.send_message("Invalid amount. Using 1 deck instead")
    decks.save_deck(interaction.channel_id, Deck(deck_amount=amount))
    if amount == 1:
        await interaction.response.send_message(f"Deck reset. Starting with 1 deck of cards")
    else:
        await interaction.response.send_message(f"Deck reset. Starting with {amount} decks of cards")

@tree.command(
    name = "deck_info",
    description = "Display information about the currently used deck"
)
async def deck_info(interaction):
    global decks
    deck = decks.load_deck(interaction.channel_id)
    total = len(deck.table_deck) + len(deck.played_deck) + len(deck.split_deck) + len(deck.discarded_deck) 
    await interaction.response.send_message(f"The current deck has {len(deck.table_deck)} unplayed cards, {len(deck.played_deck) + len(deck.split_deck)} cards on hand, and {len(deck.discarded_deck)} discarded cards, for a total of {total} cards ({total // 52} • 52 cards)\nUse `/new_deck` to generate a new deck")

class HandView(discord.ui.View):
    def __init__(self, cap, channel_id):
        super().__init__(timeout=None)
        self.hand_image = None
        self.score_string = str()
        self.reshuffled = False
        self.forced = False
        self.finished = False
        self.cap = cap
        self.channel_id = channel_id
    def make_embed(self):
        if self.reshuffled:
            embed = discord.Embed(title=f"Et-un ability test ------ {len(decks.load_deck(self.channel_id).table_deck)} 🃏 (Reshuffled)")
            self.reshuffled = False
        else:
            embed = discord.Embed(title=f"Et-un ability test ------ {len(decks.load_deck(self.channel_id).table_deck)} 🃏")
        if len(decks.load_deck(self.channel_id).played_deck) == 0:
            embed.description = "The hand is empty"
        else:
            buffer = create_hand_image(decks.load_deck(self.channel_id))
            hand_image = discord.File(buffer, filename="hand.png")
            self.hand_image = hand_image
            embed.set_image(url="attachment://hand.png")
            score = decks.load_deck(self.channel_id).evaluate(self.cap)
            self.score_string = str(score)
            if score >= self.cap:
                self.finished = True
                if score > self.cap:
                    self.score_string = "BURST"
                self.disable_buttons()
                decks.clear_hand(self.channel_id)
            if self.forced and score <= self.cap and self.finished:
                embed.add_field(name=f"Score: {score + 2} ({score} + 2) ------ Cap: {self.cap}", value="")
            else:
                embed.add_field(name=f"Score: {self.score_string} ------ Cap: {self.cap}", value="")
        return embed
    def disable_buttons(self):
        for item in self.children:
            item.disabled = True
    
    @discord.ui.button(label="Draw")
    async def draw(self, interaction, button):
        decks.draw(interaction.channel_id)
        if len(deck.table_deck) == 0:
            self.reshuffled = True
            decks.reshuffle(channel_id)
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    @discord.ui.button(label="Pass")
    async def pass_test(self, interaction, button):
        self.finished = True
        self.disable_buttons()
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
        decks.clear_hand(interaction.channel_id)
    @discord.ui.button(label="Force")
    async def force(self, interaction, button):
        button.disabled = True
        self.forced = True
        for _ in range(2):
            decks.draw(interaction.channel_id)
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)

@tree.command(
    name = "test",
    description = "Do an ability test"
)
@discord.app_commands.describe(cap = "The max score before a burst. In classic blackjack it's 21")
async def test(interaction, cap: int):
    if cap < 2:
        interaction.response.send_message(f"Invalid cap: {cap}, test aborted")
    else:
        global decks
        decks.clear_hand(interaction.channel_id)
        for _ in range(2):
            decks.draw(interaction.channel_id)
        embed = discord.Embed(title=f"Et-un ability test ------ {len(decks.load_deck(interaction.channel_id).table_deck)} 🃏")
        buffer = create_hand_image(decks.load_deck(interaction.channel_id))
        hand_image = discord.File(buffer, filename="hand.png")
        embed.set_image(url="attachment://hand.png")
        score = decks.load_deck(interaction.channel_id).evaluate(cap)
        view = HandView(cap, interaction.channel_id)
        if score >= cap or decks.load_deck(interaction.channel_id).is_crit():
            if score > cap:
                score = "BURST"
            if decks.load_deck(interaction.channel_id).is_crit():
                score = "CRIT"
            view.finished = True
            view.disable_buttons()
        embed.add_field(name=f"Score: {score} ------ Cap: {cap}", value="")
        await interaction.response.send_message(embed=embed, file=hand_image, view=view)
        if score == "BURST":
            decks.clear_hand(interaction.channel_id)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

client.run(API_KEY)
