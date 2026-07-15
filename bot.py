from os import environ
from dotenv import load_dotenv
import discord
from deck import Deck, Decks
from image_processing import create_hand_image

# Getting the bot API key from the .env file
load_dotenv()
API_KEY = environ["DISCORD_API_KEY"]

# Setting up the decks
decks = Decks()

# Setting up Discord library objects
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Returns a string with the embed title
def embed_title(cap: int, cards_left: int, reshuffled: bool = False) -> str:
    reshuffled_string = str()
    if reshuffled:
        reshuffled_string = " (Reshuffled)"
    return f"{cards_left} 🃏{reshuffled_string} | Et-un ability test | Cap: {cap}"

@tree.command(
    name = "new_deck",
    description = "Makes a new deck"
)
@discord.app_commands.describe(amount = "How many standard 52 card decks should be used")
async def new_deck(interaction, amount: int):
    global decks
    error_string = str()
    
    # Check if the amount is a valid number
    if amount < 1:
        amount = 1
        error_string = "Invalid amount. Using 1 deck instead\n"
    
    # Save the new deck
    decks.save_deck(interaction.channel_id, Deck(deck_amount=amount))
    
    # Respond with an informational message
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

# Buttons for the ability test embed
class HandView(discord.ui.View):
    def __init__(self, cap: int, channel_id: int) -> None:
        super().__init__(timeout=None)
        
        # Variable containing the buffer with the image of the played cards
        self.hand_image = None
        
        # If the deck has been reshuffled within the last draw
        self.reshuffled = False
        
        # If the played deck has been forced
        self.forced = False
        
        # If the split deck has been forced
        self.forced_split = False

        # If the deck has been split
        self.hand_split = False

        # If the player is currently choosing the action for the split deck
        self.split_turn = False

        # If any end condition has been met for the played deck (burst/hit exact)
        self.finished = False

        # If any end condition has been met for the split deck (burst/hit exact)
        self.finished_split = False
        
        # Point cap
        self.cap = cap

        # Channel ID
        self.channel_id = channel_id
    
    # Creates an embed and returns it
    def make_embed(self) -> discord.Embed:
        # Initiate the embed and add the title
        embed = discord.Embed(title=embed_title(self.cap, len(decks.load_deck(self.channel_id).table_deck), reshuffled=self.reshuffled))
        if self.reshuffled:
            self.reshuffled = False
        
        # Fallback for when an empty hand is given
        if len(decks.load_deck(self.channel_id).played_deck) == 0:
            embed.description = "The hand is empty"
        else:
            # Set up the image
            buffer = create_hand_image(decks.load_deck(self.channel_id))
            hand_image = discord.File(buffer, filename="hand.png")
            self.hand_image = hand_image
            embed.set_image(url="attachment://hand.png")
            
            # int version of the score
            score = decks.load_deck(self.channel_id).evaluate(self.cap)
            # str version of the score - replaceable by special score messages
            score_string = str(score)

            # The deck is not split
            if not self.hand_split:
                # Ending the test if an end condition has been met
                if score >= self.cap or self.finished:
                    self.finished = True
                    if score > self.cap:
                        score_string = "BURST"
                    self.disable_buttons()
                    decks.clear_hand(self.channel_id)
                
                # Add a custom score field for a finished forced test
                if self.forced and self.finished:
                    embed.add_field(name=f"Score: {score + 2} ({score} + 2)", value="")
                # Add a standard score field in other cases
                else:
                    embed.add_field(name=f"Score: {score_string}", value="")
            # The deck is split
            else:
                # score variable for the split deck
                split_score = decks.load_deck(self.channel_id).evaluate_split(self.cap)
                # score_string variable for the split deck
                split_score_string = str(split_score)
                
                # Set the decks as finished if their end condition has been met
                if score >= self.cap:
                    self.finished = True
                    if score > self.cap:
                        score_string = "BURST"
                if split_score >= self.cap:
                    self.finished_split = True
                    if split_score > self.cap:
                        split_score_string = "BURST"
                
                # Switch which deck is being controlled if the current one is finished
                if self.finished:
                    self.split_turn = True
                if self.finished_split:
                    self.split_turn = False
                
                # Set up string informing which deck is being controlled
                main_deck_selection = str()
                split_deck_selection = str()
                if self.split_turn:
                    split_deck_selection = " (CURRENTLY PLAYING)"
                else:
                    main_deck_selection = " (CURRENTLY PLAYING)"
                
                # End the test if both decks are finished
                if self.finished and self.finished_split:
                    self.disable_buttons()
                    decks.clear_hand(self.channel_id)
                    main_deck_selection = str()
                    split_deck_selection = str()
                
                # Add the first score field
                if self.forced and score <= self.cap and self.finished:
                    embed.add_field(name=f"Score 1: {score + 2} ({score} + 2)", value="\n")
                else:
                    embed.add_field(name=f"Score 1{main_deck_selection}: {score_string}", value="\n")
                
                # Add the second score field
                if self.forced_split and split_score <= self.cap and self.finished_split:
                    embed.add_field(name=f"Score 2: {split_score + 2} ({split_score} + 2)", value="")
                else:
                    embed.add_field(name=f"Score 2{split_deck_selection}: {split_score_string}", value="")
                
                # Switch the control to the other deck
                self.split_turn = not self.split_turn
        
        return embed
    
    # Disables all buttons
    def disable_buttons(self) -> None:
        for item in self.children:
            item.disabled = True
    
    @discord.ui.button(label="Draw")
    async def draw(self, interaction, button):
        # Disable the split button, in case it was enabled by a drawn double
        self.split.disabled = True
        
        # Draw the card
        if not self.hand_split:
            decks.draw(interaction.channel_id)
        else:
            if self.split_turn:
                decks.draw_split(interaction.channel_id)
            else:
                decks.draw(interaction.channel_id)
        
        # Reshuffle if the cards had ran out
        if len(decks.load_deck(interaction.channel_id).table_deck) == 0:
            self.reshuffled = True
            decks.reshuffle(self.channel_id)
        
        # Update the embed
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    
    @discord.ui.button(label="Pass")
    async def pass_test(self, interaction, button):
        # Set the proper deck as finished
        if not self.hand_split:
            self.finished = True
        else:
            if self.split_turn:
                self.finished_split = True
            else:
                self.finished = True
        
        # Update the embed
        await interaction.response.edit_message(embed=self.make_embed(), attachments=[self.hand_image], view=self)
    
    @discord.ui.button(label="Force")
    async def force(self, interaction, button):
        # Disable the split button, in case it was enabled by a drawn double
        self.split.disabled = True
        
        # The deck is not split
        if not self.hand_split:
            button.disabled = True
            self.forced = True
            
            for _ in range(2):
                decks.draw(interaction.channel_id)
        # The deck is split
        else:
            # The split deck deck is being controlled
            if self.split_turn:
                if self.forced:
                    button.disabled = True
                else:
                    button.disabled = False
                
                self.forced_split = True
                
                for _ in range(2):
                    decks.draw_split(interaction.channel_id)
            # The main deck is being controlled
            else:
                if self.forced_split:
                    button.disabled = True
                else:
                    button.disabled = False
                
                self.forced = True
                
                for _ in range(2):
                    decks.draw(interaction.channel_id)
        
        # Update the embed
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
        
        # Preventively clear the hand before proceeding
        decks.clear_hand(interaction.channel_id)
        
        # Draw the initial 2 cards
        for _ in range(2):
            if len(decks.load_deck(interaction.channel_id).table_deck) == 0:
                decks.reshuffle(interaction.channel_id)
            decks.draw(interaction.channel_id)
        
        # Create the embed
        embed = discord.Embed(title=embed_title(cap, len(decks.load_deck(interaction.channel_id).table_deck)))
        
        # Create the buttons
        view = HandView(cap, interaction.channel_id)
        
        # Set up the image
        buffer = create_hand_image(decks.load_deck(interaction.channel_id))
        hand_image = discord.File(buffer, filename="hand.png")
        embed.set_image(url="attachment://hand.png")
        
        # Check if the initial 2 cards ended the test
        score = decks.load_deck(interaction.channel_id).evaluate(cap)
        if score >= cap or decks.load_deck(interaction.channel_id).is_crit():
            if score > cap:
                score = "BURST"
            if decks.load_deck(interaction.channel_id).is_crit():
                score = "CRIT"
            view.finished = True
            view.disable_buttons()
        
        # Add score field
        embed.add_field(name=f"Score: {score}", value="")
        
        # Disable split button if there is no double
        if not decks.load_deck(interaction.channel_id).played_deck[0].rank == decks.load_deck(interaction.channel_id).played_deck[1].rank:
            view.split.disabled = True
        
        # Send the embed into the channel
        await interaction.response.send_message(embed=embed, file=hand_image, view=view)
        
        # Clear hand if the test had ended
        if score == "BURST" or score == "CRIT" or score == cap:
            decks.clear_hand(interaction.channel_id)

@client.event
async def on_ready():
    await tree.sync()
    await client.change_presence(activity=discord.Game(name="The game was rigged from the start"))
    print(f"Logged in as {client.user}")

client.run(API_KEY)
