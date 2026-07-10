from PIL import Image
from io import BytesIO

def create_hand_image(deck):
    images = [Image.open(f"images/cards/{card.rank}_of_{card.suit}.png") for card in deck.played_deck]
    width = 500*len(images)
    height = 726

    combined_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for index, image in enumerate(images):
        combined_image.paste(image, (index*500, 0))
    
    buffer = BytesIO()
    combined_image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
