import os
import json

from datetime import datetime
import discord
import requests
import pytesseract
from PIL import Image
from io import BytesIO
from plate_recognizer import PlateAPIResponse, MessageCreate
from models.message import Message, MessageLoaded
import database as db
from dotenv import load_dotenv


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
PR_API_TOKEN = os.getenv("PR_API_TOKEN")
print(DISCORD_TOKEN)
print(CHANNEL_ID)
print(PR_API_TOKEN)
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def extract_plate_text_from_image(url):
    img_res = requests.get(url)
    fp = BytesIO(img_res.content)

    regions = ["mx", "us"]  # Change to your country
    res_json = requests.post(
        "https://api.platerecognizer.com/v1/plate-reader/",
        data=dict(regions=regions),
        files=dict(upload=fp),
        headers={"Authorization": f"Token {PR_API_TOKEN}"},
    ).json()

    response = PlateAPIResponse(**res_json)
    if not response.results:
        return
    for result in response.results:
        if not result.plate:
            continue

        return result.plate

    return None


def set_message_loaded():
    with db.SessionLocal() as session:
        # Try to fetch the first row
        flag = session.query(MessageLoaded).first()

        if flag:
            # Row exists → update it
            flag.is_loaded = True
            print("Updated is_loaded to True")
        else:
            # No row exists → create it
            flag = MessageLoaded(is_loaded=True)
            session.add(flag)
            print("Created new MessageLoaded row with is_loaded=True")

        # Commit changes
        session.commit()


def store_messages(messages: MessageCreate):
    session = db.SessionLocal()
    try:
        for msg in messages:
            if not msg.plate_number:
                continue
            session.add(Message(plate_number=msg.plate_number, author=msg.author, sent_at=msg.sent_at))
        if session.new:
            session.commit()
            print("Plates stored successfully!")
    except Exception as e:
        session.rollback()
        print(f"transaction filed, rolled back. error: {e}")
    finally:
        session.close()


@client.event
async def on_ready():
    for guild in client.guilds:

        print(f"{client.user} has connected to Discord!\n" f"{guild.name} (id: {guild.id})")
        channel = client.get_channel(CHANNEL_ID)

        with db.SessionLocal() as session:
            is_loaded = session.query(MessageLoaded).first()
        if is_loaded:
            print("Historical message has already been loaded.")
            break

        messages = []
        async for msg in channel.history(limit=None):
            if not msg.attachments:
                continue

            for file in msg.attachments:
                plate_number = extract_plate_text_from_image(file.url)
                if not plate_number:
                    continue

                print(f"plate number --> {plate_number}")
                messages.append(
                    MessageCreate(author=msg.author.name, sent_at=msg.created_at, plate_number=plate_number)
                )
        store_messages(messages)
        set_message_loaded()
        break


def get_first_seen(plate_number: str) -> Message | None:
    with db.SessionLocal() as session:
        return (
            session.query(Message).filter(Message.plate_number == plate_number).order_by(Message.sent_at.asc()).first()
        )


@client.event
async def on_message(message):
    if message.channel.id != CHANNEL_ID:
        return
    if message.author == client.user:
        return
    seen_plates = {}
    new_plates = []
    if message.attachments:
        for file in message.attachments:
            curr_plate_number = extract_plate_text_from_image(file.url)
            first_msg = get_first_seen(curr_plate_number)
            if first_msg:
                seen_plates[curr_plate_number] = first_msg
            else:
                new_plates.append(
                    MessageCreate(
                        author=message.author.name, plate_number=curr_plate_number, sent_at=message.created_at
                    )
                )
    if new_plates:
        store_messages(new_plates)
    # If any plates were previously seen, prepare a reply
    if seen_plates:
        lines = [
            f"Plate **{msg.plate_number}** was first seen by **{msg.author}** on **{msg.sent_at}**"
            for msg in seen_plates.values()
        ]
        reply = "\n".join(lines)
        await message.channel.send(reply)


client.run(DISCORD_TOKEN)
