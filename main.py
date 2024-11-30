import discord
import os
import time
import logging
import subprocess
from discord import File
from discord.ext import commands, tasks
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from itertools import cycle
import aiofiles
import shutil

# Load environment variables from the .env file
load_dotenv()
bot_token = os.getenv('bot_token')
if not bot_token:
    raise ValueError("Bot token not found in environment variables.")

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Define intents and enable message content intent
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # For slash commands

# Assign unique session ID for each obfuscation request
current_session_id = 0
MAX_FILE_SIZE = 5 * 1024 * 1024  # Maximum file size of 5 MB

# Directory to save original files
ORIGINAL_FILES_DIR = "original_files"
if not os.path.exists(ORIGINAL_FILES_DIR):
    os.makedirs(ORIGINAL_FILES_DIR)

# Maintain an active Flask web server
app = Flask('')

@app.route('/')
def home():
    return "<h1>🔥 FlameCoder Obfuscate is Active 🔥</h1>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Status rotation tasks
status_list = cycle(["🔥 Obfuscating with Style 🔥", "🛠️ Transforming Code 🛠️", "🚀 Improving Security 🚀", "👾 Debugging with Finesse 👾"])
@tasks.loop(seconds=10)  # Change interval to seconds
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status_list)))

# Event triggered when the bot is ready
@bot.event
async def on_ready():
    logging.info(f'✨ FlameCoder Obfuscate Bot {bot.user} has successfully started. ✨')
    change_status.start()

# Check if the attached file is valid
def is_valid_attachment(attachment):
    return attachment.filename.endswith(('.lua', '.txt')) and attachment.size <= MAX_FILE_SIZE

# Download the attached file asynchronously and save the original
async def download_attachment(attachment, filename):
    content = await attachment.read()
    async with aiofiles.open(filename, "wb") as f:
        await f.write(content)
    # Save a copy of the original file
    shutil.copy(filename, os.path.join(ORIGINAL_FILES_DIR, os.path.basename(filename)))

# Execute the Lua obfuscation script
def run_obfuscation(inputfilename, outputfilename, preset="Medium"):
    start_time = time.time()
    command = ["lua", "src/cli.lua", inputfilename, "--out", outputfilename, "--preset", preset]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        raise Exception(f"⚠️ Obfuscation failed with error: {e}")
    return time.time() - start_time

# Validate the output file
def validate_output(outputfilename):
    try:
        with open(outputfilename, "r") as f:
            content = f.read()
        if len(content.strip()) < 10:
            raise ValueError("The output file appears to be invalid or empty.")
    except Exception as e:
        raise Exception(f"⚠️ Validation failed: {e}")

# Add a footer to the obfuscated file (optional)
def add_obfuscation_footer(outputfilename):
    try:
        with open(outputfilename, "r+") as output_file:
            content = output_file.read()
            output_file.seek(0)
            output_file.write("-- Obfuscated by FlameCoder Team, Discord = 'discord.gg/yvM2szKNyx'\n" + content)
    except Exception as e:
        logging.warning(f"⚠️ Failed to add footer: {e}")

# Send an error message and delete it after a delay
async def send_error_message(channel, content):
    error_msg = await channel.send(content)
    await error_msg.delete(delay=10)

