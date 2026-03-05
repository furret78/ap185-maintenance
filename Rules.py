from unittest import case

from BaseClasses import CollectionState
from worlds.generic.Rules import add_rule, set_rule
from .Tools import get_progress_item_requirement, get_boss_location_name_str, get_card_location_name_str, \
    get_music_location_name_str, get_achievement_location_name_str
from .variables.card_const import *
from .variables.music_and_achiev import MUSIC_ROOM_NAME_DICT, ACHIEVE_NAME_DICT


def set_all_rules(world) -> None:
    set_all_entrance_rules(world)
    set_all_location_rules(world)
    set_goal_condition(world)


def get_card_shop_item_names() -> list[str]:
    # Go through both lists and fetch the card names.
    # Nazrin's cards never show up in shop.
    shop_card_item_names = []
    for card_string_id in ABILITY_CARD_LIST:
        if card_string_id == NAZRIN_CARD_1 or card_string_id == NAZRIN_CARD_2: continue
        shop_card_item_names.append(CARD_ID_TO_NAME[card_string_id])
    return shop_card_item_names


def set_all_entrance_rules(world) -> None:
    def has_correct_stage_item(state: CollectionState, given_stage: str) -> bool:
        if world.options.progressive_stages:
            progress_requirement_count = get_progress_item_requirement(given_stage, True)
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, progress_requirement_count)
        else:
            return state.has(given_stage, world.player)

    origin_to_region_dict = {
        TUTORIAL_NAME_FULL: world.get_entrance(ORIGIN_TO_TUTORIAL_NAME),
        STAGE1_NAME_FULL: world.get_entrance(ORIGIN_TO_STAGE1_NAME),
        STAGE2_NAME_FULL: world.get_entrance(ORIGIN_TO_STAGE2_NAME),
        STAGE3_NAME_FULL: world.get_entrance(ORIGIN_TO_STAGE3_NAME),
        STAGE4_NAME_FULL: world.get_entrance(ORIGIN_TO_STAGE4_NAME),
        STAGE5_NAME_FULL: world.get_entrance(ORIGIN_TO_STAGE5_NAME),
        STAGE6_NAME_FULL: world.get_entrance(ORIGIN_TO_STAGE6_NAME),
        ENDSTAGE_NAME_FULL: world.get_entrance(ORIGIN_TO_CHIMATA_NAME),
        CHALLENGE_NAME_FULL: world.get_entrance(ORIGIN_TO_CHALLENGE_NAME)
    }

    for stage_name in origin_to_region_dict.keys():
        set_rule(origin_to_region_dict[stage_name], lambda state, used_name=stage_name: has_correct_stage_item(state, used_name))


