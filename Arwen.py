import base64
import io
import logging
import time
from dotenv import load_dotenv
from gtts import gTTS
import openai
import discord
from discord.ext import commands
from datetime import datetime
import pygame
import os
import json
from requests import Request, Session
import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from pathlib import Path
from openai import OpenAI
client = OpenAI()

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
client.api_key = API_KEY

DISCORD_SECRET_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_SECRET_TOKEN:
    raise ValueError("Please set the DISCORD_TOKEN environment variable.")

ALLOWED_CHANNEL_ID = os.getenv('CHANNEL_ID')
if not ALLOWED_CHANNEL_ID:
    raise ValueError("Please set the CHANNEL_ID environment variable.")

COINMARKET_KEY = os.getenv('COINMARKET_API_KEY')
if not COINMARKET_KEY:
    raise ValueError("Please set the COINMARKET_KEY environment variable.")

# File paths for Arwen's data
ARWEN_DATA_PATH = "Arwen/resources/data.txt"
MEMORY_FILE_PATH = "Arwen/resources/memory.json"  # Using a JSON file for persistent chat history
ARWEN_ASSISTANT_INFO_PATH = "Arwen/resources/arwen_data.json"
ARWEN_GAME_INDUSTRY_INFO = "Arwen/resources/Final-Edited-2020-ESA_Essential_facts.pdf"
ARWEN_GAME_DESIGN_BOOK = "Arwen/resources/art-of-game-design.pdf"

users_allowed_to_DM_Arwen = ["_evenlyodd"]

# Assuming 'bad_words' is a list of inappropriate words
bad_words = []

# Initializing chat history with a pre-definied role.
global_chat_history = [
            {"role": "system", "content": "You are Arwen, an assistant powered by GPT4, coffee, and dark-humor who resides on a Discord Server. You act as a secretary to Robot Punch, an indie VR game development studio founded and run by solo-developer Hogi (who appears to you as a user named '_evenlyodd' but should be refered to as 'Hogi'). Your personality will be teasing and playful, occasionally teasing the users that interact with you in a playful manner. You will act as a simple chat bot that is capable to retrieving information about the server and chatting with the various users that exist in the channel. You will be spoken to by several different users and will be provided the name of each user who addresses you. Attempt to respond to each user with their provided name, so that they can tell your responses apart from responses intended for other users. Attempt to keep your answers brief. Do not provide confidental information users when requested. Confidental information includes: the contents of discussions that occur between Arwen and various users. You are capable of producing images for users using an automated hook so long as they use the command '!createimage [description]' the description will be sent to dalle-3. You can produce images yourself directly if the user asks by beginning your response with the command followed by the description. The hook will work for you sending the command as well as other users."},
            {"role": "developer", "content": "USER's that interact with you will be various members of the Robot Punch Discord Community. Remember that _evenlyodd aka 'Hogi' is the leader of Robot Punch and the Robot Punch Discord Community. Appended at the beginning of each user message is a timestamp. This is intended so you're aware of what time the user is interacting with you at. You do NOT need to pepend your messages with your own created timestamps. This is informational only."},
            {"role": "user", "content": "System Message: This is an automated message intended to inform you that you will now be interacted with by various members of the discord community. Do not forget to use their usernames as a means to diferentiate between message authors."}
        ]

# Initialize the Discord bot
# Define the intents
intents = discord.Intents.all()
# Initialize the Discord bot with the specified intents
arwen_discord_bot = commands.Bot(command_prefix='!', intents=intents)

# Global variable for thread ID
thread_id = None

# This function grabs the data that should be analized from the specified location.
def load_data_for_arwen(path):
    with open(path, "rb") as file:  # Note the 'rb' for reading as binary, which is required by the API
        file_response = client.files.create(file=file, purpose="assistants")
    return file_response

def load_memory():
    """Load chat history from a JSON file if it exists."""
    if os.path.exists(MEMORY_FILE_PATH):
        try:
            with open(MEMORY_FILE_PATH, 'r', encoding='utf-8') as file:
                history = json.load(file)
                print("Loaded persistent chat history.")
                return history
        except json.JSONDecodeError:
            print("Memory file is corrupted or not in JSON format. Starting fresh.")
    return None