# Process the message and handle obfuscation asynchronously
async def process_message(msg, preset="Medium", add_footer=True):
    global current_session_id
    current_session_id += 1
    session_id = current_session_id

    inputfilename = f"sessionIN{session_id}.lua"
    outputfilename = f"sessionOUT{session_id}.lua"

    try:
        attachment = msg.attachments[0]
        logging.info(f'📥 {msg.author} uploaded {attachment.filename}')
        await download_attachment(attachment, inputfilename)
        loading_message = await msg.channel.send("⏳ Processing your request...")

        obfuscation_time = run_obfuscation(inputfilename, outputfilename, preset)
        validate_output(outputfilename)  # Validate the output file

        if add_footer:
            add_obfuscation_footer(outputfilename)

        obfuscated_file = File(outputfilename, filename="FlameCoder.lua")
        await msg.channel.send(file=obfuscated_file)

        embed = discord.Embed(
            title="FlameCoder Obfuscate",
            description="Obfuscation completed successfully! | Powered by FlameCoder",
            color=0x2ecc71,
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url="attachment://flamecoder.png")
        embed.add_field(name="Session ID", value=session_id, inline=False)
        embed.add_field(name="Obfuscation Time", value=f"{obfuscation_time:.2f} seconds", inline=False)
        embed.set_footer(text="Thank you for using FlameCoder Obfuscate", icon_url=bot.user.avatar.url)

        await loading_message.edit(content=f"{msg.author.mention}\n🚀 Transaction complete", embed=embed)
        logging.info(f'📤 {msg.author} obfuscated {attachment.filename} in {obfuscation_time:.2f} seconds')

    except Exception as e:
        logging.error(f"Error processing file: {e}")
        await send_error_message(msg.channel, "⚠️ An error occurred during the obfuscation process. Please try again later.")
    finally:
        for filename in [inputfilename, outputfilename]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception as e:
                    logging.warning(f"⚠️ Failed to delete file {filename}: {e}")

# Command to obfuscate the attached file
@bot.command(name='obfuscate')
async def obfuscate(ctx, preset="Medium"):
    if not ctx.message.attachments:
        await send_error_message(ctx.channel, "⚠️ No attachments found. Please attach a .lua or .txt file.")
        return

    if len(ctx.message.attachments) != 1:
        await send_error_message(ctx.channel, "⚠️ Expected exactly one attachment.")
        return

    attachment = ctx.message.attachments[0]
    if not is_valid_attachment(attachment):
        await send_error_message(ctx.channel, "⚠️ Invalid file type. Expected a .lua or .txt file.")
        return

    await process_message(ctx.message, preset)

# Command to obfuscate with different presets
@bot.command(name='obfuscate_with_preset')
async def obfuscate_with_preset(ctx, preset="Medium"):
    if not ctx.message.attachments:
        await send_error_message(ctx.channel, "⚠️ No attachments found. Please attach a .lua or .txt file.")
        return

    if len(ctx.message.attachments) != 1:
        await send_error_message(ctx.channel, "⚠️ Expected exactly one attachment.")
        return

    attachment = ctx.message.attachments[0]
    if not is_valid_attachment(attachment):
        await send_error_message(ctx.channel, "⚠️ Invalid file type. Expected a .lua or .txt file.")
        return

    await process_message(ctx.message, preset)

# Command to show bot version
@bot.command(name='version')
async def version(ctx):
    embed = discord.Embed(
        title="Bot Version",
        description="FlameCoder Obfuscate Bot",
        color=0x3498db,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Version", value="V3", inline=False)
    embed.set_footer(text="Thank you for using FlameCoder Obfuscate", icon_url=bot.user.avatar.url)
    await ctx.send(embed=embed)

# Command to show bot help
@bot.command(name='help_custom')
async def help(ctx):
    embed = discord.Embed(
        title="FlameCoder Obfuscate Bot Help",
        description="Here are the commands you can use with this bot:",
        color=0xf39c12,
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="!obfuscate", value="Obfuscate an attached .lua or .txt file with the default settings.", inline=False)
    embed.add_field(name="!obfuscate_with_preset [preset]", value="Obfuscate an attached .lua or .txt file with a specified preset (e.g., Low, Medium, High).", inline=False)
    embed.add_field(name="!version", value="Show the current version of the bot.", inline=False)
    embed.set_footer(text="Thank you for using FlameCoder Obfuscate", icon_url=bot.user.avatar.url)
    await ctx.send(embed=embed)

# Run the bot with the provided token
keep_alive()
bot.run(bot_token)