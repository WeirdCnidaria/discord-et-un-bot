from random import shuffle
import pickle

# Class handling the specific card information
class Card():
    def __init__(self, suit: str, rank: str) -> None:
        if not suit in ["diamonds", "clubs", "hearts", "spades"]:
            raise ValueError(f"{suit} is not a supported card suit")
        if not rank in ["ace", "2", "3", "4", "5", "6", "7" , "8", "9", "10", "jack", "queen", "king"]:
            raise ValueError(f"{rank} is not a supported card rank")
        self.suit = suit
        self.rank = rank
    
    # Returns the value of the card
    def value(self) -> int:
        if self.rank == "ace":
            raise Exception("The ace card has a shifting value and should be evaluated by upstream code")
        elif self.rank in ["jack", "queen", "king"]:
            return 10
        else:
            return int(self.rank)

# Class handling the deck for specific channels
class Deck():
    def __init__(self, deck_amount: int = 1, shuffle_deck: bool = True) -> None:
        # The cards still in the deck, waiting to be used
        self.table_deck = list()
        
        # The cards currently used and exposed to the players
        self.played_deck = list()
        
        # The used up cards, waiting to be shuffled back into the deck
        self.discarded_deck = list()
        
        # Extra deck used during splitting
        self.split_deck = list()

        # Creates the deck
        for _ in range(deck_amount):
            for suit in ["diamonds", "clubs", "hearts", "spades"]:
                self.table_deck.append(Card(suit, "ace"))
                for i in range(2, 11):
                    self.table_deck.append(Card(suit, str(i)))
                self.table_deck.append(Card(suit, "jack"))
                self.table_deck.append(Card(suit, "queen"))
                self.table_deck.append(Card(suit, "king"))

        # Shuffles newly created deck
        if shuffle_deck:
            self.shuffle()
    
    # Draws a card from the table deck, and puts it in the played deck
    def draw(self) -> None:
        new_card = self.table_deck[0]
        self.table_deck.pop(0)
        self.played_deck.append(new_card)
    
    # Draws a card from the table deck, and puts it in the extra splitting deck
    def draw_split(self) -> None:
        new_card = self.table_deck[0]
        self.table_deck.pop(0)
        self.split_deck.append(new_card)

    # Clears all played cards, and puts the in the discarded deck
    def clear_hand(self) -> None:
        self.discarded_deck += self.played_deck
        self.discarded_deck += self.split_deck
        self.played_deck = list()
        self.split_deck = list()
    
    # Shuffles the table deck
    def shuffle(self) -> None:
        shuffle(self.table_deck)
    
    # Reshuffles discarded cards back into the table deck
    def reshuffle(self) -> None:
        self.table_deck += self.discarded_deck
        self.discarded_deck = list()
        self.shuffle()

    # Splits the played deck; puts one of the cards into the split deck
    def split(self) -> None:
        if len(self.played_deck) != 2:
            raise Exception("You can only split with 2 cards on hand")
        if self.played_deck[0].rank != self.played_deck[1].rank:
            raise Exception("You can only split with a double")
        
        split_card = self.played_deck[1]
        self.played_deck.pop(1)
        self.split_deck.append(split_card)

        return string
    
    # Returns a boolean informing if a critical success has been drawn in the played deck
    def is_crit(self) -> bool:
        return (self.played_deck[0].rank == "ace" and self.played_deck[1].rank in ["10", "jack", "queen", "king"]) or \
               (self.played_deck[1].rank == "ace" and self.played_deck[0].rank in ["10", "jack", "queen", "king"])
    
    # Returns a boolean informing if a critical success has been drawn in the split deck
    def is_crit_split(self) -> bool:
        return (self.split_deck[0].rank == "ace" and self.split_deck[1].rank in ["10", "jack", "queen", "king"]) or \
               (self.split_deck[1].rank == "ace" and self.split_deck[0].rank in ["10", "jack", "queen", "king"])
    
    # Returns the best value of the played deck, given the point cap
    def evaluate(self, cap: int) -> int:
        # Amount of aces in the played deck
        ace_amount = 0
        # The value, not accounting for aces
        non_ace_sum = 0
        
        # Sets proper values to ace_amount and non_ace_sum
        for card in self.played_deck:
            if card.rank == "ace":
                ace_amount += 1
            else:
                non_ace_sum += card.value()
        
        if ace_amount == 0:
            return non_ace_sum
        else:
            # Calculates the best sum option, given the point cap
            sum_options = list()
            for i in range(ace_amount+1):
                sum_options.append(non_ace_sum + 11*i + 1*(ace_amount-i))
            current_option = sum_options[0]
            sum_options.pop(0)
            for sum_option in sum_options:
                if sum_option > cap:
                    break
                current_option = sum_option
            return current_option
    
    # Returns the best value of the split deck, given the point cap
    def evaluate_split(self, cap: int) -> int:
        # Amount of aces in the played deck
        ace_amount = 0
        # The value, not accounting for aces
        non_ace_sum = 0
        
        # Sets proper values to ace_amount and non_ace_sum
        for card in self.split_deck:
            if card.rank == "ace":
                ace_amount += 1
            else:
                non_ace_sum += card.value()
        
        if ace_amount == 0:
            return non_ace_sum
        else:
            # Calculates the best sum option, given the point cap
            sum_options = list()
            for i in range(ace_amount+1):
                sum_options.append(non_ace_sum + 11*i + 1*(ace_amount-i))
            current_option = sum_options[0]
            sum_options.pop(0)
            for sum_option in sum_options:
                if sum_option > cap:
                    break
                current_option = sum_option
            return current_option
    
    # Debug function. Prints the contents of the deck to the command line
    def print(self) -> None:
        print("Table deck:\n")
        for card in self.table_deck:
            print(f"{card.rank.capitalize()} of {card.suit}")
        print("\nPlayed deck:\n")
        for card in self.played_deck:
            print(f"{card.rank.capitalize()} of {card.suit}")
        print("\nDiscarded deck:\n")
        for card in self.discarded_deck:
            print(f"{card.rank.capitalize()} of {card.suit}")
    
    # Depreciated function. Returns a formatted string with the contents of the played deck
    def hand_string(self) -> str:
        if len(played_deck) == 0:
            return "The hand is empty"
        string = str()
        for card in played_deck:
            string += card.rank.capitalize() + " of " + card.suit + "\n"
        string = string[:-1]

