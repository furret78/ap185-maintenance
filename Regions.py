from BaseClasses import Entrance, Region
from .Tools import get_progress_item_requirement
from .variables.boss_and_stage import *


def create_and_connect_regions(world):
    create_all_regions(world)
    connect_regions(world)


def create_all_regions(world):
    region_menu = Region(world.origin_region_name, world.player, world.multiworld)
    regions = [region_menu]

    game_region_id = 0
    for game_region in REGION_LIST:
        regions.append(Region(game_region, world.player, world.multiworld))
        game_region_id += 1

    world.multiworld.regions += regions


def get_regions_dict(world) -> dict[str, Region]:
    """
    Retrieves all of the game's regions as a dictionary, including the menu.
    The dictionary uses the short stage names as keys.
    See REGION_LIST in boss_and_stage.py for the rest of the details.
    """
    region_dict = {
        world.origin_region_name: world.get_region(world.origin_region_name)
    }

    for game_region in REGION_LIST:
        region_dict[game_region] = world.get_region(game_region)

    return region_dict


def connect_regions(world):
    region_menu = world.get_region(world.origin_region_name)
    region_endstage = world.get_region(ENDSTAGE_CHOOSE_NAME)

    all_regions_dict = get_regions_dict(world)

    # 0 is Origin/Menu.
    # 1-8 is Tutorial-Challenge.
    # 9 is Card Dex
    # 10 is Market Card Reward
    # These use the short names as in REGION_LIST.

    # From the menu to the rest of the game.
    for region_name in all_regions_dict.keys():
        if region_name not in ORIGIN_TO_REGION_DICT.keys(): continue
        region_menu.connect(all_regions_dict[region_name], ORIGIN_TO_REGION_DICT[region_name])

    # From the Markets to the card selection at the end.
    for region_name in all_regions_dict.keys():
        if region_name not in STAGE_TO_CARD_REWARD_DICT.keys(): continue
        if world.options.disable_challenge_logic and region_name == CHALLENGE_NAME: continue
        all_regions_dict[region_name].connect(region_endstage, STAGE_TO_CARD_REWARD_DICT[region_name])