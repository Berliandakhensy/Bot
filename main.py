import discord
import os
import time
import logging
import subprocess
from discord import File
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
from itertools import cycle
import aiofiles
import shutil

# Masukkan token bot Anda langsung di sini
BOT_TOKEN = "MTMxMTg0NzMyNjg3MTk3ODAyNQ.GEhQij.OiNGIoGTJ1ZvcbkLTLs4pn_isP82h3-NAhhVic"

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Bot intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Web server for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "<h1>🔥 FlameCoder Obfuscate Bot is Active 🔥</h1>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Rotating status messages
status_list = cycle([
    "🔥 Obfuscating with Style 🔥",
    "🛠️ Transforming Code 🛠️",
    "🚀 Improving Security 🚀",
    "👾 Debugging with Finesse 👾"
])

@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=discord.Game(next(status_list)))

@bot.event
async def on_ready():
    logging.info(f'✨ Bot {bot.user} has successfully started. ✨')
    change_status.start()

# Command: obfuscate file
@bot.command(name="obfuscate")
async def obfuscate(ctx):
    if not ctx.message.attachments:
        await ctx.send("⚠️ Please attach a .lua or .txt file for obfuscation.")
        return
    
    attachment = ctx.message.attachments[0]
    if not (attachment.filename.endswith(".lua") or attachment.filename.endswith(".txt")):
        await ctx.send("⚠️ Invalid file type. Please upload a .lua or .txt file.")
        return

    file_name = f"{ctx.author.id}_{attachment.filename}"
    output_file_name = f"obfuscated_{file_name}"

    # Download and process file
    try:
        # Save the uploaded file
        async with aiofiles.open(file_name, "wb") as f:
            await f.write(await attachment.read())
        
        # Simulate obfuscation process
        obfuscation_time = time.time()
        await ctx.send(f"⏳ Obfuscating your file `{attachment.filename}`...")
        await asyncio.sleep(2)  # Simulate processing delay
        shutil.copy(file_name, output_file_name)  # Just copies for demo purposes
        obfuscation_time = time.time() - obfuscation_time

        # Send back the obfuscated file
        obfuscated_file = File(output_file_name, filename=f"Obfuscated_{attachment.filename}")
        await ctx.send(f"✅ Obfuscation complete in {obfuscation_time:.2f} seconds.", file=obfuscated_file)
        
    except Exception as e:
        logging.error(f"Error obfuscating file: {e}")
        await ctx.send("⚠️ An error occurred during the obfuscation process.")
    finally:
        # Cleanup
        for file in [file_name, output_file_name]:
            if os.path.exists(file):
                os.remove(file)

# Command: version
@bot.command(name="version")
async def version(ctx):
    embed = discord.Embed(
        title="Bot Version",
        description="FlameCoder Obfuscate Bot",
        color=0x3498db
    )
    embed.add_field(name="Version", value="V3.0", inline=False)
    embed.set_footer(text="Powered by FlameCoder")
    await ctx.send(embed=embed)

# Command: help
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="FlameCoder Obfuscate Bot - Help",
        description="Here are the commands you can use:",
        color=0xf39c12
    )
    embed.add_field(name="!obfuscate", value="Attach a .lua or .txt file to obfuscate.", inline=False)
    embed.add_field(name="!version", value="Check the bot version.", inline=False)
    await ctx.send(embed=embed)

# Keep bot alive and run
keep_alive()
bot.run(BOT_TOKEN)