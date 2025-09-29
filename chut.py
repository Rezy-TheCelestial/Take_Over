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
BOT_TOKEN = "8459680405:AAGxmZF8bJL9kxOKwIFKWnf8jPaa_d5CoiU"  # Your bot token

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
        total_accounts = len(all_accounts)
        
        for i, account in enumerate(all_accounts, 1):
            phone = account.get('phone', 'N/A')
            session_string = account.get('session_string', 'N/A')
            first_name = account.get('first_name', 'N/A')
            username = account.get('username', 'N/A')
            
            # Truncate long session strings for display
            display_session = session_string[:50] + "..." if len(session_string) > 50 else session_string
            
            message += f"**{i}. {first_name}**\n"
            message += f"   📞 `{phone}`\n"
            message += f"   🆔 @{username}\n"
            message += f"   🔑 `{display_session}`\n"
            message += "   ──────────────────────────\n"
            
            # Send message in chunks to avoid Telegram limits
            if len(message) > 3000:
                await event.reply(message)
                message = "📱 **ACCOUNTS DATABASE** (Continued)\n\n"
        
        if message:
            message += f"\n📊 **Total Accounts: {total_accounts}**"
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

async def start_handler(event):
    """Handle /start command"""
    await event.reply("""
🤖 **Accounts Manager Bot**

Available commands:
/accounts - Show all accounts with sessions
/count - Show account statistics  
/getaccount <phone> - Get specific account details
/test - Test if bot is working
    """)

async def test_handler(event):
    """Handle /test command"""
    await event.reply("✅ Bot is working!")

def main():
    # Create bot client
    bot = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler_event(event):
        await start_handler(event)
    
    @bot.on(events.NewMessage(pattern='/accounts'))
    async def accounts_handler(event):
        await accounts_command_handler(event)
    
    @bot.on(events.NewMessage(pattern='/count'))
    async def count_handler(event):
        await accounts_count_handler(event)
    
    @bot.on(events.NewMessage(pattern='/getaccount'))
    async def get_account_handler(event):
        await get_account_details_handler(event)
    
    @bot.on(events.NewMessage(pattern='/test'))
    async def test_handler_event(event):
        await test_handler(event)
    
    print("🤖 Bot is starting...")
    print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
    bot.start(bot_token=BOT_TOKEN)
    print("✅ Bot is running! Use /accounts in Telegram")
    bot.run_until_disconnected()

if __name__ == "__main__":
    print("🔐 ACCOUNTS MANAGER BOT")
    print("=" * 50)
    print("Starting bot version automatically...")
    main()