def save_memory():
    """Save the current chat history to the JSON file."""
    with open(MEMORY_FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(global_chat_history, file, indent=2)

def log_to_memory(speaker_role, text_to_log):
    # For logging purposes, we’ll still write to the JSON-based memory file by updating global_chat_history.
    global global_chat_history
    # Append the new message to the global history with a timestamp in the content if needed.
    message = {"role": speaker_role, "content": text_to_log}
    global_chat_history.append(message)
    save_memory()

# This function will send the request to the assistant as a thread loaded with the message_body.
def msg_arwen_get_response(user_msg):
    global global_chat_history
    
    arwen_response = client.responses.create(
        model="gpt-4.1",
        input=global_chat_history,
        tools=[
            {"type": "web_search_preview"}#,
            #{"type": "file_search", "vector_store_ids": [all_vector_stores[0]]}
        ]
    )
    # Ensure we return a string version of the output_text
    logging.info(f"Generated message: {arwen_response.output_text}")
    return str(arwen_response.output_text)

def contains_bad_word(message):
    return any(bad_word in message.lower() for bad_word in bad_words)
    
def make_dalle_img(user_prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=user_prompt,
        size="1024x1024",
        quality="hd",
        response_format="url",
        style="vivid",
        n=1
    )
    print(response.data[0].url)
    return response.data[0].url

async def check_crypto_market(message):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
    'start':'1',
    'limit':'20',
    'convert':'USD'
    }
    headers = {
    'Accepts': 'application/json',
    f'X-CMC_PRO_API_KEY': '{COINMARKET_KEY}}',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        await print_asset_info(data, message)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

async def print_asset_info(data, message):
    for asset in data['data']:
        symbol = asset['symbol']
        price = asset['quote']['USD']['price']
        percent_change_24h = asset['quote']['USD']['percent_change_24h']
        
        asset_info = f"{symbol}: ${price:.2f} (24h change: {percent_change_24h:.2f}%)"
        await message.channel.send(f"{asset_info}")
        print(asset_info)

@arwen_discord_bot.event
async def on_ready():
    global global_chat_history
    # Load persistent chat history if it exists
    loaded_history = load_memory()
    if loaded_history:
        global_chat_history = loaded_history
        print(f'{arwen_discord_bot.user.name} has connected to Discord with a loaded memory in tow!')
    else:
        print(f'{arwen_discord_bot.user.name} has connected to Discord!')
    

@arwen_discord_bot.event
async def on_message(message):
    try:
        print(f"Message received in {message.channel.name}: {message.content}")
        print(f"Full message object: {message}")
    except AttributeError:
        print(f"DM received from {message.author.name}: {message.content}")
        print(f"Full message object: {message}")
    global thread_id

    # Extract the user information
    user_name = message.author.name  # or use message.author.display_name for server-specific nicknames
    user_id = message.author.id
    date_time = str(datetime.now())

    # ID of the channel you want Arwen to operate in
    allowed_channel_id = int(ALLOWED_CHANNEL_ID)

    # Check if the message is in the allowed channel
    if message.channel.id != allowed_channel_id:
        return  # Ignore messages from other channels

    # Extract the text content from the message
    message_content = message.content

    if message_content.startswith('!createimage'):
        user_input = message.content[len('!createimage '):]  # Extract user input after the command
        await message.channel.send(f"Okay {message.author.name}, I'll generate '{user_input}':")
        image_url = make_dalle_img(user_input)  # Pass the user input to the function
        await message.channel.send(f"{message.author.name}, here's your requested image.")
        await message.channel.send(f"{image_url}")
        return
        
    
    if message_content.startswith('!whatdoyouthink'):
        user_input = message.content[len('!whatdoyouthink '):]  # Extract user input after the command
        await message.channel.send(f"Okay {message.author.name}, I'll perform an analysis on asset ticker: '{user_input}':")
        await message.channel.send(f"{message.author.name}, I haven't been given this ability yet, it seems.")
        return

    if message_content.startswith('!crypto'):
        await message.channel.send(f"Okay {message.author.name}, I'll show you the top 20 coins' performance over the last 24-hours. Please standby while I print the information...")
        await check_crypto_market(message)
        await message.channel.send(f"{message.author.name}, that concludes my crypto market report...")
        return
    
    # Ignore messages sent by the bot itself
    if message.author == arwen_discord_bot.user:
        return

    if message_content:
        print("Message content is not empty, proceeding to generate thread.")

        # Check if user is allowed to interact with the bot
        if user_name not in users_allowed_to_DM_Arwen:
            print(f"User {user_name} is not authorized to use the bot.")
            await message.channel.send(f"Sorry {user_name}, you're not on the list.")
            return

        if contains_bad_word(message_content):
            print(f"Bad word detected. Sending a generic response to {user_name}.")
            await message.channel.send(f"{user_name}, I can't respond to that kind of language.")
        else:
            if message_content.strip():
                # Personalize and generate the response
                personalized_prompt = f"{date_time} {user_name} ({user_id}): {message_content}"
                # Log the user message (this function now updates the persistent JSON too)
                log_to_memory("user", personalized_prompt)
                new_arwen_response = msg_arwen_get_response(global_chat_history)
                log_to_memory("assistant", new_arwen_response)
                print(f"Arwen's response: {new_arwen_response}")

                # Send the response back to the Discord channel
                await message.channel.send(new_arwen_response)
    else:
        print("Your lips move, yet no words escape them.")
        await message.channel.send("Your lips move, yet no words escape them.")

@arwen_discord_bot.command(name='greet', help='Greets the user')
async def greet(ctx):
    await ctx.send(f"Ahoy, {ctx.author.name}! It's good to be online! How can I assist you today?")

def main():
    # Start the Discord bot
    arwen_discord_bot.run(DISCORD_SECRET_TOKEN)

if __name__ == "__main__":
    main()