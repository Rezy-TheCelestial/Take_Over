import os

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://pokemon_bot_user:PokemonBot2024!Secure@cluster0pokemon-bot-clu.iveqoue.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0pokemon-bot-cluster")
DB_NAME = "pokemon_guess_bot"
ACCOUNTS_COLL = "Accounts"

# Telegram API
API_ID = int(os.getenv("API_ID", "29288199"))
API_HASH = os.getenv("API_HASH", "9ff308629870e029601d2ee667821506")

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8275817464:AAGnjwnKXvJ9NrTNE4SEnsZAHs1gm1bLDP8")

# Security
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "Secure@2024")