# Class handling all the Deck objects
class Decks():
    def __init__(self, 
                 load_saved: bool = True, 
                 saved_dir: str = "save/saved_decks.pickle", 
                 print_debug_info: bool = True) -> None:
        self.decks = dict()
        self.dir = saved_dir
        self.print_debug = print_debug_info
        if load_saved:
            self.load()
    
    # Returns the deck from a given channel
    def load_deck(self, channel_id: int) -> Deck:
        if channel_id not in self.decks:
            self.decks[channel_id] = Deck()
        return self.decks[channel_id]
    
    # Saves the given deck into memory
    def save_deck(self, channel_id: int, deck: Deck) -> None:
        self.decks[channel_id] = deck
    
    # Clears the played deck from a Deck object
    def clear_hand(self, channel_id: int) -> None:
        self.load_deck(channel_id)
        self.decks[channel_id].clear_hand()
        self.save()
    
    # Draws a card into the played deck in a given Deck object
    def draw(self, channel_id: int) -> None:
        self.load_deck(channel_id)
        self.decks[channel_id].draw()
    
    # Draws a card into the split deck in a given Deck object
    def draw_split(self, channel_id: int) -> None:
        self.load_deck(channel_id)
        self.decks[channel_id].draw_split()
    
    # Splits the played deck in a given Deck object
    def split(self, channel_id) -> None:
        self.load_deck(channel_id)
        self.decks[channel_id].split()
    
    # Reshuffles discarded cards back into the table deck in a given Deck object
    def reshuffle(self, channel_id) -> None:
        self.load_deck(channel_id)
        self.decks[channel_id].reshuffle()
    
    # Loads the saved decks from a local file
    def load(self) -> None:
        try:
            with open(self.dir, "rb") as f:
                self.decks = pickle.load(f)
        except FileNotFoundError:
            self.decks = dict()
            if self.print_debug:
                print("[deck.py] No saved decks detected, creating empty deck list")
    
    # Saves the decks in memory into a local file
    def save(self) -> None:
        with open(self.dir, "wb") as f:
            pickle.dump(self.decks, f)
