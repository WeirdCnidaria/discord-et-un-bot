from random import shuffle
import pickle

class Card():
    def __init__(self, suit: str, rank: str):
        if not suit in ["diamonds", "clubs", "hearts", "spades"]:
            raise ValueError(f"{suit} is not a supported card suit")
        if not rank in ["ace", "2", "3", "4", "5", "6", "7" , "8", "9", "10", "jack", "queen", "king"]:
            raise ValueError(f"{rank} is not a supported card rank")
        self.suit = suit
        self.rank = rank
    def value(self):
        if self.rank == "ace":
            raise Exception("The ace card has a shifting value and should be evaluated by upstream code")
        elif self.rank in ["jack", "queen", "king"]:
            return 10
        else:
            return int(self.rank)

class Deck():
    def __init__(self, deck_amount: int = 1, shuffle_deck: bool = True):
        # The cards still in the deck, waiting to be used
        self.table_deck = list()
        # The cards currently used and exposed to the players
        self.played_deck = list()
        # The used up cards, waiting to be shuffled back into the deck
        self.discarded_deck = list()
        # Extra deck used during splitting
        self.split_deck = list()

        for _ in range(deck_amount):
            for suit in ["diamonds", "clubs", "hearts", "spades"]:
                self.table_deck.append(Card(suit, "ace"))
                for i in range(2, 11):
                    self.table_deck.append(Card(suit, str(i)))
                self.table_deck.append(Card(suit, "jack"))
                self.table_deck.append(Card(suit, "queen"))
                self.table_deck.append(Card(suit, "king"))

        if shuffle_deck:
            self.shuffle()
    def draw(self):
        new_card = self.table_deck[0]
        self.table_deck.pop(0)
        self.played_deck.append(new_card)
    def clear_hand(self):
        self.discarded_deck += self.played_deck
        self.played_deck = list()
    def shuffle(self):
        shuffle(self.table_deck)
    def reshuffle(self):
        self.table_deck += self.discarded_deck
        self.discarded_deck = list()
        self.shuffle()
    def print(self):
        print("Table deck:\n")
        for card in self.table_deck:
            print(f"{card.rank.capitalize()} of {card.suit}")
        print("\nPlayed deck:\n")
        for card in self.played_deck:
            print(f"{card.rank.capitalize()} of {card.suit}")
        print("\nDiscarded deck:\n")
        for card in self.discarded_deck:
            print(f"{card.rank.capitalize()} of {card.suit}")
    def is_crit(self):
        return (self.table_deck[0].rank == "ace" and self.table_deck[1].rank in ["10", "jack", "queen", "king"]) or \
               (self.table_deck[1].rank == "ace" and self.table_deck[0].rank in ["10", "jack", "queen", "king"])
    def hand_string(self):
        if len(played_deck) == 0:
            return "The hand is empty"
        string = str()
        for card in played_deck:
            string += card.rank.capitalize() + " of " + card.suit + "\n"
        string = string[:-1]
        return string
    def evaluate(self, cap: int):
        ace_amount = 0
        non_ace_sum = 0
        
        for card in self.played_deck:
            if card.rank == "ace":
                ace_amount += 1
            else:
                non_ace_sum += card.value()
        
        if ace_amount == 0:
            return non_ace_sum
        else:
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

class Decks():
    def __init__(self, load_saved=True, saved_dir="temp/saved_decks.pickle", print_debug_info=True):
        self.decks = dict()
        self.dir = saved_dir
        self.print_debug = print_debug_info
        if load_saved:
            self.load()
    def load_deck(self, channel_id):
        if channel_id not in self.decks:
            self.decks[channel_id] = Deck()
        return self.decks[channel_id]
    def save_deck(self, channel_id, deck):
        self.decks[channel_id] = deck
    def clear_hand(self, channel_id):
        self.load_deck(channel_id)
        self.decks[channel_id].clear_hand()
        self.save()
    def draw(self, channel_id):
        self.load_deck(channel_id)
        self.decks[channel_id].draw()
    def reshuffle(self, channel_id):
        self.load_deck(channel_id)
        self.decks[channel_id].reshuffle()
    def load(self):
        try:
            with open(self.dir, "rb") as f:
                self.decks = pickle.load(f)
        except FileNotFoundError:
            self.decks = dict()
            if self.print_debug:
                print("[deck.py] No saved decks detected, creating empty deck list")
    def save(self):
        with open(self.dir, "wb") as f:
            pickle.dump(self.decks, f)
