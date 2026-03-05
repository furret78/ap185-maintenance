from typing import Dict

from .Regions import get_regions_dict
from .variables.card_const import *
from .variables.meta_data import *
from .Tools import get_boss_location_name_str, get_card_location_name_str, get_music_location_name_str, \
    get_achievement_location_name_str
from BaseClasses import Location
from .variables.music_and_achiev import MUSIC_ROOM_NAME_DICT, ACHIEVE_NAME_DICT, MUSIC_ROOM_UNLOCK_STR


class TouhouHBMLocation(Location):
    game: str = SHORT_NAME


def create_all_locations(world):
    create_regular_locations(world)


def get_boss_names_challenge_list() -> list[str]:
    """
    Gets all bosses that appears in Challenge Market.
    """
    result_boss_list: list[str] = []
    challenge_set_id = 1
    # This will iterate through the entire boss list.
    for boss_sets in ALL_BOSSES_LIST:
        if challenge_set_id <= TUTORIAL_ID or challenge_set_id >= STAGE_CHIMATA_ID: continue
        # Gets the actual list data of the current stage chosen.
        current_boss_set = ALL_BOSSES_LIST[challenge_set_id]
        # Iterate through it. If the index is 4 or more, that's a story boss.
        boss_challenge_id = 0
        for boss_challenge in current_boss_set:
            if boss_challenge_id >= 4: continue
            result_boss_list.append(boss_challenge)
            boss_challenge_id += 1
        # Move onto the next stage.
        challenge_set_id += 1

    # Return the final list.
    return result_boss_list


location_groups: Dict[str, set[str]] = {}

location_id_offset = 1
location_table = {} # Name to ID
location_id_to_name = {} # ID to Name
location_cards_id_to_card_string_id = {}

# Boss locations
stage_id = 0
for stages in STAGE_LIST:
    # Normal stages
    if stage_id < STAGE_CHALLENGE_ID:
        stage_boss_group: set[str] = set()
        # This goes through the boss list of a given market.
        for boss in ALL_BOSSES_LIST[stage_id]:
            currentBossStringEncounter: str = get_boss_location_name_str(stage_id, boss)
            currentBossStringDefeat: str = get_boss_location_name_str(stage_id, boss, True)
            # Add the boss Encounter locations.
            location_table[currentBossStringEncounter] = location_id_offset
            location_id_to_name[location_id_offset] = currentBossStringEncounter
            # Add the boss Defeat locations.
            location_table[currentBossStringDefeat] = location_id_offset + 1
            location_id_to_name[location_id_offset + 1] = currentBossStringDefeat
            # Offset the ID number.
            location_id_offset += 2

            stage_boss_group.add(currentBossStringEncounter)
            stage_boss_group.add(currentBossStringDefeat)
        location_groups.update({STAGE_SHORT_TO_FULL_NAME[stages]: stage_boss_group})

    # Challenge Market
    if stage_id == STAGE_CHALLENGE_ID:
        challenge_boss_group: set[str] = set()
        for boss in get_boss_names_challenge_list():
            currentBossStringEncounter: str = get_boss_location_name_str(STAGE_CHALLENGE_ID, boss)
            location_table[currentBossStringEncounter] = location_id_offset
            location_id_to_name[location_id_offset] = currentBossStringEncounter
            location_id_offset += 1
            challenge_boss_group.add(currentBossStringEncounter)
        location_groups.update({CHALLENGE_NAME_FULL: challenge_boss_group})

    stage_id += 1

# Card Shop locations at the end of each Market.
# Location name groups.
card_groups_list: list[set[str]] = [set(), set(), set(), set(), set(), set(), set(), set(), set()]

