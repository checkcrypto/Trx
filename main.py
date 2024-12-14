import random
import requests
from mnemonic import Mnemonic
from bip32utils import BIP32Key
from eth_account import Account
from telegram import Update
from telegram.ext import Application, CommandHandler
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)

# Telegram bot token
TOKEN = '7961595239:AAE72trvWlWG2srUhYazbscEZeJykzdQFFQ'  # Replace with your bot's token

# Mnemonic setup
mnemo = Mnemonic("english")
seedlist = ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd",
            "abuse", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic",
            "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add",
            "addict", "address", "adjust", "admit"]

count = 0  # Address counter

# Function to generate a valid mnemonic
def generate_valid_mnemonic():
    while True:
        phrase = random.sample(seedlist, 12)
        phrase_str = ' '.join(phrase)
        if mnemo.check(phrase_str):
            return phrase_str

# Derive ETH address from mnemonic
def mnemonic_to_eth_address(mnemonic):
    seed = mnemo.to_seed(mnemonic)
    bip32_root_key = BIP32Key.fromEntropy(seed)
    bip32_child_key = bip32_root_key.ChildKey(44 + 0x80000000)  # BIP44 path for ETH (coin type 60)
    bip32_child_key = bip32_child_key.ChildKey(0).ChildKey(0)  # Account 0, external chain
    private_key = bip32_child_key.PrivateKey()

    account = Account.from_key(private_key)
    return account.address

# Derive BNB address from mnemonic
def mnemonic_to_bnb_address(mnemonic):
    seed = mnemo.to_seed(mnemonic)
    bip32_root_key = BIP32Key.fromEntropy(seed)
    bip32_child_key = bip32_root_key.ChildKey(44 + 0x80000000)  # BIP44 path for BNB (coin type 714)
    bip32_child_key = bip32_child_key.ChildKey(0).ChildKey(0)  # Account 0, external chain
    private_key = bip32_child_key.PrivateKey()

    account = Account.from_key(private_key)
    return account.address

# Derive TRX address from mnemonic
def mnemonic_to_trx_address(mnemonic):
    seed = mnemo.to_seed(mnemonic)
    bip32_root_key = BIP32Key.fromEntropy(seed)
    bip32_child_key = bip32_root_key.ChildKey(44 + 0x80000000)  # BIP44 path for TRX (coin type 195)
    bip32_child_key = bip32_child_key.ChildKey(0).ChildKey(0)  # Account 0, external chain
    private_key = bip32_child_key.PrivateKey()

    # Derive TRX address from private key using TronGrid API
    url = "https://api.trongrid.io/wallet/getaddress"
    response = requests.post(url, json={"privateKey": private_key.hex()})
    address = response.json().get("address", "")
    return address

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

# Check TRX balance
def check_trx_balance(address):
    url = f"https://api.trongrid.io/v1/accounts/{address}"
    response = requests.get(url)
    data = response.json()

    if "data" in data and len(data["data"]) > 0:
        balance = data["data"][0].get("balance", 0) / 1e6  # Convert Sun to TRX
        return balance
    return 0

# Find addresses with balances
async def find_crypto_with_balance(update: Update, context):
    global count
    message = await update.message.reply_text("Searching for addresses with balance...")

    while True:
        mnemonic = generate_valid_mnemonic()

        # Derive addresses
        eth_address = mnemonic_to_eth_address(mnemonic)
        bnb_address = mnemonic_to_bnb_address(mnemonic)
        trx_address = mnemonic_to_trx_address(mnemonic)

        # Check balances
        eth_balance = check_eth_balance(eth_address)
        bnb_balance = check_bnb_balance(bnb_address)
        trx_balance = check_trx_balance(trx_address)

        count += 1

        if count % 1000 == 0:  # Update every 100 addresses checked
            msg = f"Checked {count} addresses\n"
            msg += f"Mnemonic: {mnemonic}\n"
            msg += f"ETH Address: {eth_address} | Balance: {eth_balance} ETH\n"
            msg += f"BNB Address: {bnb_address} | Balance: {bnb_balance} BNB\n"
            msg += f"TRX Address: {trx_address} | Balance: {trx_balance} TRX\n"
            await message.edit_text(msg)

        if eth_balance > 0 or bnb_balance > 0 or trx_balance > 0:
            found_message = f"🎉 Found balance!\nMnemonic: {mnemonic}\n"
            if eth_balance > 0:
                found_message += f"ETH Address: {eth_address} | Balance: {eth_balance} ETH\n"
            if bnb_balance > 0:
                found_message += f"BNB Address: {bnb_address} | Balance: {bnb_balance} BNB\n"
            if trx_balance > 0:
                found_message += f"TRX Address: {trx_address} | Balance: {trx_balance} TRX\n"
            found_message += f"Checked Addresses: {count}"
            await message.edit_text(found_message)
            break

# Start command
async def start(update: Update, context):
    await update.message.reply_text("Starting to search for crypto addresses with balance...")
    await find_crypto_with_balance(update, context)

# Set up the Application and dispatcher
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == '__main__':
    main()