from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, ACCOUNTS_COLL

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.accounts = self.db[ACCOUNTS_COLL]
    
    def get_all_accounts(self):
        return list(self.accounts.find({}))
    
    def get_account_by_phone(self, phone):
        return self.accounts.find_one({'phone_number': phone})
    
    def update_account_status(self, phone, status, has_2fa=False):
        self.accounts.update_one(
            {'phone_number': phone},
            {'$set': {
                'status': status,
                'has_2fa': has_2fa,
                'last_updated': datetime.now()
            }}
        )
    
    def close(self):
        self.client.close()
