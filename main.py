import random
import requests
from mnemonic import Mnemonic
from bip32utils import BIP32Key
from eth_account import Account
from telegram import Update
from telegram.ext import Application, CommandHandler
import logging

# Enable logging for your bot
logging.basicConfig(level=logging.INFO)

# Suppress httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Telegram bot token
TOKEN = '8156418368:AAFIQaZ2GBfZ3hQzkRJDrLRJELwJLyyXT4U'  # Replace with your bot's token

# Mnemonic setup
mnemo = Mnemonic("english")

# Count of scanned addresses
count = 0  

# Function to generate a valid mnemonic
def generate_valid_mnemonic():
    # Generate a valid mnemonic from the BIP39 standard
    phrase = mnemo.generate(strength=128)  # Strength of 128 bits generates a 12-word mnemonic
    return phrase

# Derive ETH address from mnemonic
def mnemonic_to_eth_address(mnemonic):
    seed = mnemo.to_seed(mnemonic)  # Convert mnemonic to seed
    bip32_root_key = BIP32Key.fromEntropy(seed)  # Create a BIP32 root key from the seed
    bip32_child_key = bip32_root_key.ChildKey(44 + 0x80000000)  # BIP44 path for ETH (coin type 60)
    bip32_child_key = bip32_child_key.ChildKey(0).ChildKey(0)  # Account 0, external chain
    private_key = bip32_child_key.PrivateKey()

    account = Account.from_key(private_key)  # Use eth_account to get the address
    return account.address

# Derive BNB address from mnemonic
def mnemonic_to_bnb_address(mnemonic):
    seed = mnemo.to_seed(mnemonic)  # Convert mnemonic to seed
    bip32_root_key = BIP32Key.fromEntropy(seed)  # Create a BIP32 root key from the seed
    bip32_child_key = bip32_root_key.ChildKey(44 + 0x80000000)  # BIP44 path for BNB (coin type 714)
    bip32_child_key = bip32_child_key.ChildKey(0).ChildKey(0)  # Account 0, external chain
    private_key = bip32_child_key.PrivateKey()

    account = Account.from_key(private_key)  # Use eth_account to get the address
    return account.address

# Check ETH balance
def check_eth_balance(address):
    url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "1":
        balance = int(data["result"]) / 10**18  # Convert Wei to ETH
        return balance
    return 0

# Check BNB balance
def check_bnb_balance(address):
    url = f"https://api.bscscan.com/api?module=account&action=balance&address={address}&tag=latest"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "1":
        balance = int(data["result"]) / 10**18  # Convert Wei to BNB
        return balance
    return 0

# Find addresses with balances
async def find_crypto_with_balance(update: Update, context):
    global count
    message = await update.message.reply_text(
        "✨ Awesome! Starting a scan on ETH or BNB... 🌍\n"
        "🌱 Seed: .......\n"
        "🏦 Address: .......\n"
        "🔄 Scanned wallets: 0"
        )

    while True:
        # Generate mnemonic and derive addresses
        mnemonic = generate_valid_mnemonic()
        eth_address = mnemonic_to_eth_address(mnemonic)
        bnb_address = mnemonic_to_bnb_address(mnemonic)

        # Check balances
        eth_balance = check_eth_balance(eth_address)
        bnb_balance = check_bnb_balance(bnb_address)

        count += 1

        # Update progress message every 1000 checks
        if count % 1000 == 0:
            msg = f"🔄 Scanned wallets: {count}\n"
            msg += f"🌱Seed: {mnemonic}\n"
            msg += f"🏦ETH Address: {eth_address} | Balance: {eth_balance} ETH\n"
            msg += f"🏦BNB Address: {bnb_address} | Balance: {bnb_balance} BNB\n"
            await message.edit_text(msg)

        # Send a separate message if balance is found
        if eth_balance > 0 or bnb_balance > 0:
            found_message = f"🎉 Found balance!\nMnemonic: {mnemonic}\n"
            if eth_balance > 0:
                found_message += f"ETH Address: {eth_address} | Balance: {eth_balance} ETH\n"
            if bnb_balance > 0:
                found_message += f"BNB Address: {bnb_address} | Balance: {bnb_balance} BNB\n"
            found_message += f"Checked Addresses: {count}"
            await update.message.reply_text(found_message)

# Start command
async def start(update: Update, context):
    await update.message.reply_text("Searching for addresses with balance...")
    await find_crypto_with_balance(update, context)

# Set up the Application and dispatcher
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()