def set_all_location_rules(world) -> None:
    # Helper CollectionStates specifically for conditions that just require stage access.

    # Tutorial stage has 5 exclusive cards.
    def has_tutorial_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player)
        else:
            return state.has(TUTORIAL_NAME_FULL, world.player)

    def has_challenge_access_item(state: CollectionState, is_boss: bool = False) -> bool:
        """
        Checks for Challenge Market access.
        If generation has turned off Challenge Market in logic (disable_challenge_logic == true),
        this will always return False.
        If doing Progressive Stages, also return False.
        """
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(CHALLENGE_NAME)) and low_skill_rules(state)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(CHALLENGE_NAME))
        if world.options.disable_challenge_logic and not is_boss: return False
        else:
            # Challenge Market is also lategame.
            if world.options.low_skill_logic:
                return state.has(CHALLENGE_NAME_FULL, world.player) and low_skill_rules(state)
            else:
                return state.has(CHALLENGE_NAME_FULL, world.player)

    # For specific stages (excludes Challenge Market by default).
    def has_stage_access_item(state: CollectionState, short_stage_name: str) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(short_stage_name))
        else:
            return state.has(STAGE_SHORT_TO_FULL_NAME[short_stage_name], world.player)

    def has_stage_list_access_item(state: CollectionState, stage_name_list: list[str], achieve_check: bool = False) -> bool:
        """
        Checks for whether the player would have any of the stages available.
        When checking for Progressive Market requirements, this will always take the first name on the list.
        Challenge Market-related checks have their own separate condition.

        :param state: CollectionState. Just pass the one from the lambda in.
        :param stage_name_list: The full names of the stages.
        """
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(stage_name_list[0], True))
        else:
            if achieve_check: return state.has_all(stage_name_list, world.player)
            else: return state.has_any(stage_name_list, world.player)

    def has_any_stage_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player)

        non_challenge_stages = STAGE_NAME_LIST
        if CHALLENGE_NAME_FULL in non_challenge_stages:
            non_challenge_stages.remove(CHALLENGE_NAME_FULL)
        return state.has_any(non_challenge_stages, world.player) or has_challenge_access_item(state)

    # For more open reward pools. Of course, these all imply Challenge Market clauses as well.
    # Common. Shows up in every stage except Tutorial.
    def has_common_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE1_NAME))

        non_challenge_stages = STAGE_NAME_LIST
        if TUTORIAL_NAME_FULL in non_challenge_stages:
            non_challenge_stages.remove(TUTORIAL_NAME_FULL)
        if CHALLENGE_NAME_FULL in non_challenge_stages:
            non_challenge_stages.remove(CHALLENGE_NAME_FULL)
        return state.has_any(non_challenge_stages, world.player) or has_challenge_access_item(state)

    # Very early game (Stage 1+). Does not show up in Stage 5 or End of Market.
    def has_very_early_game_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE1_NAME))

        return has_early_game_access_item(state) or state.has(STAGE1_NAME_FULL, world.player)

    # Early game (Stage 2+). Does not show up in Stage 5 or End of Market.
    def has_early_game_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE2_NAME))

        return has_midgame_access_item(state) or state.has(STAGE2_NAME_FULL, world.player)

    # Midgame (Stage 3+). Does not show up in Stage 5 or End of Market.
    def has_midgame_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE3_NAME))

        return (state.has_any((STAGE3_NAME_FULL, STAGE4_NAME_FULL, STAGE6_NAME_FULL), world.player)
                or has_challenge_access_item(state))

    # Lategame (Stage 4+). Does not show up in End of Market.
    # Low Skill Logic forces the generation to include certain Ability Cards as compulsory.
    def has_lategame_access_item(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE4_NAME)) and low_skill_rules(state)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE4_NAME))

        if world.options.low_skill_logic:
            return ((state.has_any((STAGE4_NAME_FULL, STAGE5_NAME_FULL, STAGE6_NAME_FULL), world.player)
                     and low_skill_rules(state)) or has_challenge_access_item(state))
        else:
            return (state.has_any((STAGE4_NAME_FULL, STAGE5_NAME_FULL, STAGE6_NAME_FULL), world.player)
                    or has_challenge_access_item(state))

    def low_skill_rules(state: CollectionState) -> bool:
        return state.has_all(LOW_SKILL_CARD_LIST, world.player)

    # Special access rules.
    def has_nitori_access(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE4_NAME)) and state.has(BLANK_CARD_NAME, world.player) and low_skill_rules(state)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE4_NAME)) and state.has(BLANK_CARD_NAME, world.player)

        if world.options.low_skill_logic:
            return state.has_all((STAGE4_NAME_FULL, BLANK_CARD_NAME), world.player) and low_skill_rules(state)
        else:
            return state.has_all((STAGE4_NAME_FULL, BLANK_CARD_NAME), world.player)

    def has_takane_access(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE6_NAME)) and state.has(NITORI_STORY_CARD_NAME, world.player) and low_skill_rules(state)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE6_NAME)) and state.has(NITORI_STORY_CARD_NAME, world.player)

        if world.options.low_skill_logic:
            return state.has_all((STAGE6_NAME_FULL, NITORI_STORY_CARD_NAME), world.player) and low_skill_rules(state)
        else:
            return state.has_all((STAGE6_NAME_FULL, NITORI_STORY_CARD_NAME), world.player)

    def has_sekibanki_access(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE2_NAME))

        return state.has_any((STAGE2_NAME_FULL, ENDSTAGE_NAME_FULL), world.player) or has_challenge_access_item(state)

    # Lily White's and Doremy's cards are a little more open.
    def has_lily_white_access(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE1_NAME))

        if world.options.low_skill_logic:
            return has_very_early_game_access_item(state) or (has_stage_access_item(state, STAGE5_NAME) and low_skill_rules(state)) or has_challenge_access_item(state)
        else:
            return has_very_early_game_access_item(state) or has_stage_access_item(state, STAGE5_NAME) or has_challenge_access_item(state)

    def has_doremy_access(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE2_NAME))

        if world.options.low_skill_logic:
            return has_early_game_access_item(state) or (has_stage_access_item(state, STAGE5_NAME) and low_skill_rules(state)) or has_challenge_access_item(state)
        else:
            return has_early_game_access_item(state) or has_stage_access_item(state, STAGE5_NAME) or has_challenge_access_item(state)

    def has_nazrin2_access(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has(PROGRESS_ITEM_NAME_FULL, world.player)

        black_market_stages = STAGE_NAME_LIST
        if ENDSTAGE_NAME_FULL in black_market_stages:
            black_market_stages.remove(ENDSTAGE_NAME_FULL)
        if CHALLENGE_NAME_FULL in black_market_stages:
            black_market_stages.remove(CHALLENGE_NAME_FULL)
        return state.has_any(black_market_stages, world.player) or has_challenge_access_item(state)

    def all_bosses_access(state: CollectionState) -> bool:
        """
        Checks if the player can access all bosses outside of Challenge Market.
        This accounts for not only all stage unlocks but also the two special cards.
        """
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(ENDSTAGE_NAME)) and state.has_all((BLANK_CARD_NAME, NITORI_STORY_CARD_NAME), world.player) and low_skill_rules(state)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(ENDSTAGE_NAME)) and state.has_all((BLANK_CARD_NAME, NITORI_STORY_CARD_NAME), world.player)

        if world.options.low_skill_logic:
            return state.has_all(
                (TUTORIAL_NAME_FULL, STAGE1_NAME_FULL, STAGE2_NAME_FULL, STAGE3_NAME_FULL, STAGE4_NAME_FULL,
                 STAGE5_NAME_FULL, STAGE6_NAME_FULL, ENDSTAGE_NAME_FULL, NITORI_STORY_CARD_NAME, BLANK_CARD_NAME),
                world.player) and low_skill_rules(state)
        else:
            return state.has_all(
                (TUTORIAL_NAME_FULL, STAGE1_NAME_FULL, STAGE2_NAME_FULL, STAGE3_NAME_FULL, STAGE4_NAME_FULL,
                 STAGE5_NAME_FULL, STAGE6_NAME_FULL, ENDSTAGE_NAME_FULL, NITORI_STORY_CARD_NAME, BLANK_CARD_NAME),
                world.player)

    def all_cards_access(state: CollectionState) -> bool:
        return state.has_all(get_card_shop_item_names(), world.player)

    # Access rules for the Ability Card dex entries.
    # Ensures that the player has a way to grind for Funds + the card in the Permanent Card Shop.
    # This will fail if this is a solo game and the player chooses to start with no Markets unlocked.
    # (Hopefully)
    def has_grind_access(state: CollectionState, the_card_id: str) -> bool:
        return state.has(CARD_ID_TO_NAME[the_card_id], world.player) and has_any_stage_access_item(state)

    def add_generic_access_card_rule(card_name_id: str, access_level: int):
        generic_location_card_name: str = get_card_location_name_str(card_name_id, False)
        generic_location_card = world.get_location(generic_location_card_name)

        match access_level:
            case 0:  # Common access.
                add_rule(generic_location_card, lambda state: has_common_access_item(state))
            case 1:  # Stage 1+
                add_rule(generic_location_card, lambda state: has_very_early_game_access_item(state))
            case 2:  # Stage 2+
                add_rule(generic_location_card, lambda state: has_early_game_access_item(state))
            case 3:  # Stage 3+
                add_rule(generic_location_card, lambda state: has_midgame_access_item(state))
            case 4:  # Lategame
                add_rule(generic_location_card, lambda state: has_lategame_access_item(state))
            case _:
                pass

    #
    # Location rules for bosses here.
    #
    # Normal stages and story bosses.
    for stage_short_name in STAGE_LIST:
        stage_id_from_list = STAGE_NAME_TO_ID[stage_short_name]
        if stage_short_name != CHALLENGE_NAME:
            for boss_name in ALL_BOSSES_LIST[stage_id_from_list]:
                location_encounter = world.get_location(get_boss_location_name_str(stage_id_from_list, boss_name))
                location_defeat = world.get_location(get_boss_location_name_str(stage_id_from_list, boss_name))

                # Check if it's Nitori or Takane
                if boss_name == BOSS_NITORI_NAME:
                    add_rule(location_encounter, lambda state: has_nitori_access(state))
                    add_rule(location_defeat, lambda state: has_nitori_access(state))
                    continue
                elif boss_name == BOSS_TAKANE_NAME:
                    add_rule(location_encounter, lambda state: has_takane_access(state))
                    add_rule(location_defeat, lambda state: has_takane_access(state))
                    continue

                # If it's none of them
                add_rule(location_encounter, lambda state, the_name = stage_short_name: has_stage_access_item(state, the_name))
                add_rule(location_defeat, lambda state, the_name = stage_short_name: has_stage_access_item(state, the_name))
        # Challenge Market Encounter clause.
        else:
            internal_stage_id = 0
            for challenge_boss_set in ALL_BOSSES_LIST:
                if TUTORIAL_ID < internal_stage_id < STAGE_CHIMATA_ID:
                    for challenge_boss_name in challenge_boss_set:
                        # If it's Nitori or Takane, do not set rules.
                        if challenge_boss_name == BOSS_NITORI_NAME or challenge_boss_name == BOSS_TAKANE_NAME:
                            continue

                        location_encounter = get_boss_location_name_str(STAGE_CHALLENGE_ID, challenge_boss_name)
                        add_rule(world.get_location(location_encounter), lambda state: has_challenge_access_item(state, True))
                internal_stage_id += 1

    #
    # Location rules for Ability Cards as stage rewards here.
    #
    # Tutorial has 5 cards only obtainable there.
    # Challenge Market has every single card in the game except for the 5 in Tutorial.
    # Boss exclusive cards first.
    for card_string_id in ABILITY_CARD_LIST:
        # Skip over Nazrin's cards and the Mallet card.
        if card_string_id in ABILITY_CARD_CANNOT_EQUIP: continue
        if card_string_id == MALLET_CARD: continue
        # Card exclusivity check.
        was_exclusive_card: bool = False

        for stage_name, card_set in STAGE_EXCLUSIVE_CARD_LIST.items():
            for card_id in card_set:
                if card_string_id != card_id: continue
                name_card_reward: str = get_card_location_name_str(card_string_id, False)
                location_card_reward = world.get_location(name_card_reward)

                # Tutorial stage has 5 exclusive cards not seen in Challenge Market.
                if stage_name == TUTORIAL_NAME:
                    add_rule(location_card_reward, lambda state: has_tutorial_access_item(state))
                    was_exclusive_card = True
                    continue
                # Capitalist's Dilemma requires Blank Card and 4th Market unlock.
                if card_string_id == NITORI_STORY_CARD:
                    add_rule(location_card_reward,
                             lambda state: has_nitori_access(state) or has_challenge_access_item(state))
                # Hundredth Black Market requires Capitalist's Dilemma and 6th Market unlock.
                elif card_string_id == TAKANE_STORY_CARD:
                    add_rule(location_card_reward,
                             lambda state: has_takane_access(state) or has_challenge_access_item(state))
                # Freewheeling Severed Head somehow shows up in End of Market.
                elif card_string_id == SEKIBANKI_CARD:
                    add_rule(location_card_reward, lambda state: has_sekibanki_access(state))
                # Generic conditions otherwise.
                else:
                    add_rule(location_card_reward, lambda state, the_name = stage_name: has_stage_access_item(state, the_name))

                was_exclusive_card = True

        if was_exclusive_card: continue

        # If it gets here, that means the card in question is not exclusive.
        # Check for Item Season and Sheep You Want to Count first.
        if card_string_id == LILY_WHITE_CARD:
            lily_location_name: str = get_card_location_name_str(LILY_WHITE_CARD, False)
            lily_location = world.get_location(lily_location_name)
            add_rule(lily_location, lambda state: has_lily_white_access(state))
            continue
        if card_string_id == DOREMY_CARD:
            doremy_location_name: str = get_card_location_name_str(DOREMY_CARD, False)
            doremy_location = world.get_location(doremy_location_name)
            add_rule(doremy_location, lambda state: has_doremy_access(state))
            continue

        # If it's not those two, then it belongs in a card tier.
        if card_string_id in STAGE_COMMON_CARD_LIST:
            add_generic_access_card_rule(card_string_id, 0)
            continue
        if card_string_id in STAGE1_CARD_LIST:
            add_generic_access_card_rule(card_string_id, 1)
            continue
        if card_string_id in STAGE2_CARD_LIST:
            add_generic_access_card_rule(card_string_id, 2)
            continue
        if card_string_id in STAGE3_CARD_LIST:
            add_generic_access_card_rule(card_string_id, 3)
            continue
        if card_string_id in LATEGAME_CARD_LIST:
            add_generic_access_card_rule(card_string_id, 4)
            continue

    #
    # Location rules for Ability Card dex entries here.
    #
    # Nazrin's cards don't have rules for unlocking. Practically every stage has it.
    nazrin_card1_location = world.get_location(get_card_location_name_str(NAZRIN_CARD_1, True))
    add_rule(nazrin_card1_location, lambda state: has_any_stage_access_item(state))
    nazrin_card2_location = world.get_location(get_card_location_name_str(NAZRIN_CARD_2, True))
    add_rule(nazrin_card2_location, lambda state: has_nazrin2_access(state))
    # The rest are only available if their respective item is available in the shop.
    for card_string_id in ABILITY_CARD_LIST:
        # Skip Nazrin's cards.
        if card_string_id in ABILITY_CARD_CANNOT_EQUIP: continue

        card_dex_location = world.get_location(get_card_location_name_str(card_string_id, True))
        add_rule(card_dex_location, lambda state, the_card_name = card_string_id: has_grind_access(state, the_card_name))

    #
    # Location rules for Music Room tracks here.
    #
    # Each track pretty much plays under different conditions. Not much of a way to classify them.
    # Check if their checks are enabled first.
    if world.options.music_room_checks:
        for track_id in MUSIC_ROOM_NAME_DICT.keys():
            music_track_location = world.get_location(get_music_location_name_str(track_id))

            match track_id:
                case 1: # An Exciting and Familiar Gensokyo
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [STAGE1_NAME_FULL, STAGE2_NAME_FULL]) or has_challenge_access_item(state))
                case 2: # Youkai Hook On
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [TUTORIAL_NAME_FULL, STAGE1_NAME_FULL, STAGE2_NAME_FULL, STAGE3_NAME_FULL]) or has_challenge_access_item(state))
                case 3: # Black Markets Can Happen Anywhere, Anytime
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [STAGE3_NAME_FULL, STAGE4_NAME_FULL]) or has_challenge_access_item(state))
                case 4: # Take Thy Danmaku In Hand, O Bulletphiles
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [STAGE4_NAME_FULL, STAGE5_NAME_FULL, STAGE6_NAME_FULL]) or has_challenge_access_item(state))
                case 5: # The 100th Black Market
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [STAGE5_NAME_FULL, STAGE6_NAME_FULL]) or has_challenge_access_item(state))
                case 6: # Lunatic Dreamer
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [TUTORIAL_NAME_FULL]))
                case 7: # Lunar Rainbow
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [TUTORIAL_NAME_FULL, ENDSTAGE_NAME_FULL]))
                case 8: # Where Is That Bustling Marketplace Now ~ Immemorial Marketeers
                    add_rule(music_track_location, lambda state: has_stage_list_access_item(state, [ENDSTAGE_NAME_FULL]))
                case 9: # A Rainbow-Colored World
                    add_rule(music_track_location, lambda state: has_takane_access(state))
                case _: continue

    #
    # Location rules for Achievements here.
    #
    # Each achievement has different conditions.
    # Check if their checks are enabled first.
    if world.options.achievement_checks:
        for achieve_id in ACHIEVE_NAME_DICT.keys():
            achievement_name_location = world.get_location(get_achievement_location_name_str(achieve_id))

            match achieve_id:
                case 0: # Clear the game.
                    add_rule(achievement_name_location, lambda state: has_takane_access(state))
                case 1: # Defeat all Stage 1 bosses.
                    add_rule(achievement_name_location, lambda state: has_stage_access_item(state, STAGE1_NAME))
                case 2: # Stage 2 bosses.
                    add_rule(achievement_name_location, lambda state: has_stage_access_item(state, STAGE2_NAME))
                case 3: # etc.
                    add_rule(achievement_name_location, lambda state: has_stage_access_item(state, STAGE3_NAME))
                case 4: # Needs Blank Card as well.
                    add_rule(achievement_name_location, lambda state: has_nitori_access(state))
                case 5:
                    add_rule(achievement_name_location, lambda state: has_stage_access_item(state, STAGE5_NAME))
                case 6: # Needs Capitalist's Dilemma as well.
                    add_rule(achievement_name_location, lambda state: has_takane_access(state))
                case 7: # Defeat Chimata.
                    add_rule(achievement_name_location, lambda state: has_stage_access_item(state, ENDSTAGE_NAME))
                case 8: # Defeat all bosses. Basically Full Story Clear with all stages.
                    add_rule(achievement_name_location, lambda state: all_bosses_access(state))
                case 9: # Clear Challenge Market.
                    add_rule(achievement_name_location, lambda state: has_challenge_access_item(state, True))
                case 10: # All equipment slots. 4th Market is where this can be achieved minimally.
                    add_rule(achievement_name_location, lambda state: has_stage_list_access_item(state, [TUTORIAL_NAME_FULL, STAGE1_NAME_FULL, STAGE2_NAME_FULL, STAGE3_NAME_FULL, STAGE4_NAME_FULL], True))
                case 11: # All cards collected. Item-dependent.
                    add_rule(achievement_name_location, lambda state: all_cards_access(state))


def set_goal_condition(world) -> None:
    def minimum_story_clear(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE6_NAME)) and state.has_all([NITORI_STORY_CARD_NAME] + LOW_SKILL_CARD_LIST, world.player)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(STAGE6_NAME)) and state.has(NITORI_STORY_CARD_NAME, world.player)

        if world.options.low_skill_logic:
            return state.has_all((NITORI_STORY_CARD_NAME, STAGE6_NAME_FULL), world.player) and state.has_all(LOW_SKILL_CARD_LIST, world.player)
        else:
            return state.has_all((NITORI_STORY_CARD_NAME, STAGE6_NAME_FULL), world.player)

    def full_story_clear(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            if world.options.low_skill_logic:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(ENDSTAGE_NAME)) and state.has_all(([NITORI_STORY_CARD_NAME, BLANK_CARD_NAME] + LOW_SKILL_CARD_LIST), world.player)
            else:
                return state.has(PROGRESS_ITEM_NAME_FULL, world.player, get_progress_item_requirement(ENDSTAGE_NAME)) and state.has_all((NITORI_STORY_CARD_NAME, BLANK_CARD_NAME), world.player)

        if world.options.low_skill_logic:
            return state.has_all(
                (NITORI_STORY_CARD_NAME, BLANK_CARD_NAME, STAGE4_NAME_FULL, STAGE6_NAME_FULL, ENDSTAGE_NAME_FULL),
                world.player) and state.has_all(LOW_SKILL_CARD_LIST, world.player)
        else:
            return state.has_all(
            (NITORI_STORY_CARD_NAME, BLANK_CARD_NAME, STAGE4_NAME_FULL, STAGE6_NAME_FULL, ENDSTAGE_NAME_FULL),
            world.player)

    # Since this checks for items, and full stage names are used as items, use that.
    def all_cards_clear(state: CollectionState) -> bool:
        return state.has_all(get_card_shop_item_names(), world.player)

    # To defeat all bosses, you need all stages to be available except the Challenge Market.
    # Both instances of Mike Goutokuji are counted.
    boss_condition_list = STAGE_NAME_LIST
    if CHALLENGE_NAME_FULL in boss_condition_list: boss_condition_list.remove(CHALLENGE_NAME_FULL)

    def all_bosses_clear(state: CollectionState) -> bool:
        # If Progressive Stages is enabled, this is just straight up Full Story Clear conditions.
        if world.options.progressive_stages:
            return full_story_clear(state)

        if world.options.low_skill_logic:
            return state.has_all((boss_condition_list + LOW_SKILL_CARD_LIST + [NITORI_STORY_CARD_NAME, BLANK_CARD_NAME]), world.player)
        else:
            return state.has_all((boss_condition_list + [NITORI_STORY_CARD_NAME, BLANK_CARD_NAME]), world.player)

    def full_clear_rule(state: CollectionState) -> bool:
        if world.options.progressive_stages:
            return state.has_all((get_card_shop_item_names()), world.player) and full_story_clear(state)

        return state.has_all((get_card_shop_item_names() + boss_condition_list), world.player)

    match world.options.completion_type:
        # Minimum Story Clear
        case 1:
            world.multiworld.completion_condition[world.player] = lambda state: minimum_story_clear(state)
        # All Cards
        case 2:
            world.multiworld.completion_condition[world.player] = lambda state: all_cards_clear(state)
        # All Bosses
        case 3:
            world.multiworld.completion_condition[world.player] = lambda state: all_bosses_clear(state)
        # Full Clear
        case 4:
            world.multiworld.completion_condition[world.player] = lambda state: full_clear_rule(state)
        # Full Story Clear/Default
        case _:
            world.multiworld.completion_condition[world.player] = lambda state: full_story_clear(state)