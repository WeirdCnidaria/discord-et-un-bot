from PIL import Image
from io import BytesIO
from deck import Deck

# Creates a deck image, from the Deck object
def create_hand_image(deck: Deck) -> BytesIO:
    # Checks if the deck has been split
    split = len(deck.split_deck) != 0
    
    # Sets up variables for the deck image
    images = [Image.open(f"images/cards/{card.rank}_of_{card.suit}.png") for card in deck.played_deck]
    if split:
        images_2 = [Image.open(f"images/cards/{card.rank}_of_{card.suit}.png") for card in deck.split_deck]
        width = 500*max(len(images), len(images_2))
        height = 726*2
    else:
        width = 500*len(images)
        height = 726
    
    # Creates the deck image
    combined_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for index, image in enumerate(images):
        combined_image.paste(image, (index*500, 0))
   
    # Adds the second row of cards for split decks
    if split:
        for index, image in enumerate(images_2):
            combined_image.paste(image, (index*500, 726))

    # Saves the deck image into a buffer
    buffer = BytesIO()
    combined_image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer
