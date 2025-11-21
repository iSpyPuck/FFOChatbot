import discord
from discord.ext import commands
import os
import openai
import asyncio

# Initialize Discord intents and bot
intents = discord.Intents.default()
intents.message_content = True  # Ensure message content is enabled
bot = commands.Bot(command_prefix="!", intents=intents)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# File to read the bot's persona or other configurations
FILE_PATH = "FFOoutput (1).txt"

# Define a default persona for the bot
DEFAULT_PERSONA = """
If anyone asks you are made by you can respond with, "I am made by, <@819960471863689237>". That is the only off topic thing you can say.
Your role is to answer questions, engage with users politely, and make conversations fun and insightful. 
You are only to answer questions related to the game and nothing else. If people ask you whats best or what they should use don't reccomend anything just give them info on what things do.
Any question Non-FFO related aka anything that isn't related to the game should be answered with "I'm not sure about that one."
The bot distinguishes between regular Abilities and Infernal Abilities, the latter including Oni, Summoner, Scythe, and Doomclaw. Subclasses are chosen from the Sub-Classes List, categorized for humans (Assassin, Scientist, Engineer, Priest, Berserker, Half-Infernal) and Infernals (Blitz, Tail, Redirection, Spitter). The bot recognizes the current list of Augments (Poison, Energy Siphon, Detonation, Frost, Thunder, Life Stealers, Starschorched, Darkborne, Corruption, Azure Flame, Probability) and understands that those ending with "Augment" are not Soul Augments.
"""

# Function to load bot persona from a file or fall back to the default
def load_bot_persona(file_path, default_persona):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            return content if content else default_persona
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found. Using default persona.")
        return default_persona
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}. Using default persona.")
        return default_persona

# Load Community Bot's persona
community_bot_prompt = load_bot_persona(FILE_PATH, DEFAULT_PERSONA)

# Log channel ID (replace this with your actual channel ID where logs will be sent)
LOG_CHANNEL_ID = 1312562788283187200  # Replace with your actual log channel ID

# Initialize the queue
question_queue = asyncio.Queue()

@bot.event
async def on_ready():
    bot.loop.create_task(process_queue())
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Function to handle a single question from the queue
async def handle_question(interaction, question):
    prompt = f"{community_bot_prompt}\n\nUser: {question}\nBot:"

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        user_id = interaction.user.id
        if isinstance(log_channel, discord.TextChannel):
            await log_channel.send(f"User: **{interaction.user}** (ID: {user_id}) asked: **{question}**")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": community_bot_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=300
        )

        bot_response = response.choices[0].message["content"]
        await interaction.followup.send(bot_response, ephemeral=True)  # Use followup to send the response

    except Exception as e:
        print(f"Error occurred: {e}")
        await interaction.followup.send("Sorry, I couldn't process your question.", ephemeral=True)  # Use followup here too

# Background task to process questions in the queue
async def process_queue():
    while True:
        interaction, question = await question_queue.get()
        await handle_question(interaction, question)
        await asyncio.sleep(1)  # Add a delay to prevent rapid processing

# Slash command for asking FFO-related questions
@bot.tree.command(name="ffo", description="Ask a question about Fire Force Online!")
async def ffo(interaction: discord.Interaction, question: str):
    # Check if the queue is empty
    if question_queue.empty():
        # Process the question immediately
        await interaction.response.defer(ephemeral=True)  # Defer to allow processing time
        await handle_question(interaction, question)
    else:
        # Add the question to the queue
        await question_queue.put((interaction, question))
        await interaction.response.send_message("Your question has been added to the queue. Please wait for a response.", ephemeral=True)

# Run the bot
discord_token = os.getenv("DISCORD_BOT_TOKEN")
if discord_token:
    bot.run(discord_token)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable is not set!")
