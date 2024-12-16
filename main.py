import random
import requests
from mnemonic import Mnemonic
from bip32utils import BIP32Key
from eth_account import Account
from telegram import Update
from telegram.ext import Application, CommandHandler
from concurrent.futures import ThreadPoolExecutor
import logging

# Enable logging for your bot
logging.basicConfig(level=logging.INFO)

# Suppress httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Telegram bot token
TOKEN = '8044956388:AAGWX1cEa-vfwbeBjjvsPpx4J9X8cg5KoHk'  # Replace with your bot's token

# Mnemonic setup
mnemo = Mnemonic("english")
seedlist = ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd",
            "abuse", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic",
            "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add",
            "addict", "address", "adjust", "admit"]

count = 0  # Address counter
executor = ThreadPoolExecutor(max_workers=2)  # Thread pool for concurrent tasks

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

# Check balances in parallel
def check_balances(mnemonic):
    eth_address = mnemonic_to_eth_address(mnemonic)
    bnb_address = mnemonic_to_bnb_address(mnemonic)

    eth_balance = check_eth_balance(eth_address)
    bnb_balance = check_bnb_balance(bnb_address)

    return mnemonic, eth_address, eth_balance, bnb_address, bnb_balance

# Find addresses with balances using ThreadPoolExecutor
async def find_crypto_with_balance(update: Update, context):
    global count
    message = await update.message.reply_text("Searching for addresses with balance...")

    def task_callback(result):
        nonlocal message
        mnemonic, eth_address, eth_balance, bnb_address, bnb_balance = result
        nonlocal count

        count += 1

        # Update progress message every 1000 checks
        if count % 1000 == 0:
            msg = f"Checked {count} addresses\n"
            msg += f"Latest Mnemonic: {mnemonic}\n"
            msg += f"ETH Address: {eth_address} | Balance: {eth_balance} ETH\n"
            msg += f"BNB Address: {bnb_address} | Balance: {bnb_balance} BNB\n"
            context.bot.loop.create_task(message.edit_text(msg))

        # Send a separate message if balance is found
        if eth_balance > 0 or bnb_balance > 0:
            found_message = f"🎉 Found balance!\nMnemonic: {mnemonic}\n"
            if eth_balance > 0:
                found_message += f"ETH Address: {eth_address} | Balance: {eth_balance} ETH\n"
            if bnb_balance > 0:
                found_message += f"BNB Address: {bnb_address} | Balance: {bnb_balance} BNB\n"
            found_message += f"Checked Addresses: {count}"
            context.bot.loop.create_task(update.message.reply_text(found_message))

    while True:
        mnemonic = generate_valid_mnemonic()
        future = executor.submit(check_balances, mnemonic)
        future.add_done_callback(lambda f: task_callback(f.result()))

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
