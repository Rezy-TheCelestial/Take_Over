from telethon import TelegramClient, events
from telethon.sessions import StringSession
import pymongo
import asyncio
import os

# MongoDB configuration
MONGO_URI = "mongodb+srv://botuser:botpass123@cluster0.juyoluw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "guess_bot"
ACCOUNTS_COLL = "Accounts"

# Telegram Bot configuration
SESSION_NAME = "hexamon_bot_telethon"
API_ID = 29288199
API_HASH = "9ff308629870e029601d2ee667821506"
BOT_TOKEN = "8459680405:AAGxmZF8bJL9kxOKwIFKWnf8jPaa_d5CoiU"  # Replace with your bot token

# Initialize MongoDB client
try:
    mongo_client = pymongo.MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    accounts_collection = db[ACCOUNTS_COLL]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

async def accounts_command_handler(event):
    """Handle /accounts command"""
    try:
        # Get all accounts from MongoDB
        all_accounts = list(accounts_collection.find({}))
        
        if not all_accounts:
            await event.reply("📭 No accounts found in database.")
            return
        
        message = "📱 **ACCOUNTS DATABASE**\n\n"
        
        for i, account in enumerate(all_accounts, 1):
            phone = account.get('phone', 'N/A')
            session_string = account.get('session_string', 'N/A')
            first_name = account.get('first_name', 'N/A')
            username = account.get('username', 'N/A')
            
            # Truncate long session strings for display
            display_session = session_string[:50] + "..." if len(session_string) > 50 else session_string
            
            message += f"**{i}. Account Details:**\n"
            message += f"   👤 **Name:** {first_name}\n"
            message += f"   📞 **Phone:** `{phone}`\n"
            message += f"   🆔 **Username:** @{username}\n"
            message += f"   🔑 **Session:** `{display_session}`\n"
            message += "   " + "─" * 30 + "\n\n"
        
        # Send the message (Telegram has 4096 character limit)
        if len(message) > 4000:
            # Split into multiple messages if too long
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await event.reply(part)
        else:
            await event.reply(message)
            
    except Exception as e:
        await event.reply(f"❌ Error fetching accounts: {e}")

async def accounts_count_handler(event):
    """Handle /count command to show account statistics"""
    try:
        total_accounts = accounts_collection.count_documents({})
        accounts_with_phone = accounts_collection.count_documents({"phone": {"$ne": "N/A", "$exists": True}})
        accounts_with_session = accounts_collection.count_documents({"session_string": {"$ne": "N/A", "$exists": True}})
        
        message = f"""
📊 **ACCOUNTS STATISTICS**

📱 Total Accounts: **{total_accounts}**
📞 With Phone: **{accounts_with_phone}**
🔑 With Session: **{accounts_with_session}**
        """
        await event.reply(message)
        
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

async def get_account_details_handler(event):
    """Handle /getaccount command to get specific account details"""
    try:
        # Extract phone number from command
        command_text = event.text.split()
        if len(command_text) < 2:
            await event.reply("❌ Usage: /getaccount <phone_number>")
            return
        
        phone = command_text[1]
        account = accounts_collection.find_one({"phone": phone})
        
        if not account:
            await event.reply(f"❌ No account found with phone: {phone}")
            return
        
        session_string = account.get('session_string', 'N/A')
        first_name = account.get('first_name', 'N/A')
        username = account.get('username', 'N/A')
        
        message = f"""
🔍 **ACCOUNT DETAILS**

👤 **Name:** {first_name}
📞 **Phone:** `{phone}`
🆔 **Username:** @{username}
🔑 **Session String:**
`{session_string}`
        """
        
        await event.reply(message)
        
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

def main():
    # Create bot client
    bot = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        await event.reply("""
🤖 **Accounts Manager Bot**

Available commands:
/accounts - Show all accounts with sessions
/count - Show account statistics  
/getaccount <phone> - Get specific account details
        """)
    
    @bot.on(events.NewMessage(pattern='/accounts'))
    async def accounts_handler(event):
        await accounts_command_handler(event)
    
    @bot.on(events.NewMessage(pattern='/count'))
    async def count_handler(event):
        await accounts_count_handler(event)
    
    @bot.on(events.NewMessage(pattern='/getaccount'))
    async def get_account_handler(event):
        await get_account_details_handler(event)
    
    print("🤖 Bot is starting...")
    bot.start(bot_token=BOT_TOKEN)
    print("✅ Bot is running! Use /accounts to see all accounts")
    bot.run_until_disconnected()

# ALTERNATIVE: If you want to run without bot token (user account)
async def user_account_version():
    """Version that runs with user account instead of bot"""
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    await client.start()
    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name}")
    
    @client.on(events.NewMessage(pattern='/accounts'))
    async def handler(event):
        if event.is_private:  # Only respond to private messages
            await accounts_command_handler(event)
    
    print("👤 User account version running! Use /accounts in private chat")
    await client.run_until_disconnected()

if __name__ == "__main__":
    print("🔐 ACCOUNTS MANAGER")
    print("=" * 50)
    
    choice = input("Choose version:\n1. Bot version (needs bot token)\n2. User account version\nChoice: ").strip()
    
    if choice == "1":
        # You need to set BOT_TOKEN variable above
        if "YOUR_BOT_TOKEN_HERE" in BOT_TOKEN:
            print("❌ Please set BOT_TOKEN variable in the code")
        else:
            main()
    else:
        asyncio.run(user_account_version())