for card_string in ABILITY_CARD_LIST:
    # Automatically filter out Nazrin's cards.
    if card_string in ABILITY_CARD_CANNOT_EQUIP: continue
    if card_string == MALLET_CARD: continue

    cardLocationNameString: str = get_card_location_name_str(card_string, False)
    location_table[cardLocationNameString] = location_id_offset
    location_id_to_name[location_id_offset] = cardLocationNameString
    location_cards_id_to_card_string_id[location_id_offset] = card_string
    location_id_offset += 1

    # Location name grouping.
    # Tutorial (entirely exclusives)
    if card_string in STAGE_EXCLUSIVE_CARD_LIST[TUTORIAL_NAME]:
        card_groups_list[0].add(cardLocationNameString)
        continue
    # 1st Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[STAGE1_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string in STAGE1_CARD_LIST
        or card_string == LILY_WHITE_CARD):
        card_groups_list[1].add(cardLocationNameString)
    # 2nd Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[STAGE2_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string in STAGE1_CARD_LIST
        or card_string in STAGE2_CARD_LIST
        or card_string == LILY_WHITE_CARD
        or card_string == DOREMY_CARD):
        card_groups_list[2].add(cardLocationNameString)
    # 3rd Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[STAGE3_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string in STAGE1_CARD_LIST
        or card_string in STAGE2_CARD_LIST
        or card_string in STAGE3_CARD_LIST
        or card_string == LILY_WHITE_CARD
        or card_string == DOREMY_CARD):
        card_groups_list[3].add(cardLocationNameString)
    # 4th Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[STAGE4_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string in STAGE1_CARD_LIST
        or card_string in STAGE2_CARD_LIST
        or card_string in STAGE3_CARD_LIST
        or card_string in LATEGAME_CARD_LIST
        or card_string == LILY_WHITE_CARD
        or card_string == DOREMY_CARD):
        card_groups_list[4].add(cardLocationNameString)
    # 5th Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[STAGE5_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string in LATEGAME_CARD_LIST
        or card_string == LILY_WHITE_CARD
        or card_string == DOREMY_CARD):
        card_groups_list[5].add(cardLocationNameString)
    # 6th Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[STAGE6_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string in STAGE1_CARD_LIST
        or card_string in STAGE2_CARD_LIST
        or card_string in STAGE3_CARD_LIST
        or card_string in LATEGAME_CARD_LIST
        or card_string == LILY_WHITE_CARD
        or card_string == DOREMY_CARD):
        card_groups_list[6].add(cardLocationNameString)
    # End of Market
    if (card_string in STAGE_EXCLUSIVE_CARD_LIST[ENDSTAGE_NAME]
        or card_string in STAGE_COMMON_CARD_LIST
        or card_string == SEKIBANKI_CARD):
        card_groups_list[7].add(cardLocationNameString)
    # Challenge Market (unconditional)
    card_groups_list[8].add(cardLocationNameString)

for stage_short_name in STAGE_LIST:
    location_groups[STAGE_SHORT_TO_FULL_NAME[stage_short_name]].update(card_groups_list[STAGE_LIST.index(stage_short_name)])

# Card Dex locations.
# In location name group terms, these are "Everywhere". No need to do anything about them.
dex_card_set = set()
for cards in ABILITY_CARD_LIST:
    cardLocationNameString: str = get_card_location_name_str(cards, True)
    location_table[cardLocationNameString] = location_id_offset
    location_id_to_name[location_id_offset] = cardLocationNameString
    location_cards_id_to_card_string_id[location_id_offset] = cards
    location_id_offset += 1
    dex_card_set.add(cardLocationNameString)
location_groups.update({CARD_DEX_NAME: dex_card_set})

# Music Room locations.
music_room_set = set()
for track_id in MUSIC_ROOM_NAME_DICT.keys():
    musicLocationNameString: str = get_music_location_name_str(track_id)
    location_table[musicLocationNameString] = location_id_offset
    location_id_to_name[location_id_offset] = musicLocationNameString
    location_id_offset += 1
    music_room_set.add(musicLocationNameString)
location_groups.update({MUSIC_ROOM_UNLOCK_STR: music_room_set})

# Achievement locations.
achievement_set = set()
for achieve_id in ACHIEVE_NAME_DICT.keys():
    achieveLocationNameString: str = get_achievement_location_name_str(achieve_id)
    location_table[achieveLocationNameString] = location_id_offset
    location_id_to_name[location_id_offset] = achieveLocationNameString
    location_id_offset += 1
    achievement_set.add(achieveLocationNameString)
