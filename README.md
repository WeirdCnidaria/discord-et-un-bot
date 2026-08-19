# Et-un bot for Discord

This project is a Discord bot meant for simulating card decks and ability tests for the "Et-un" RPG engine. It adds basic commands for creating decks and performing tests, and can handle multiple decks at the same time on separate channels. Credit for the engine goes to @kanpka_ on Discord.

## Starting the bot

Make sure you have Python installed, and install packages required to run the program from `requirements.txt`. Create a file named `.env` in the project folder, with the Discord app API key (see `.env.example` for the file structure). Run `bot.py` to start the bot.

## Available commands

- `/new_deck [amount]` - Creates and shuffles a new playing deck for the channel it's run in. `[amount]` specifies how many standard 52 card decks should be used for the newly created playing deck.
- `/deck_info` - Displays information about the deck of the channel it's run in. Specifically - how many cards are currently drawn, discarded, still in the deck, and total.
- `/ability_test [cap]` - Simulates an Et-un ability test, drawing cards from the channel`s deck. [cap] specifies the difficulty cap of the test, that the player is attempting to reach. The created embed has full support for drawing cards, forcing the test, passing, and for simple splitting.
