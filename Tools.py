import shutil
import os

from .variables.boss_and_stage import *
from .variables.card_const import CARD_ID_TO_NAME
from .variables.meta_data import *
from .variables.music_and_achiev import *


def getAddressFromPointer(pm, static_base, offsets=None):
    """
    Retrieves the "name" of the address holding data, derived from a static base address and its offsets.
    """
    # The value of a pointer holds the "name" of another address.
    # Reading the other address would yield its data.
    # e.g. th185.exe+?????'s location holds the "name" of another address.
    # Read the value held at th185.exe+????? to retrieve this "name".
    # That value is the address that the client needs.
    # It changes every time, but this helper reliably tells the client what it is.
    address = static_base
    if offsets is None: return pm.read_uint(address)
    if offsets is list:
        for offset_index in offsets[:-1]:
            address = pm.read_uint(address)
            address += offset_index
        return pm.read_uint(address)

    address = pm.read_uint(static_base)
    address += offsets
    return pm.read_uint(address)


def getPointerAddress(pm, base, offsets):
    address = base
    for offset in offsets[:-1]:
        address = pm.read_uint(address)
        address += offset
    return pm.read_uint(address) + offsets[-1]


def clamp(n, smallest, largest): return max(smallest, min(n, largest))


def copy_paste_to_path(source_file, destination_directory):
    filename = os.path.basename(source_file)
    destination_path = os.path.join(destination_directory, filename)
    if os.path.exists(destination_path):
        os.remove(destination_path)
    shutil.copy2(source_file, destination_path)


def get_item_index_save_name(seed_name, team_number, slot_number) -> str:
    return LAST_INDEX_FILE_NAME + str(seed_name) + str(team_number) + str(slot_number) + JSON_EXTENSION


def convert_currency_to_joules(amount: int, currency_type: int = 0) -> int:
    if currency_type == CURRENCY_FUNDS_ID or currency_type is None:
        return amount * RATES_FUNDS_TO_JOULES
    elif currency_type == CURRENCY_BULLET_MONEY_ID:
        return amount * RATES_BULLET_MONEY_TO_JOULES
    else:
        return 0

def convert_joules_to_currency(amount: int, currency_type: int = 0) -> int:
    if currency_type == CURRENCY_FUNDS_ID or currency_type is None:
        return amount // RATES_FUNDS_TO_JOULES
    elif currency_type == CURRENCY_BULLET_MONEY_ID:
        return amount // RATES_BULLET_MONEY_TO_JOULES
    else:
        return 0

def get_energy_withdraw_tag(seed_name, currency_type: int):
    final_currency_type = "fs"

    if currency_type == CURRENCY_BULLET_MONEY_ID:
        final_currency_type = "bm"

    return str(seed_name) + "-" + final_currency_type

def get_progress_item_count(starting_market: int) -> int:
    """
    Returns how many progress items should be pushed based on the Starting Market.
    By default, 0 progress items = 0 stages unlocked.

    Tutorial - 1
    1st Market - 2
    2nd Market - 3
    3rd Market - 4
    4th Market - 5
    5th Market - 6
    6th Market - 7
    End of Market - 8
    Challenge Market - 9
    """
    return clamp(starting_market + 1, 1, 9)

def get_progress_item_requirement(stage_name: str, use_full_name: bool = False) -> int:
    if use_full_name:
        return clamp(STAGE_NAME_TO_ID[STAGE_FULL_TO_SHORT_NAME[stage_name]] + 1, 1, 9)
    else:
        return clamp(STAGE_NAME_TO_ID[stage_name] + 1, 1, 9)


def get_boss_location_name_str(market_stage_id: int, boss_name: str, is_defeat: bool = False) -> str:
    """
    Gets the location name according to Stage ID and Boss name.
    Has an Encounter and Defeat variant.
    """
    locationType: str = ENCOUNTER_TYPE_NAME
    if is_defeat: locationType = DEFEAT_TYPE_NAME
    return f"[{STAGE_LIST[market_stage_id]}] {boss_name} - {locationType}"


def get_card_location_name_str(card_id: str, is_dex: bool = False) -> str:
    """
    Gets the location name according to Ability Card string ID.
    Has a Shop Unlock and Dex Unlock variant.
    """
    regionName: str = ENDSTAGE_CHOOSE_NAME
    if is_dex: regionName = CARD_DEX_NAME
    return f"[{regionName}] {CARD_ID_TO_NAME[card_id]}"


def get_music_location_name_str(track_id: int) -> str:
    """
    Gets the location name according to the Music Room dictionary.
    Argument is clamped before assigning.
    """
    safe_id_used = clamp(track_id, 0, 9)
    return f"[{MUSIC_ROOM_UNLOCK_STR}] {safe_id_used + 1}. {MUSIC_ROOM_NAME_DICT[safe_id_used]}"


def get_achievement_location_name_str(achievement_id: int) -> str:
    """
    Gets the location name according to the Achievements dictionary.
    Argument is clamped before assigning.
    """
    safe_id_used = clamp(achievement_id, 0, 11)
    return f"{ACHIEVE_UNLOCK_STR}{safe_id_used + 1}: {ACHIEVE_NAME_DICT[safe_id_used]}"


def get_boss_id_according_to_internal(boss_id: int) -> int:
    """
    Retrieves the boss ID according to how it's internally set in the game.
    """
    if boss_id == BOSS_NITORI:
        return boss_id + 11
    elif boss_id == BOSS_TAKANE:
        return boss_id + 3
    elif boss_id == BOSS_CHIMATA:
        return boss_id
    elif boss_id >= BOSS_TSUKASA:
        return boss_id + 1

    return boss_id + 2


def get_stage_id_according_to_internal(stage_id: int) -> int:
    """
    Retrieves the stage ID according to how it's internally set in the game.
    """
    return stage_id + 1

def get_boss_and_stage_id(stage_id: int, boss_id: int) -> list[int]:
    """
    Retrieves both the stage ID and boss ID according to the game's internal values.
    The first returned value is the stage ID, while the second is the boss ID.
    """
    hidden_boss_id = get_boss_id_according_to_internal(boss_id)
    hidden_stage_id = get_stage_id_according_to_internal(stage_id)
    # Tutorial has exactly 1 boss. That is Mike.
    # That Mike is special.
    if stage_id == TUTORIAL_ID:
        return [hidden_stage_id, 1]
    return [hidden_stage_id, hidden_boss_id]