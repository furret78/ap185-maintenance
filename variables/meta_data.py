"""
Variables: Meta data about the game.
"""

FILE_NAME = "th185.exe"
DISPLAY_NAME = "Black Market of Bulletphilia ~ 100th Black Market"
SHORT_NAME = "Touhou 18.5"

# Save data management
APPDATA_PATH = "\\ShanghaiAlice\\th185\\"
# Scorefile
SCOREFILE_NAME = "scoreth185.dat"
SCOREFILE_BACKUP_NAME = "scoreth185bak.dat"
# Last received item list
LAST_INDEX_FILE_NAME = "th185ap_"
JSON_EXTENSION = ".json"
JSON_SLOT_NAME = "slot_name"
JSON_SLOT_ITEMS = "items"

# Various client messages
SERVER_NOT_CONNECTED_MSG = "The client hasn't connected to the server yet!"
GAME_NOT_RUNNING_MSG = "The game isn't running!"

# Death Link
DEATH_LINK_TRIGGER_LIFE = 0
DEATH_LINK_TRIGGER_STAGE = 1

DEATH_LINK_LIFE_MSGS: list[str] = [
    " flew too close to a bullet.",
    " can't dodge very well.",
    " has a big hitbox.",
    " thought the bullets were made of candy.",
    " hit a fairy."
]

DEATH_LINK_STAGE_MSGS: list[str] = [
    " got kicked out of the Black Market.",
    " got kicked off the premises.",
    " fumbled their run.",
    " got folded like a deck of Ability Cards."
]

DEATH_LINK_GENERIC_MSGS: list[str] = [
    " pichuun'd.",
    " fell through a gap.",
    " got spirited away."
]

DEATH_LINK_NOT_ENABLED = "Death Link is not enabled for this slot."
DEATH_LINK_INFO_CHANGED = "Death Link trigger temporarily changed: "
DEATH_LINK_INFO_LIFE = "Upon losing a life, a Death Link will be sent."
DEATH_LINK_INFO_STAGE = "Upon failing a stage, a Death Link will be sent."

# Energy Link
MAX_FUNDS = 999999
MAX_BULLET_MONEY = 4294967295
RATES_FUNDS_TO_JOULES = 3*(10**8) # 3E8
RATES_BULLET_MONEY_TO_JOULES = RATES_FUNDS_TO_JOULES // 3
CURRENCY_FUNDS_ID = 0
CURRENCY_BULLET_MONEY_ID = 1
CURRENCY_FUNDS_ARGS_LIST: list[str] = ["f", "F", "funds", "Funds", "fund", "Fund"]
CURRENCY_BULLET_MONEY_ARGS_LIST: list[str] = ["b", "B", "bm", "Bm", "BM", "bullet", "Bullet", "bullet money", "Bullet Money", "bullet_money", "Bullet_Money"]
INTERACT_DEPOSIT_ARGS_LIST: list[str] = ["d", "D", "dp", "Dp", "deposit", "Deposit"]
INTERACT_WITHDRAW_ARGS_LIST: list[str] = ["w", "W", "wd", "Wd", "withdraw", "Withdraw"]
CURRENCY_NAME_FUNDS = "Funds"
CURRENCY_NAME_BULLET_MONEY = "Bullet Money"
INVALID_CURRENCY_STRING = "Invalid currency type!"
BULLET_MONEY_CANNOT_WITHDRAW = "Cannot withdraw Bullet Money. Enter a stage first."