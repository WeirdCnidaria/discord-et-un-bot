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
    error_string = str()
    if amount < 1:
        amount = 1
        error_string = "Invalid amount. Using 1 deck instead\n"
    decks.save_deck(interaction.channel_id, Deck(deck_amount=amount))
    if amount == 1:
        await interaction.response.send_message(error_string + f"Deck reset. Starting with 1 deck of cards")
    else:
        await interaction.response.send_message(error_string + f"Deck reset. Starting with {amount} decks of cards")

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
        self.reshuffled = False
        self.forced = False
        self.forced_split = False
        self.hand_split = False
        self.split_turn = True
        self.finished = False
        self.finished_split = False
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
            score_string = str(score)
            if not self.hand_split:
                if score >= self.cap or self.finished:
                    self.finished = True
                    if score > self.cap:
                        score_string = "BURST"
                    self.disable_buttons()
                    decks.clear_hand(self.channel_id)
                if self.forced and score <= self.cap and self.finished:
                    embed.add_field(name=f"Score: {score + 2} ({score} + 2) ------ Cap: {self.cap}", value="")
                else:
                    embed.add_field(name=f"Score: {score_string} ------ Cap: {self.cap}", value="")
            else:
                split_score = decks.load_deck(self.channel_id).evaluate_split(self.cap)
                split_score_string = str(split_score)
                if self.split_turn:
                    self.split_turn = False
                else:
                    self.split_turn = True
                if self.finished:
                    self.split_turn = True
                if self.finished_split:
                    self.split_turn = False
                if score >= self.cap:
                    self.finished = True
                    if score > self.cap:
                        score_string = "BURST"
                if split_score >= self.cap:
                    self.finished_split = True
                    if split_score > self.cap:
                        split_score_string = "BURST"
                main_deck_selection = str()
                split_deck_selection = str()
                if self.split_turn:
                    split_deck_selection = " (CURRENTLY PLAYING)"
                else:
                    main_deck_selection = " (CURRENTLY PLAYING)"
                if self.finished and self.finished_split:
                    self.disable_buttons()
                    decks.clear_hand(self.channel_id)
                    main_deck_selection = str()
                    split_deck_selection = str()
                if self.forced and score <= self.cap and self.finished:
                    embed.add_field(name=f"Score 1: {score + 2} ({score} + 2) - Cap: {self.cap}", value="\n")
                else:
                    embed.add_field(name=f"Score 1{main_deck_selection}: {score_string} - Cap: {self.cap}", value="\n")
                if self.forced_split and split_score <= self.cap and self.finished_split:
                    embed.add_field(name=f"Score 2: {split_score + 2} ({split_score} + 2) - Cap: {self.cap}", value="")
                else:
                    embed.add_field(name=f"Score 2{split_deck_selection}: {split_score_string} - Cap: {self.cap}", value="")
        return embed
    def disable_buttons(self):
        for item in self.children:
            item.disabled = True
    
    @discord.ui.button(label="Draw")
    async def draw(self, interaction, button):
        self.split.disabled = True
        if not self.hand_split:
            decks.draw(interaction.channel_id)
        else:
            if self.split_turn:
                decks.draw_split(interaction.channel_id)
            else:
                decks.draw(interaction.channel_id)
        if len(decks.load_deck(interaction.channel_id).table_deck) == 0:
            self.reshuffled = True
            decks.reshuffle(channel_id)
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    @discord.ui.button(label="Pass")
    async def pass_test(self, interaction, button):
        if not self.hand_split:
            self.finished = True
        else:
            if self.split_turn:
                self.finished_split = True
            else:
                self.finished = True
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    @discord.ui.button(label="Force")
    async def force(self, interaction, button):
        self.split.disabled = True
        if not self.hand_split:
            button.disabled = True
            self.forced = True
            for _ in range(2):
                decks.draw(interaction.channel_id)
        else:
            if self.split_turn:
                if self.forced:
                    button.disabled = True
                else:
                    button.disabled = False
                self.forced_split = True
                for _ in range(2):
                    decks.draw_split(interaction.channel_id)
            else:
                if self.forced_split:
                    button.disabled = True
                else:
                    button.disabled = False
                self.forced = True
                for _ in range(2):
                    decks.draw(interaction.channel_id)
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    @discord.ui.button(label="Split")
    async def split(self, interaction, button):
        button.disabled = True
        self.hand_split = True
        decks.split(interaction.channel_id)
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
            if len(decks.load_deck(interaction.channel_id).table_deck) == 0:
                decks.reshuffle(interaction.channel_id)
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
        if not decks.load_deck(interaction.channel_id).played_deck[0].rank == decks.load_deck(interaction.channel_id).played_deck[1].rank:
            view.split.disabled = True
        await interaction.response.send_message(embed=embed, file=hand_image, view=view)
        if score == "BURST" or score == "CRIT" or score == cap:
            decks.clear_hand(interaction.channel_id)

@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(activity=discord.Game(name="The game was rigged from the start"))
    print(f"Logged in as {client.user}")

client.run(API_KEY)