location_groups.update({"Achievements": achievement_set})


def get_location_names_with_ids(location_names: list[str]) -> dict[str, int | None]:
    return {location_name: location_table[location_name] for location_name in location_names}


def create_regular_locations(world):
    all_regions_dict = get_regions_dict(world)

    # Stages Tutorial-Challenge
    for region_name in all_regions_dict.keys():
        # Boss Encounters and Defeats
        if region_name in STAGE_LIST:
            local_stage_id = STAGE_NAME_TO_ID[region_name]
            if region_name != CHALLENGE_NAME:
                for boss_name in ALL_BOSSES_LIST[local_stage_id]:
                    locationEncounter: str = get_boss_location_name_str(local_stage_id, boss_name)
                    locationDefeat: str = get_boss_location_name_str(local_stage_id, boss_name, True)

                    boss_encounter_location = TouhouHBMLocation(
                        world.player,
                        locationEncounter,
                        world.location_name_to_id[locationEncounter],
                        all_regions_dict[region_name]
                    )
                    boss_defeat_location = TouhouHBMLocation(
                        world.player,
                        locationDefeat,
                        world.location_name_to_id[locationDefeat],
                        all_regions_dict[region_name]
                    )

                    all_regions_dict[region_name].locations.append(boss_encounter_location)
                    all_regions_dict[region_name].locations.append(boss_defeat_location)
            else:
                boss_challenge_list = get_boss_names_challenge_list()
                for challenge_boss in boss_challenge_list:
                    locationEncounter: str = get_boss_location_name_str(STAGE_CHALLENGE_ID, challenge_boss)

                    boss_encounter_location = TouhouHBMLocation(
                        world.player,
                        locationEncounter,
                        world.location_name_to_id[locationEncounter],
                        all_regions_dict[CHALLENGE_NAME]
                    )

                    all_regions_dict[CHALLENGE_NAME].locations.append(boss_encounter_location)
        # Ability Card as Market Card Rewards
        elif region_name == ENDSTAGE_CHOOSE_NAME:
            for stage_card in ABILITY_CARD_LIST:
                if stage_card in ABILITY_CARD_CANNOT_EQUIP or stage_card == MALLET_CARD: continue
                card_shop_location_name: str = get_card_location_name_str(stage_card, False)

                card_shop_location = TouhouHBMLocation(
                    world.player,
                    card_shop_location_name,
                    world.location_name_to_id[card_shop_location_name],
                    all_regions_dict[region_name]
                )

                all_regions_dict[region_name].locations.append(card_shop_location)
        # Ability Cards as Card Dex Unlocks
        elif region_name == CARD_DEX_NAME:
            for dex_card in ABILITY_CARD_LIST:
                card_dex_location_name: str = get_card_location_name_str(dex_card, True)

                card_dex_location = TouhouHBMLocation(
                    world.player,
                    card_dex_location_name,
                    world.location_name_to_id[card_dex_location_name],
                    all_regions_dict[region_name]
                )

                all_regions_dict[region_name].locations.append(card_dex_location)
        # Music Room and Achievements.
        # Both share the origin region.
        elif region_name == world.origin_region_name:
            # Music Room comes first.
            if world.options.music_room_checks:
                for track_index in MUSIC_ROOM_NAME_DICT.keys():
                    music_location_name: str = get_music_location_name_str(track_index)

                    music_location = TouhouHBMLocation(
                        world.player,
                        music_location_name,
                        world.location_name_to_id[music_location_name],
                        all_regions_dict[region_name]
                    )

                    all_regions_dict[region_name].locations.append(music_location)

            # Achievements come after.
            if world.options.achievement_checks:
                for achieve_index in ACHIEVE_NAME_DICT.keys():
                    achievement_location_name: str = get_achievement_location_name_str(achieve_index)

                    achievement_location = TouhouHBMLocation(
                        world.player,
                        achievement_location_name,
                        world.location_name_to_id[achievement_location_name],
                        all_regions_dict[region_name]
                    )

                    all_regions_dict[region_name].locations.append(achievement_location)