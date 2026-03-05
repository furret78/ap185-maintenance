import os
import pkgutil
import random
import traceback
import typing
from typing import Optional
import asyncio
import colorama
import orjson

from CommonClient import (
    CommonContext,
    ClientCommandProcessor,
    get_base_parser,
    logger,
    server_loop,
    gui_enabled,
)
from NetUtils import NetworkItem
from .GameHandler import *
from .Items import GAME_ONLY_ITEM_ID, item_table, ITEM_TABLE_ID_TO_STAGE_NAME, ITEM_TABLE_ID_TO_CARD_ID
from .Locations import *
from .variables.meta_data import *
from .Tools import get_item_index_save_name, convert_currency_to_joules, get_energy_withdraw_tag, \
    convert_joules_to_currency, get_boss_location_name_str, get_card_location_name_str
from .variables.music_and_achiev import MUSIC_ROOM_UNLOCK_STR, ACHIEVE_UNLOCK_STR


# Handles the game itself. The watcher that runs loops is down below.

def copy_and_replace(directory: str):
    ap_scorefile_data = pkgutil.get_data("worlds.th185", "scorefile/scoreth185.dat")
    if ap_scorefile_data is None:
        logger.error("The Client could not find its own save data!")
        return

    # The actual scorefile used by the game.
    full_file_path = os.path.join(directory, os.path.basename(SCOREFILE_NAME))
    if os.path.exists(full_file_path):
        os.remove(full_file_path)
    with open(full_file_path, "wb") as binary_file:
        binary_file.write(ap_scorefile_data)

    # Remove the backup scorefile in there since it interferes with Archipelago functionality.
    backup_file_path = os.path.join(directory, os.path.basename(SCOREFILE_BACKUP_NAME))
    if os.path.exists(backup_file_path):
        os.remove(backup_file_path)

    logger.info(f"Successfully replaced save data at: {full_file_path}")

def get_currency_type_from_str(currency_type_string: str, game_context) -> int:
    if currency_type_string in CURRENCY_FUNDS_ARGS_LIST:
        return CURRENCY_FUNDS_ID
    elif currency_type_string in CURRENCY_BULLET_MONEY_ARGS_LIST:
        if not game_context.energylink_bulletmoney_enabled:
            logger.info("Bullet Money exchanges are not enabled for this slot.")
            return -1
        return CURRENCY_BULLET_MONEY_ID
    else:
        logger.info(INVALID_CURRENCY_STRING)
        return -1

def get_random_death_message(lost_final_life: bool = False) -> str:
    if lost_final_life: return random.choice(DEATH_LINK_STAGE_MSGS)
    else: return random.choice(DEATH_LINK_LIFE_MSGS + DEATH_LINK_GENERIC_MSGS)


class TouhouHBMClientProcessor(ClientCommandProcessor):
    def __init__(self, ctx):
        super().__init__(ctx)

    def _cmd_relink_game(self):
        """
        Internally forces the client to enter Error state in order to restart link to the game.
        """
        self.ctx.inError = True

    def _cmd_show_funds(self):
        """
        Retrieves the number of Funds in the menu.
        """
        if not self.ctx.handler or not self.ctx.handler.gameController:
            logger.error(GAME_NOT_RUNNING_MSG)
            return

        funds_count = self.ctx.handler.gameController.getMenuFunds()
        logger.info(f"Current Funds: {funds_count}")

    def _cmd_unlock_no_card(self):
        """
        Command to forcibly unlock the option to equip no cards in the loadout.
        """
        if not self.ctx.handler or not self.ctx.handler.gameController:
            logger.error(GAME_NOT_RUNNING_MSG)
            return

        self.ctx.handler.gameController.setNoCardData()

    def _cmd_energylink(self, interaction_type: str = None, amount = None, currency_type: str = None):
        """
        Command for executing interactions with the Energy Link pool.
        Leave all blank arguments to check if Energy Link is enabled.
        :param interaction_type: Deposit ("d"), withdraw ("w").
        :param amount: Amount of currency to perform the interaction on.
        :param currency_type: Funds ("f"), Bullet Money ("b").
        """
        if not self.ctx.is_connected:
            logger.info(SERVER_NOT_CONNECTED_MSG)
            return

        if not self.ctx.energylink_enabled:
            logger.info("Energy Link isn't enabled for this slot.")
            return
        elif interaction_type is None and amount is None and currency_type is None:
            logger.info("Energy Link available.")
            return

        if interaction_type is None:
            logger.info("Invalid Energy Link interaction type.")
            return
        if amount is None:
            logger.info("Amount to perform operation hasn't been specified yet!")
            return
        elif int(amount) <= 0:
            logger.info("Amount must be a positive integer!")
            return

        final_currency_type: int = get_currency_type_from_str(currency_type, self.ctx)
        if final_currency_type == -1:
            return

        if interaction_type in INTERACT_DEPOSIT_ARGS_LIST:
            asyncio.create_task(self.ctx.deposit_currency(int(amount), final_currency_type))
            return
        elif interaction_type in INTERACT_WITHDRAW_ARGS_LIST:
            asyncio.create_task(self.ctx.withdraw_currency(int(amount), final_currency_type))
            return
        else:
            logger.info("Invalid Energy Link interaction type.")

    def _cmd_deathlink(self):
        """
        Show Death Link status for this game.
        """
        if not self.ctx.is_connected:
            logger.info(SERVER_NOT_CONNECTED_MSG)
            return

        logger.info(f"Death Link status: {self.ctx.deathlink_enabled}")
        if not self.ctx.deathlink_enabled: return
        if self.ctx.deathlink_trigger == DEATH_LINK_TRIGGER_LIFE:
            logger.info(DEATH_LINK_INFO_LIFE)
        elif self.ctx.deathlink_trigger == DEATH_LINK_TRIGGER_STAGE:
            logger.info(DEATH_LINK_INFO_STAGE)

    def _cmd_deathlink_trigger(self, trigger: str = None):
        """
        Get or set when a Death Link is triggered. Leave blank to check status.
        :param trigger: Upon Life Loss ("life"), Upon Stage Fail ("stage").
        """
        if not self.ctx.is_connected:
            logger.info(SERVER_NOT_CONNECTED_MSG)
            return
        if not self.ctx.deathlink_enabled:
            logger.info(DEATH_LINK_NOT_ENABLED)
            return

        if trigger is None:
            if self.ctx.deathlink_trigger == DEATH_LINK_TRIGGER_LIFE:
                logger.info(DEATH_LINK_INFO_LIFE)
            elif self.ctx.deathlink_trigger == DEATH_LINK_TRIGGER_STAGE:
                logger.info(DEATH_LINK_INFO_STAGE)
            else:
                logger.info("Death Link condition unknown.")
            return
        else:
            if trigger == "life":
                self.ctx.deathlink_trigger = DEATH_LINK_TRIGGER_LIFE
                logger.info(DEATH_LINK_INFO_CHANGED + DEATH_LINK_INFO_LIFE)
            elif trigger == "stage":
                self.ctx.deathlink_trigger = DEATH_LINK_TRIGGER_STAGE
                logger.info(DEATH_LINK_INFO_CHANGED + DEATH_LINK_INFO_STAGE)
            else:
                logger.info("Invalid Death Link trigger arguments.")

    def _cmd_show_save_directory(self):
        """
        Show the current save data directory the client is using.
        """
        logger.info(f"Current save data directory: {self.ctx.scorefile_path}")

    def _cmd_set_save_directory(self, save_path: str = None):
        """
        Sets a new path to the save data directory.
        """

        if save_path is not None:
            self.ctx.scorefile_path = save_path
            logger.info(f"Save data directory was changed to: {self.ctx.scorefile_path}")
        else:
            default_appdata_path = os.getenv("APPDATA")
            if default_appdata_path is None:
                self.ctx.scorefile_path = None
            else:
                self.ctx.scorefile_path = default_appdata_path + APPDATA_PATH

            logger.info(f"Save data directory was reset to default.")

    def _cmd_replace_save(self):
        """
        Replaces the game's scoreth185.dat file and deletes the scoreth185bak.dat file.
        Recommended to manually back up save data before doing this.
        The game's save data is often located at %appdata%/ShanghaiAlice/th185.
        Recommended to run before launching the game itself.
        """
        copy_and_replace(self.ctx.scorefile_path)


class TouhouHBMContext(CommonContext):
    """Touhou 18.5 Game Context"""
    handler = None
    scorefile_path = ""

    def __init__(self, server_address: Optional[str], password: Optional[str]) -> None:
        super().__init__(server_address, password)
        self.item_ap_id_to_name = None
        self.item_name_to_ap_id = None
        self.location_ap_id_to_name = None
        self.options = None
        self.is_connected = None
        self.inError = None
        self.location_name_to_ap_id = None
        self.all_location_ids = []
        self.previous_location_checked = []
        self.game = DISPLAY_NAME
        self.items_handling = 0b111  # Item from starting inventory, own world and other world
        self.command_processor = TouhouHBMClientProcessor

        self.no_card_unlocked: bool = False
        self.loadingDataSetup: bool = True
        self.retrievedCustomData: bool = False

        # Scorefile path.
        default_appdata_path = os.getenv("APPDATA")
        if default_appdata_path is None:
            self.scorefile_path = None
        else:
            self.scorefile_path = default_appdata_path + APPDATA_PATH

        # Additional game data.
        # Funds as shown in the menu.
        # Should only be sent to the server when:
        # - A check for the Ability Card Dex was found.
        # - Exiting a stage.
        self.menuFunds: int = 0
        # Number of Ability Cards the player can equip at the start of a stage.
        self.loadout_slots: int = 1  # Max 7 in-game.
        # Equipment cost.
        self.equip_cost: int = 100  # Max 350% in-game.
        # This is for eye-candy. List contains the string IDs of cards marked as "New!" in the game.
        self.permashop_cards_new: list = []
        # List of Cards that are unlocked in Shop.
        # When connected to the server, the entire ReceivedItem package will be scanned
        # for any cards that are in there. Same with the list of unlocked stages.
        self.permashop_cards: list = []
        self.unlocked_stages: list = []
        self.progressive_stage_list: list[int] = []
        # Dex dictionary does not exist. Use the list of acquired checks for that.
        # Owning a card and unlocking its dex entry is one and the same,
        # but it is separate for the player.
        self.custom_data_keys_list: list = [str(self.team) + "_" + str(self.slot) + "Funds185",
                                            str(self.team) + "_" + str(self.slot) + "Slots185",
                                            str(self.team) + "_" + str(self.slot) + "EquipCost185",
                                            str(self.team) + "_" + str(self.slot) + "LastItem185"]

        # Set to True when scanning the card shop addresses as locations.
        # Set to False when in the menu.
        self.enable_card_selection_checking: bool = False
        # The opposite of the above.
        # Set to True when scanning the card shop addresses as items.
        # Set to False when in stages.
        self.enable_card_shop_scanning: bool = True

        self.receivedItemQueue: list[
            NetworkItem] = []  # All items freshly arrived. Will be filtered for wrong IDs as it's processed.
        self.menuItemQueue: list = []  # Items received but not yet executed because game is in a stage.
        self.gameItemQueue: list = []  # Items received but not yet executed because game is in the menu.
        # Note: Funds do not go in here, but they have separate functions to execute
        # depending on whether the game is in the menu or not instead.

        # Checks whether Menu funds and stuff has been loaded yet.
        self.menu_stats_initialized: bool = False

        # List of all received items from the server.
        self.all_received_items: list[int] = []
        self.loaded_past_received_items: bool = False
        self.last_received_item_index_server: int = -1

        # Whether the game is running or not.
        # Checks for whether it is the game itself or just the window resolution dialogue box.
        self.is_game_running: bool = False

        # DeathLink-related fields
        self.deathlink_enabled: bool = False
        self.pending_received_deathlink: bool = False
        self.pending_life_deduction: bool = False
        self.died_to_deathlink: bool = False
        self.caused_deathlink: bool = False
        self.deathlink_trigger: int = DEATH_LINK_TRIGGER_LIFE
        self.lost_final_life: bool = False
        self.last_recorded_life: int = 0

        # EnergyLink-related fields
        # self.menuFunds get repurposed here as it is not linked to DataStorage anymore.
        self.energylink_enabled: bool = False
        self.energylink_bulletmoney_enabled: bool = False

        # Item reception stuff. This gets resets within the same function they are used.
        self.received_funds: int = 0
        self.received_bullet_money: int = 0
        self.received_lives: int = 0
        self.received_shot_attack: int = 0
        self.received_circle_atk: int = 0
        self.received_circle_size: int = 0
        self.received_circle_duration: int = 0
        self.received_circle_graze: int = 0
        self.received_speed: int = 0
        self.received_invincibility: int = 0
        self.received_equip_cost: int = 0
        self.received_invinc_cancel: bool = False

        self.reset()

    def reset(self):
        self.previous_location_checked = []
        self.all_location_ids = []
        self.handler = None
        self.no_card_unlocked = False

        self.inError = False

        self.previous_location_checked = None
        self.is_connected = False
        self.loadingDataSetup = True

        self.menuFunds = 0
        self.loadout_slots = 1
        self.equip_cost = 100
        self.permashop_cards_new = []
        self.permashop_cards = []
        self.unlocked_stages = []
        self.progressive_stage_list = []

        self.enable_card_selection_checking = False
        self.enable_card_shop_scanning = True

        self.receivedItemQueue = []
        self.menuItemQueue = []
        self.gameItemQueue = []
        self.menu_stats_initialized = False
        self.is_game_running = False
        self.all_received_items = []
        self.loaded_past_received_items = False
        self.last_received_item_index_server = -1

        self.deathlink_enabled = False
        self.pending_received_deathlink = False
        self.pending_life_deduction = False
        self.died_to_deathlink = False
        self.caused_deathlink = False
        self.deathlink_trigger = DEATH_LINK_TRIGGER_LIFE
        self.last_recorded_life = 0
        self.lost_final_life = False
        self.last_death_link = 0

        self.energylink_enabled = False
        self.energylink_bulletmoney_enabled = False

        self.received_funds = 0
        self.received_bullet_money = 0
        self.received_lives = 0
        self.received_shot_attack = 0
        self.received_circle_atk = 0
        self.received_circle_size = 0
        self.received_circle_duration = 0
        self.received_circle_graze = 0
        self.received_speed = 0
        self.received_invincibility = 0
        self.received_equip_cost = 0
        self.received_invinc_cancel = False

        #self.reset_game_data()

    def reset_game_data(self):
        if not self.handler: return
        if not self.handler.gameController: return
        self.is_game_running = self.handler.gameController.check_if_in_game()
        # If the game isn't running, no need to do anything.
        if not self.is_game_running: return

        # If it is, reset all stats immediately.
        # 1. Clear all boss records.
        def reset_boss_records():
            for stage_name in STAGE_LIST:
                if stage_name != CHALLENGE_NAME:
                    for boss_name in ALL_BOSSES_LIST[STAGE_NAME_TO_ID[stage_name]]:
                        # Get the location name first, convert that to ID,
                        # and then append if it is not in previously checked locations.
                        # Encounters
                        self.handler.setBossRecordGame(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name], False,
                                                       ENCOUNTER_ID)
                        self.handler.setBossRecordGame(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name], False,
                                                       DEFEAT_ID)
                else:
                    # Special Challenge Market clause
                    boss_set_id_loc = 1
                    for boss_set in ALL_BOSSES_LIST:
                        # If it's the Tutorial set or End of Market set, discard those.
                        if TUTORIAL_ID <= boss_set_id_loc >= STAGE_CHIMATA_ID: continue
                        for boss_name in boss_set:
                            # Make sure to exclude the story bosses.
                            if boss_name in STORY_BOSSES_LIST: continue
                            # There are only encounters. Check those.
                            self.handler.setBossRecordGame(STAGE_CHALLENGE_ID, BOSS_NAME_TO_ID[boss_name], False,
                                                           ENCOUNTER_ID)

        reset_boss_records()

        # 2. Clear all stage unlock records.
        def reset_stage_unlocks():
            if len(self.handler.stages_unlocked) > 0:
                for i in self.handler.stages_unlocked.keys():
                    self.handler.stages_unlocked[i] = False
                self.update_stage_list()

        reset_stage_unlocks()

        # 3. Clear all menu records (Funds, card slots, equip cost).
        def reset_menu_records():
            self.handler.setMenuFunds(0)
            self.handler.setCardSlots(1)
            self.handler.setEquipCost(100)
            for song_id, song_name in MUSIC_ROOM_NAME_DICT.items():
                self.handler.setMusicRecord(song_id, False)
            for trophy_id, trophy_name in ACHIEVE_NAME_DICT.items():
                self.handler.setAchievementStatus(trophy_id, False)

        reset_menu_records()

        # 4. Clear all card dex records.
        def reset_card_dex():
            for card in ABILITY_CARD_LIST:
                self.handler.setDexCardData(card, False)

        reset_card_dex()

        # 5. Clear all card shop records.
        def reset_card_shop():
            for card in ABILITY_CARD_LIST:
                if card == NAZRIN_CARD_1 or card == NAZRIN_CARD_2: continue
                self.handler.setCardShopRecordGame(card, False)

        reset_card_shop()

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = f"{DISPLAY_NAME} Client"
        return ui

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        """
        Manage the package received from the server
        """
        if cmd == "RoomInfo":
            self.seed_name = args["seed_name"]

        if cmd == "Connected":
            self.previous_location_checked = args['checked_locations']
            self.all_location_ids = set(args["missing_locations"] + args["checked_locations"])
            self.options = args["slot_data"]  # Yaml Options
            self.is_connected = True
            self.slot = args["slot"]

            if self.handler is not None:
                self.handler.reset()

            asyncio.create_task(self.send_msgs([{"cmd": "GetDataPackage", "games": [DISPLAY_NAME]}]))

        if cmd == "ReceivedItems":
            asyncio.create_task(self.handle_received_items(args["index"], args["items"]))

        elif cmd == "Retrieved":  # Custom data
            # Menu Funds
            if self.custom_data_keys_list[0] in args["keys"] and not self.energylink_enabled:
                if args["keys"][self.custom_data_keys_list[0]] is not None:
                    self.menuFunds = args["keys"][self.custom_data_keys_list[0]]

            # Loadout Slots
            if self.custom_data_keys_list[1] in args["keys"]:
                if args["keys"][self.custom_data_keys_list[1]] is not None:
                    self.loadout_slots = clamp(args["keys"][self.custom_data_keys_list[1]], 1, 34)

            # Equip Cost
            if self.custom_data_keys_list[2] in args["keys"]:
                if args["keys"][self.custom_data_keys_list[2]] is not None:
                    self.equip_cost = args["keys"][self.custom_data_keys_list[2]]
                    if self.equip_cost < 100: self.equip_cost = 100

            # Last Saved Index
            if self.custom_data_keys_list[3] in args["keys"]:
                if args["keys"][self.custom_data_keys_list[3]] is not None:
                    self.last_received_item_index_server = args["keys"][self.custom_data_keys_list[3]]
                else:
                    self.last_received_item_index_server = 0

        elif cmd == "DataPackage":
            if not self.all_location_ids:
                # Connected package not received yet, wait for datapackage request after connected package
                return
            self.location_name_to_ap_id = args["data"]["games"][DISPLAY_NAME]["location_name_to_id"]
            self.location_name_to_ap_id = {
                name: loc_id for name, loc_id in
                self.location_name_to_ap_id.items() if loc_id in self.all_location_ids
            }
            self.location_ap_id_to_name = {v: k for k, v in self.location_name_to_ap_id.items()}
            self.item_name_to_ap_id = args["data"]["games"][DISPLAY_NAME]["item_name_to_id"]
            self.item_ap_id_to_name = {v: k for k, v in self.item_name_to_ap_id.items()}

        elif cmd == "Bounced":
            tags = args.get("tags", [])
            # Skip checking if DeathLink is in ctx.tags. Wouldn't have been sent this otherwise.
            if "DeathLink" in tags and self.last_death_link != args["data"]["time"]:
                self.last_death_link = args["data"]["time"]
                self.on_deathlink(args["data"])

        if cmd == "SetReply":
            if self.energylink_enabled:
                # Check if EnergyLink pool matches current team and slot.
                actual_withdrawn_amount = 0
                withdraw_currency_type = CURRENCY_FUNDS_ID

                if args["key"] == f"EnergyLink{self.team}" and args["slot"] == self.slot:
                    received_tag = args.get("tag", "")
                    currency_type: int
                    currency_name: str = CURRENCY_NAME_FUNDS

                    # Check if this SetReply concerns Funds or Bullet Money.
                    if received_tag == get_energy_withdraw_tag(self.seed_name, CURRENCY_FUNDS_ID):
                        currency_type = CURRENCY_FUNDS_ID
                        currency_name = CURRENCY_NAME_FUNDS
                    elif received_tag == get_energy_withdraw_tag(self.seed_name, CURRENCY_BULLET_MONEY_ID):
                        currency_type = CURRENCY_BULLET_MONEY_ID
                        currency_name = CURRENCY_NAME_BULLET_MONEY

                        # Check here if the player is not in a stage.
                        # If not, return the energy immediately.
                        if not self.checkIfGameInStage():
                            logger.info(BULLET_MONEY_CANNOT_WITHDRAW)
                            asyncio.create_task(self.send_direct_deposit_msg(args["original_value"] - args["value"]))
                            return

                    # If it's none of the above, the package is probably mangled.
                    else:
                        currency_type = -1
                        logger.info("SetReply package from the server is broken.")

                    if currency_type != -1:
                        actual_withdrawn_amount = convert_joules_to_currency(args["original_value"] - args["value"], currency_type)
                        withdraw_currency_type = currency_type
                    else: return

                    # If the converted amount rounds down to 0, immediately return the energy back to the server.
                    if actual_withdrawn_amount <= 0:
                        logger.info(f"Not enough energy for {currency_name}. Returned to the pool.")
                        asyncio.create_task(self.send_direct_deposit_msg(args["original_value"] - args["value"]))
                    else:
                        asyncio.create_task(self.process_received_currency(actual_withdrawn_amount, withdraw_currency_type))
                        self.current_energy_link_value = args["value"]

    def client_received_initial_server_data(self):
        """
        This method waits until the client finishes the initial conversation with the server.
        This means:
            - All LocationInfo packages received - requested only if patch files dont exist.
            - DataPackage package received (id_to_name maps and name_to_id maps are popualted)
            - Connection package received (slot number populated)
            - RoomInfo package received (seed name populated)
        """
        return self.is_connected

    #
    # More game helper functions
    #
    def update_stage_list(self):
        self.handler.updateStageList()

    def checkIfGameInStage(self):
        """
        Helper function that checks if the game is currently in a stage.
        This checks both whether the game is actually in a stage and whether it should scan for Market Card Rewards.
        If it is, return True.
        """
        return self.handler.isGameInStage() and self.enable_card_selection_checking

    #
    # Victory conditions
    #
    def checkVictory(self) -> bool:
        """
        Check if the player has won the game.
        """

        def checkMinimumStory() -> bool:
            return location_table[get_boss_location_name_str(STAGE6_ID, BOSS_TAKANE_NAME, True)] in self.previous_location_checked

        def checkFullStory() -> bool:
            if location_table[get_boss_location_name_str(STAGE4_ID, BOSS_NITORI_NAME,
                                          True)] not in self.previous_location_checked: return False
            if location_table[get_boss_location_name_str(STAGE_CHIMATA_ID, BOSS_CHIMATA_NAME,
                                          True)] not in self.previous_location_checked: return False
            if not checkMinimumStory(): return False

            return True

        def checkAllCards() -> bool:
            if not self.handler.dex_card_unlocked: return False
            for name in ABILITY_CARD_LIST:
                if location_table[get_card_location_name_str(name, True)] not in self.previous_location_checked: return False

            return True

        def checkAllBosses() -> bool:
            for stage_name in STAGE_LIST:
                if stage_name == CHALLENGE_NAME: continue
                for boss_name in ALL_BOSSES_LIST[STAGE_NAME_TO_ID[stage_name]]:
                    if location_table[get_boss_location_name_str(STAGE_NAME_TO_ID[stage_name], boss_name, True)] not in self.previous_location_checked: return False

            return True

        def checkFullClear() -> bool:
            return checkAllCards() and checkAllBosses()

        completion_goal = self.options["completion_type"]

        match completion_goal:
            case 0:
                return checkFullStory()
            case 1:
                return checkMinimumStory()
            case 2:
                return checkAllCards()
            case 3:
                return checkAllBosses()
            case 4:
                return checkFullClear()
            case _:
                return False

    #
    # Item Reception and helper functions.
    #
    async def handle_received_items(self, network_index, network_items_list):
        """
        Handle items received from the server. Since some save data is also
        embedded into the items list, the index will be ignored for them specifically.
        The rest of the items are separated into queues and processed simultaneously.
        """
        # Wait until the game is online and the client is not having issues before processing the items.
        while self.handler is None or self.handler.gameController is None or not self.handler.gameController.check_if_in_game() or self.inError:
            await asyncio.sleep(0.5)

        network_item_in_id: list[int] = []
        for network_item in network_items_list:
            network_item_in_id.append(network_item.item)

        # Python slicing will exclude the index of the start point if it's a positive integer.
        # Before actually processing it, wait until the client has loaded the local list of received items.
        while not self.loaded_past_received_items or self.last_received_item_index_server <= -1:
            await asyncio.sleep(0.5)

        datastorage_was_used: bool = False
        local_list_length = len(self.all_received_items)
        # Backup index number from DataStorage. Does not get used if there is local data.
        if (not self.all_received_items or self.all_received_items == []) and self.last_received_item_index_server > 0:
            local_list_length = self.last_received_item_index_server
            datastorage_was_used = True

        newly_received_items: list[NetworkItem] = []

        # Upon receiving this package, check if the index is 0.
        # If it is, bring up the loaded local item list. Grab the length of that local list.
        # Slice the server's list from that number onwards. Only process that.
        if network_index <= 0:
            # If the server's list is somehow shorter than the local one,
            # this is probably divergent history.
            if len(network_items_list) < local_list_length:
                logger.info("Received item list is somehow smaller than the local list. Divergent history?")
                self.all_received_items = []
                for network_item in network_items_list:
                    self.all_received_items.append(network_item.item)
                await self.write_last_item_list()
                return
            # Otherwise, business as usual.
            newly_received_items = network_items_list[local_list_length:]
            # Check if Data Storage's index was used.
            # This should only ever happen upon loading data for the first time.
            if datastorage_was_used:
                for network_item in network_items_list:
                    self.all_received_items.append(network_item.item)
                await self.write_last_item_list()
        # If the index is not 0, check for the most common case first.
        else:
            # If the index is the same as the local list's length, process that as per usual.
            if network_index == local_list_length:
                newly_received_items = network_items_list
            # If the index is different, request a Sync.
            else:
                sync_msg = [{'cmd': 'Sync'}]
                if self.locations_checked:
                    sync_msg.append({"cmd": "LocationChecks",
                                     "locations": list(self.locations_checked)})
                await self.send_msgs(sync_msg)

        # Save data items do not care about index.
        self.handle_save_data_items(network_items_list)
        # Safeguard if there are no newly received items.
        if len(newly_received_items) <= 0: return
        self.handle_filler_items(newly_received_items)
        await self.add_to_item_list(newly_received_items)

    def handle_save_data_items(self, network_item_list: list[NetworkItem]):
        ability_card_unlock_list = []
        stage_unlock_list = []
        progress_item_list = []

        for network_item in network_item_list:
            if network_item.item in ITEM_TABLE_ID_TO_STAGE_NAME:
                stage_unlock_list.append(ITEM_TABLE_ID_TO_STAGE_NAME[network_item.item])
            elif network_item.item in ITEM_TABLE_ID_TO_CARD_ID:
                ability_card_unlock_list.append(ITEM_TABLE_ID_TO_CARD_ID[network_item.item])
            # Item ID for progressive stages.
            # There is really no need to check for this option here since generation realistically will never
            # give Progressive Markets in non-Progressive worlds.
            # The only way to get Progressive Markets in non-Progressive worlds
            # is via console.
            elif self.options["progressive_stages"] and network_item.item == item_table[PROGRESS_ITEM_NAME_FULL].code:
                progress_item_list.append(network_item.item)

        self.handle_ability_cards(ability_card_unlock_list)
        self.handle_stages(stage_unlock_list)

        if len(progress_item_list) > 0:
            self.progressive_stage_list += progress_item_list

        self.handle_progressive_stages(self.progressive_stage_list)

    def handle_ability_cards(self, filtered_list):
        if len(filtered_list) <= 0: return
        for card_name in filtered_list:
            if card_name not in self.permashop_cards:
                self.permashop_cards.append(card_name)
                self.permashop_cards_new.append(card_name)
                self.try_unlock_card_in_shop(card_name)

    def handle_stages(self, filtered_list):
        if len(filtered_list) <= 0: return
        for stage_name_in_list in filtered_list:
            if stage_name_in_list not in self.unlocked_stages:
                self.unlocked_stages.append(stage_name_in_list)
                self.handler.stages_unlocked[stage_name_in_list] = True

        self.handler.updateStageList()

    def handle_progressive_stages(self, all_items_list):
        if len(all_items_list) < 0: return

        progress_item_count = all_items_list.count(item_table[PROGRESS_ITEM_NAME_FULL].code)
        if progress_item_count <= 0: return

        for stage_name_in_list in STAGE_LIST:
            if progress_item_count >= (STAGE_NAME_TO_ID[stage_name_in_list] + 1):
                if stage_name_in_list not in self.unlocked_stages:
                    self.unlocked_stages.append(stage_name_in_list)
                    self.handler.stages_unlocked[stage_name_in_list] = True

        self.handler.updateStageList()

    def handle_filler_items(self, filtered_list):
        if len(filtered_list) <= 0: return

        for filler_item in filtered_list:
            item_id = filler_item.item
            if item_id in ITEM_TABLE_ID_TO_STAGE_NAME: continue
            if item_id in ITEM_TABLE_ID_TO_CARD_ID: continue
            if item_id == item_table[PROGRESS_ITEM_NAME_FULL].code: continue
            if item_id in GAME_ONLY_ITEM_ID:
                self.gameItemQueue.append(item_id)
                continue

            self.menuItemQueue.append(item_id)

        self.handle_menu_items()
        asyncio.create_task(self.handle_game_only_items())

    def try_unlock_card_in_shop(self, card_name: str):
        if (self.handler.isGameInStage()
            or self.enable_card_selection_checking
            or not self.enable_card_shop_scanning):
            return

        self.handler.permashop_card_new = self.permashop_cards_new
        self.handler.setCardShopRecordHandler(card_name, True)
        self.handler.setCardShopRecordGame(card_name, True)

    async def handle_game_only_items(self):
        # Properly handle the items only meant for stages here.
        # This does not get to run if the queue is empty,
        # or the game is not running, or the game is not in a stage.
        while not self.enable_card_selection_checking:
            await asyncio.sleep(0.5)

        for item_id in self.gameItemQueue:
            match item_id:
                # Filler + Useful
                # Lives
                case 1:
                    self.received_lives += 1
                case 8:
                    self.received_lives += 2
                # Bullet Money
                case 4:
                    self.received_bullet_money += 200
                case 5:
                    self.received_bullet_money += 500
                case 7:
                    self.received_bullet_money += 1000
                case 12:
                    self.received_bullet_money += 5
                case 13:
                    self.received_bullet_money += 10
                # Shot Attack %
                case 14:
                    self.received_shot_attack += 15
                case 15:
                    self.received_shot_attack += 30
                case 16:
                    self.received_shot_attack += 45
                case 17:
                    self.received_shot_attack += 60
                case 300:
                    self.received_shot_attack += 100
                case 301:
                    self.received_shot_attack += 200
                # Magic Circle Attack %
                case 18:
                    self.received_circle_atk += 30
                case 19:
                    self.received_circle_atk += 60
                case 20:
                    self.received_circle_atk += 90
                case 21:
                    self.received_circle_atk += 120
                # Magic Circle Size %
                case 22:
                    self.received_circle_size += 5
                case 23:
                    self.received_circle_size += 10
                case 24:
                    self.received_circle_size += 15
                case 25:
                    self.received_circle_size += 20
                # Magic Circle Duration %
                case 26:
                    self.received_circle_duration += 10
                case 27:
                    self.received_circle_duration += 20
                # Magic Circle Graze Range %
                case 28:
                    self.received_circle_graze += 15
                case 29:
                    self.received_circle_graze += 30
                case 30:
                    self.received_circle_graze += 45
                case 31:
                    self.received_circle_graze += 60
                # Movement Speed %
                case 32:
                    self.received_speed += 20
                # Invincibility
                case 40:
                    self.received_invincibility += 120
                case 41:
                    self.received_invincibility += 300
                case 42:
                    self.received_invincibility += 600
                case 400:
                    self.received_invincibility += 420

                # Traps
                # Bullet Money
                case 50:
                    self.received_bullet_money -= 50
                case 51:
                    self.received_bullet_money -= 100
                case 52:
                    self.received_bullet_money -= 200
                case 53:
                    self.received_bullet_money -= 300
                # Movement Speed
                case 71:
                    self.received_speed += 500
                case 73:
                    self.received_speed += 1000
                # Invincibility
                case 72:
                    self.received_invinc_cancel = True
                # Default
                case _:
                    logger.info(f"Ignoring unknown game item (ID {item_id}).")

            self.gameItemQueue.remove(item_id)

        if self.received_bullet_money != 0:
            self.handler.addBulletMoney(self.received_bullet_money)
        if self.received_lives != 0:
            self.handler.addLife(self.received_lives)
        if self.received_shot_attack != 0:
            self.handler.gameController.addShotAttack(self.received_shot_attack)

        if self.received_circle_atk != 0:
            self.handler.gameController.addMagicCircleAttack(self.received_circle_atk)
        if self.received_circle_size != 0:
            self.handler.gameController.addMagicCircleSize(self.received_circle_size)
        if self.received_circle_duration != 0:
            self.handler.gameController.addMagicCircleDuration(self.received_circle_duration)
        if self.received_circle_graze != 0:
            self.handler.gameController.addMagicCircleGraze(self.received_circle_graze)

        if self.received_speed != 0:
            self.handler.gameController.addSpeed(self.received_speed)
        if self.received_invincibility != 0:
            self.handler.gameController.addInvincibility(self.received_invincibility)
        if self.received_invinc_cancel:
            self.handler.gameController.clearInvincibility()

        self.received_bullet_money = 0
        self.received_lives = 0
        self.received_shot_attack = 0
        self.received_circle_atk = 0
        self.received_circle_size = 0
        self.received_circle_duration = 0
        self.received_circle_graze = 0
        self.received_speed = 0
        self.received_invincibility = 0
        self.received_invinc_cancel = False

        return

    def handle_menu_items(self):
        # These items get processed no matter what,
        # but effects may differ depending on certain criteria.
        for item_id in self.menuItemQueue:
            match item_id:
                # Filler + Useful
                case 2:
                    self.received_funds += 200
                case 3:
                    self.received_funds += 1000
                case 6:
                    self.received_funds += 500
                case 10:
                    self.received_funds += 5
                case 11:
                    self.received_funds += 10
                # Traps
                case 60:
                    self.received_funds -= 50
                case 61:
                    self.received_funds -= 100
                case 62:
                    self.received_funds -= 200
                case 63:
                    self.received_funds -= 300
                case 70:
                    self.received_equip_cost -= 50
                # Default
                case _:
                    logger.info(f"Ignoring unknown item (ID {item_id}).")

            self.menuItemQueue.remove(item_id)

        if self.received_funds != 0:
            asyncio.create_task(self.addFundsToGame(self.received_funds))
        # Equip Cost never goes below 100%. This is checked when applying.
        if self.received_equip_cost != 0:
            self.handler.addEquipCost(self.received_equip_cost)
            self.received_equip_cost = 0

        return

    async def addFundsToGame(self, received_funds: int):
        while not self.menu_stats_initialized:
            await asyncio.sleep(0.5)

        if self.enable_card_selection_checking:
            self.handler.addGameFunds(received_funds)
        else:
            self.handler.addMenuFunds(received_funds)
            if not self.energylink_enabled:
                await self.save_menu_funds_to_server()

        self.received_funds = 0

    #
    # Functions for saving custom data to server.
    #
    # If EnergyLink is enabled, don't save anything related to Funds.
    async def save_menu_stats_to_server(self):
        self.menuFunds = self.handler.getMenuFunds()
        self.loadout_slots = clamp(self.handler.getCardSlots(), 1, 34)
        self.equip_cost = self.handler.getEquipCost()

        if self.energylink_enabled:
            await self.send_msgs(
                [
                    {
                        "cmd": "Set",
                        "key": self.custom_data_keys_list[1],
                        "default": 1,
                        "operations": [{"operation": 'replace', "value": self.loadout_slots}]
                    },
                    {
                        "cmd": "Set",
                        "key": self.custom_data_keys_list[2],
                        "default": 100,
                        "operations": [{"operation": 'replace', "value": self.equip_cost}]
                    }
                ]
            )
            return

        await self.send_msgs(
            [
                {
                    "cmd": 'Set',
                    "key": self.custom_data_keys_list[0],
                    "default": 0,
                    "operations": [{"operation": 'replace', "value": self.menuFunds}]
                },
                {
                    "cmd": "Set",
                    "key": self.custom_data_keys_list[1],
                    "default": 1,
                    "operations": [{"operation": 'replace', "value": self.loadout_slots}]
                },
                {
                    "cmd": "Set",
                    "key": self.custom_data_keys_list[2],
                    "default": 100,
                    "operations": [{"operation": 'replace', "value": self.equip_cost}]
                }
            ]
        )

    async def save_menu_funds_to_server(self):
        if self.energylink_enabled: return

        self.menuFunds = self.handler.getMenuFunds()

        await self.send_msgs(
            [
                {
                    "cmd": 'Set',
                    "key": self.custom_data_keys_list[0],
                    "default": 0,
                    "operations": [{"operation": 'replace', "value": self.menuFunds}]
                }
            ]
        )

    async def save_last_index_to_server(self):
        self.last_received_item_index_server = len(self.all_received_items)
        await self.send_msgs(
            [
                {
                    "cmd": 'Set',
                    "key": self.custom_data_keys_list[3],
                    "default": 0,
                    "operations": [{"operation": 'replace', "value": self.last_received_item_index_server}]
                }
            ]
        )

    #
    # Async loops that handle the game process.
    #
    async def wait_for_initial_connection_info(self):
        """
        This method waits until the client finishes the initial conversation with the server.
        See client_recieved_initial_server_data for wait requirements.
        """
        self.retrievedCustomData = False

        if self.client_received_initial_server_data():
            return

        logger.info("Waiting for connect from server...")
        while not self.client_received_initial_server_data() and not self.exit_event.is_set():
            await asyncio.sleep(1)

    async def connect_to_game(self):
        """
        Connect the client to the game process.
        """
        self.handler = None

        while self.handler is None:
            try:
                self.handler: GameHandler = GameHandler()
            except Exception as e:
                await asyncio.sleep(2)

    async def reconnect_to_game(self):
        """
        Reconnect to the game without resetting everything
        """

        while self.handler.gameController is None:
            try:
                self.handler.reconnect()
            except Exception as e:
                await asyncio.sleep(2)

    async def main_loop(self):
        """
        Main loop. Responsible for scanning locations for checks and stage updates.
        """
        try:
            await self.update_locations_checked()
            self.update_stage_list()
        except Exception as e:
            self.inError = True
            logger.error(f"Error in the MAIN loop.")
            logger.error(traceback.format_exc())

    async def game_loop(self):
        """
        Game loop. Doesn't really do much.
        """
        try:
            if not self.handler.isGameInStage(): return

            if self.enable_card_shop_scanning: self.enable_card_shop_scanning = False
            if not self.enable_card_selection_checking:
                await self.transfer_from_menu_to_stage()
                self.enable_card_selection_checking = True
        except Exception as e:
            self.inError = True
            logger.error(f"Error in the GAME loop.")
            logger.error(traceback.format_exc())

    async def menu_loop(self):
        """
        Menu-only loop. Responsible for handling menu-exclusive things.
        Mainly here to fiddle with the Permanent Card Shop since it has 2 checks in 1,
        split between the gameplay section and the menu section.
        """
        try:
            if not self.no_card_unlocked:
                self.handler.unlockNoCard()
                self.no_card_unlocked = True

            if self.handler.isGameInStage(): return

            if self.enable_card_selection_checking: self.enable_card_selection_checking = False
            if not self.enable_card_shop_scanning:
                await self.transfer_from_stage_to_menu()
                self.enable_card_shop_scanning = True
        except Exception as e:
            self.inError = True
            logger.error(f"Error in the MENU loop.")
            logger.error(traceback.format_exc())

    async def update_locations_checked(self):
        """
        Check if any locations has been checked since this was last called.
        If there is, send a message and update the checked location list.
        """
        def obligatory_location_table_check(given_location_name: str) -> bool:
            """
            Obligatory location table check function.
            If this returns False, location does not exist or has already been checked.
            If True, it does exist AND has not been checked yet.

            :param given_location_name: The (string) name of the location to check.
            """
            if given_location_name not in location_table: return False
            if location_table[given_location_name] not in self.all_location_ids: return False
            if location_table[given_location_name] in self.previous_location_checked: return False

            return True

        new_locations = []

        if self.loadingDataSetup: return

        # Check bosses first.
        for stage_name in STAGE_LIST:
            if stage_name != CHALLENGE_NAME:
                for boss_name in ALL_BOSSES_LIST[STAGE_NAME_TO_ID[stage_name]]:
                    # Get the location name first, convert that to ID,
                    # and then append if it is not in previously checked locations.
                    # Encounters
                    if self.handler.getBossRecordGame(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name]):
                        locationName: str = get_boss_location_name_str(STAGE_NAME_TO_ID[stage_name], boss_name)
                        if obligatory_location_table_check(locationName):
                            self.handler.setBossRecordHandler(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name],
                                                              True)
                            new_locations.append(location_table[locationName])
                    # Defeat
                    if self.handler.getBossRecordGame(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name], 1):
                        locationName: str = get_boss_location_name_str(STAGE_NAME_TO_ID[stage_name], boss_name, True)
                        if obligatory_location_table_check(locationName):
                            self.handler.setBossRecordHandler(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name],
                                                              True, 1)
                            new_locations.append(location_table[locationName])
            else:
                # Special Challenge Market clause
                boss_set_id_loc = 1
                for boss_set in ALL_BOSSES_LIST:
                    # If it's the Tutorial set or End of Market set, discard those.
                    if TUTORIAL_ID <= boss_set_id_loc >= STAGE_CHIMATA_ID: continue
                    for boss_name in boss_set:
                        # Make sure to exclude the story bosses.
                        if boss_name in STORY_BOSSES_LIST: continue
                        # There are only encounters. Check those.
                        if self.handler.getBossRecordGame(STAGE_CHALLENGE_ID, BOSS_NAME_TO_ID[boss_name]):
                            locationName: str = get_boss_location_name_str(STAGE_CHALLENGE_ID, boss_name)
                            if obligatory_location_table_check(locationName):
                                self.handler.setBossRecordHandler(STAGE_CHALLENGE_ID, BOSS_NAME_TO_ID[boss_name], True)
                                new_locations.append(location_table[locationName])

        # Check Ability Cards.
        # Split into stage-exclusive and dex.
        # First step is checking if the card location exists in the big location table.

        # Stage-exclusive.
        player_has_found_card_in_stage = False
        if self.checkIfGameInStage():
            for card in ABILITY_CARD_LIST:
                cardLocationName: str = get_card_location_name_str(card, False)
                if not obligatory_location_table_check(cardLocationName): continue

                # Card shop unlock location does exist if it made it past that.
                if self.handler.getCardShopRecordGame(card) != 0:
                    # Card shop location is True. This is a check.
                    new_locations.append(location_table[cardLocationName])
                    player_has_found_card_in_stage = True

            if self.handler.isBlackMarketOpen():
                self.handler.setDexCardData(NAZRIN_CARD_2, True)
                cardLocationName: str = get_card_location_name_str(NAZRIN_CARD_2, True)
                if obligatory_location_table_check(cardLocationName):
                    new_locations.append(location_table[cardLocationName])

        # Dex
        player_has_purchased_card_bool = False
        for card in ABILITY_CARD_LIST:
            cardLocationName: str = get_card_location_name_str(card, True)
            if not obligatory_location_table_check(cardLocationName): continue

            # Card dex location does exist if it made it past that.
            if self.handler.getDexCardData(card):
                # Card dex location is True. This is a check.
                new_locations.append(location_table[cardLocationName])
                player_has_purchased_card_bool = True

        # Finally, check for Music Room and Achievements.
        # Music Room goes first.
        if self.options["music_room_checks"]:
            for soundtrack_id in MUSIC_ROOM_NAME_DICT.keys():
                musicLocationName: str = get_music_location_name_str(soundtrack_id)
                if not obligatory_location_table_check(musicLocationName): continue

                # Music Room location does exist if it made it past that.
                if self.handler.getMusicRecord(soundtrack_id):
                    # Track has been unlocked. This is a check.
                    new_locations.append(location_table[musicLocationName])

        # And then Achievements.
        if self.options["achievement_checks"]:
            for achievement_id in ACHIEVE_NAME_DICT.keys():
                achieveLocationName: str = get_achievement_location_name_str(achievement_id)
                if not obligatory_location_table_check(achieveLocationName): continue

                # Achievement location does exist.
                if self.handler.getAchievementStatus(achievement_id):
                    new_locations.append(location_table[achieveLocationName])

        # If there are new locations, send a message to the server
        # and add to the list of previously checked locations.
        if new_locations:
            # Since both of Nazrin's cards do not get unlocked at all past the Tutorial,
            # This is added so that it gets unlocked in the dex.
            # The Bullet Money variant is set to be unlocked at the opening of a Black Market.
            # The Funds variant is set to be unlocked at the Market Card Reward selection.
            if player_has_found_card_in_stage:
                self.handler.setDexCardData(NAZRIN_CARD_1, True)
                cardLocationName: str = get_card_location_name_str(NAZRIN_CARD_1, True)
                if obligatory_location_table_check(cardLocationName):
                    new_locations.append(location_table[cardLocationName])

            if player_has_purchased_card_bool and not self.energylink_enabled: await self.save_menu_funds_to_server()

            self.previous_location_checked = self.previous_location_checked + new_locations
            await self.send_msgs([{"cmd": 'LocationChecks', "locations": new_locations}])

        if self.checkVictory() and not self.finished_game:
            self.finished_game = True
            await self.send_msgs([{"cmd": 'StatusUpdate', "status": 30}])

    async def get_custom_data_from_server(self):
        self.retrievedCustomData = True
        if self.energylink_enabled:
            await self.send_msgs([{"cmd": "Get", "keys": self.custom_data_keys_list[1:]}])
            await self.send_msgs([{"cmd": "SetNotify", "keys": self.custom_data_keys_list[1:]}])
            return
        await self.send_msgs([{"cmd": "Get", "keys": self.custom_data_keys_list}])
        await self.send_msgs([{"cmd": "SetNotify", "keys": self.custom_data_keys_list}])

    async def load_save_data(self):
        """
        Load all save data as needed before location checking can begin.
        Should be carried out at the very first game connection.
        """
        while self.handler is None or self.handler.gameController is None or not self.handler.gameController.check_if_in_game():
            await asyncio.sleep(0.5)

        self.handler.setLoadMenuIndex(self.options["starting_market"])

        self.load_sava_data_records()
        self.load_save_data_bosses()
        self.load_save_data_dex()
        self.load_save_data_menu()

        return

    def load_save_data_bosses(self):
        # Assume that the game is in 100% locked mode.
        for location_id in self.previous_location_checked:
            full_location_name = location_id_to_name[location_id]
            # Iterate through all shortened stage names.
            for stage_name in STAGE_LIST:
                # If this stage name exists in the location's name, continue.
                # If not, abort mission.
                if stage_name in full_location_name:
                    if stage_name == CHALLENGE_NAME:
                        # Special Challenge Market clause
                        boss_set_id_loc = 1
                        for boss_set in ALL_BOSSES_LIST:
                            # If it's the Tutorial set or End of Market set, discard those.
                            if TUTORIAL_ID <= boss_set_id_loc >= STAGE_CHIMATA_ID: continue
                            for boss_name in boss_set:
                                if boss_name not in full_location_name: continue
                                self.handler.setBossRecordHandler(STAGE_CHALLENGE_ID, BOSS_NAME_TO_ID[boss_name], True)
                                self.handler.setBossRecordGame(STAGE_CHALLENGE_ID, BOSS_NAME_TO_ID[boss_name], True)
                    else:
                        for boss_name in ALL_BOSSES_LIST[STAGE_NAME_TO_ID[stage_name]]:
                            if boss_name not in full_location_name: continue
                            record_type = ENCOUNTER_ID
                            if DEFEAT_TYPE_NAME in full_location_name: record_type = DEFEAT_ID
                            self.handler.setBossRecordHandler(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name],
                                                              True, record_type)
                            self.handler.setBossRecordGame(STAGE_NAME_TO_ID[stage_name], BOSS_NAME_TO_ID[boss_name],
                                                           True, record_type)

    def load_save_data_dex(self):
        # Assume that the game is in 100% locked mode.
        for location_id in self.previous_location_checked:
            full_location_name = location_id_to_name[location_id]
            # If none of these locations talk about the Card Dex, discard and move on.
            if CARD_DEX_NAME not in full_location_name:
                continue

            for card_string_id in ABILITY_CARD_LIST:
                card_location_name: str = get_card_location_name_str(card_string_id, True)
                if card_location_name == full_location_name:
                    self.handler.unconditionalDexUnlock(card_string_id)

    def load_save_data_menu(self):
        if not self.energylink_enabled: self.handler.setMenuFunds(self.menuFunds)
        self.handler.setCardSlots(self.loadout_slots)
        self.handler.setEquipCost(self.equip_cost)

        self.menu_stats_initialized = True

    def load_sava_data_records(self):
        # Assume that the game is in 100% locked mode.
        for location_id in self.previous_location_checked:
            full_location_name = location_id_to_name[location_id]
            # Check for the Music Room first.
            if self.options["music_room_checks"] and MUSIC_ROOM_UNLOCK_STR in full_location_name:
                for music_id, music_name in MUSIC_ROOM_NAME_DICT.items():
                    if music_name not in full_location_name: continue
                    self.handler.setMusicRecord(music_id, True)

            # Then Achievements.
            if self.options["achievement_checks"] and ACHIEVE_UNLOCK_STR in full_location_name:
                for achievement_id, achievement_name in ACHIEVE_NAME_DICT.items():
                    if achievement_name not in full_location_name: continue
                    self.handler.setAchievementStatus(achievement_id, True)

    async def transfer_from_menu_to_stage(self):
        """
        Handles transferring from the menu to the game stage.
        Mainly for the Ability Card shop addresses.
        Previously checked locations are save data for Card Selection checks.
        """
        menu_shop_card_list = ABILITY_CARD_LIST
        for invalid_card in ABILITY_CARD_CANNOT_EQUIP:
            if invalid_card in menu_shop_card_list: menu_shop_card_list.remove(invalid_card)

        # Clear out the records of the entire Card Shop in the memory.
        for card_string_id in menu_shop_card_list:
            self.handler.setCardShopRecordGame(card_string_id, False)

        # Go over the list of acquired checks and set as appropriate.
        for location_id in self.previous_location_checked:
            full_location_name = location_id_to_name[location_id]
            # If none of these locations talk about the Market Card Reward, discard and move on.
            if ENDSTAGE_CHOOSE_NAME not in full_location_name:
                continue

            # It does not really matter what value the records are set to aside from 0x00 and non-0x00.
            for card_string_id in menu_shop_card_list:
                card_location_name: str = get_card_location_name_str(card_string_id, False)
                if card_location_name == full_location_name:
                    self.handler.setCardShopRecordGame(card_string_id, True)

        await self.save_menu_stats_to_server()

    async def transfer_from_stage_to_menu(self):
        """
        Handles transferring from the game stage to the menu.
        """
        menu_shop_card_list = ABILITY_CARD_LIST
        for invalid_card in ABILITY_CARD_CANNOT_EQUIP:
            if invalid_card in menu_shop_card_list: menu_shop_card_list.remove(invalid_card)

        # Clear out the records of the entire Card Shop in the memory.
        for card_string_id in menu_shop_card_list:
            self.handler.setCardShopRecordGame(card_string_id, False)

        await asyncio.sleep(0.5)

        # For all cards that can be bought in the shop...
        for card_name in menu_shop_card_list:
            # Check if it's unlocked.
            if card_name in self.permashop_cards:
                self.handler.setCardShopRecordHandler(card_name, True)
                self.handler.permashop_card_new = self.permashop_cards_new
            self.handler.setCardShopRecordGame(card_name, card_name in self.permashop_cards)

        # Check Card Slots and unlock its achievement as needed, if it hasn't already.
        if self.handler.getCardSlots() >= 7 and not self.handler.getAchievementStatus(10):
            self.handler.setAchievementStatus(10, True)

        # Resets stats for Death Link if it is active.
        if self.deathlink_enabled: self.reset_deathlink_stats()

        # Save Funds, Card Slots, and Equip Cost.
        await self.save_menu_stats_to_server()


    #
    # Last Received Item Index handling.
    #
    # The data is saved in a .json named "th185ap_????.json", where ???? is the seed name.
    # The data consists of a Dictionary, wherein there is the slot name and received item list.
    # Only do this after connection has been established since this calls for the seed name and slot name.
    #
    # Use orjson functions for dealing with said .json.
    async def initial_load_last_item_list(self):
        # Responsible for loading the index of the last item received when client connects to the server.
        # The usual workflow of this function is as follows:
        # 1. Check if the file exists in the path.
        # 2. If the file exists, read the entire file as one Dictionary.
        # 3. Check if the slot name matches and if the item list exists.
        # 5. Read the item list as a list.
        #
        # If at any point that any of the steps above fail, skip the entire thing.

        # Check if this operation has already been carried out before.
        if self.loaded_past_received_items: return

        json_file_name = get_item_index_save_name(self.seed_name, self.team, self.slot)
        full_file_path = os.path.join(self.scorefile_path, os.path.basename(json_file_name))

        # Check if the file exists.
        if os.path.exists(full_file_path):
            with open(full_file_path) as json_file:
                saved_data_dict: dict = orjson.loads(json_file.read())
                # Check if the slot name matches and item list exists.
                if JSON_SLOT_ITEMS in saved_data_dict:
                    self.all_received_items = saved_data_dict[JSON_SLOT_ITEMS]

        self.loaded_past_received_items = True
        return

    async def add_to_item_list(self, item_list: list[NetworkItem]):
        # Adds item to the list of received items.
        # Call the function to write the item list to a local file afterwards.
        if item_list is None or item_list == []:
            return

        item_id_list: list[int] = []
        for network_item in item_list:
            item_id_list.append(network_item.item)

        self.all_received_items += item_id_list

        await self.write_last_item_list()

    async def write_last_item_list(self):
        # Writes the last received item index to a .json file named "th185ap".
        # Initial check to make sure the client has not reset itself.
        if not self.is_connected and not self.inError: return
        if len(self.all_received_items) <= 0: return

        json_file_name = get_item_index_save_name(self.seed_name, self.team, self.slot)
        full_file_path = os.path.join(self.scorefile_path, os.path.basename(json_file_name))

        full_dict = {
            JSON_SLOT_NAME: self.player_names[self.slot],
            JSON_SLOT_ITEMS: self.all_received_items
        }

        # Remove the old file before writing.
        if os.path.exists(full_file_path):
            os.remove(full_file_path)
        # Overwrite the entire thing.
        with open(full_file_path, "wb") as json_file:
            json_file.write(orjson.dumps(full_dict))

        # Write this to the server. No need to wait for it, though.
        # It's just a backup measure if local data is somehow gone.
        asyncio.create_task(self.save_last_index_to_server())
        return

    #
    # Death Link
    #
    def on_deathlink(self, data: typing.Dict[str, typing.Any]) -> None:
        """
        Called when receiving a Death Link from the server.
        """
        self.pending_received_deathlink = True
        if not self.enable_card_selection_checking:
            self.pending_life_deduction = True
            self.pending_received_deathlink = False
        return super().on_deathlink(data)

    async def send_deathlink(self):
        """
        Sends a Deathlink to the server, if the server is active.
        """
        # If Death Link is not enabled, don't send anything.
        if not self.deathlink_enabled: return
        await self.send_death(self.player_names[self.slot] + get_random_death_message(self.lost_final_life))

    async def deathlink_loop(self):
        # If going back to the menu, the first transition will turn off
        # both pending Death Link and the "Died to Death Link" flag.

        # If Death Link isn't enabled, return.
        if not self.deathlink_enabled: return
        try:
            player_state_normal_bool: bool = self.handler.checkForPlayerNormal()
            player_state_dead_bool: bool = self.handler.checkForPlayerDeath()
            ingame_life: int = self.handler.gameController.getLives()

            # This loop will only run when the game is currently in a stage.
            # Skip the loop otherwise.

            # If not in a stage, don't do anything here.
            if not self.checkIfGameInStage(): return

            # If a Death Link had already arrived, it will be stored as a life lost.
            # Upon entering a stage, immediately deduct 1 Life.
            if self.pending_life_deduction:
                self.handler.addLife(-1)
                self.pending_life_deduction = False
                return

            if player_state_normal_bool and self.last_recorded_life != ingame_life:
                self.last_recorded_life = ingame_life

            # There is no need to check for deathbomb since the player has no bombs here anyways.
            # If the player received a Death Link from the server and they are not dead, try to kill the player.
            # Then, turn off the Death Link flag.
            if self.pending_received_deathlink and not self.died_to_deathlink:
                # If Anti-Death Link Invincibility is enabled, check against invincibility.
                if self.death_link_check_invincibility(): self.handler.killPlayer()
                self.died_to_deathlink = True
                self.pending_received_deathlink = False
            # In case there is no pending Death Link but the player died due to it before,
            # monitor them until death/invincibility wears off.
            elif self.died_to_deathlink:
                if player_state_normal_bool:
                    self.died_to_deathlink = False
            # If the player has not received a Death Link and did not die to Death Link before,
            # monitor them until their death kicks in.
            # If a death is registered, send a Death Link.
            elif player_state_dead_bool:
                if not self.caused_deathlink:
                    self.lost_final_life = self.last_recorded_life <= 0
                    if (self.deathlink_trigger == DEATH_LINK_TRIGGER_LIFE
                        or (self.deathlink_trigger == DEATH_LINK_TRIGGER_STAGE and self.last_recorded_life <= 0)):
                        self.caused_deathlink = True
                        await self.send_deathlink()
            elif self.caused_deathlink and player_state_normal_bool:
                self.caused_deathlink = False
        except Exception as e:
            self.inError = True
            logger.error(f"Error in the DEATH LINK loop.")
            logger.error(traceback.format_exc())

    def reset_deathlink_stats(self):
        self.pending_received_deathlink = False
        self.pending_life_deduction = False
        self.died_to_deathlink = False
        self.caused_deathlink = False
        self.lost_final_life = False

    def generic_loop_running_condition(self):
        return not self.exit_event.is_set() and self.handler and not self.inError

    def death_link_check_invincibility(self) -> bool:
        return not self.options["death_link_invincibility"] or (self.options["death_link_invincibility"] and not self.handler.checkInvincibility())

    #
    # Energy Link
    #
    # This will first take a look at the amount in the game.
    # Compare the amount to subtract to the amount that's in store.
    # If what the player has is less than the desired amount,
    # subtract that number instead.
    # Otherwise, subtract according to the desired amount.
    # If at 0, reactions differ depending on whether the game is in a stage or not.
    async def deposit_currency(self, amount: int, currency_type: int):
        amount_to_deposit: int = 0

        if currency_type == CURRENCY_FUNDS_ID:
            self.menuFunds = self.handler.getMenuFunds()

            # Check if the game is in the menu.
            if not self.checkIfGameInStage():
                if self.menuFunds < amount:
                    amount_to_deposit = self.menuFunds
                else: amount_to_deposit = amount

                self.handler.addMenuFunds(-amount_to_deposit)
            # Otherwise, the game is in a stage.
            # Deduct from the current Funds in the stage first.
            else:
                gameFunds = self.handler.getGameFunds()
                # If game Funds are insufficient, dip into the menu Funds.
                if gameFunds < amount:
                    amount_to_deposit = gameFunds
                    self.handler.addGameFunds(-amount_to_deposit)
                    # Dipping into the menu Funds here.
                    # Check if it can cover the remaining difference.
                    # If it cannot, add all of it to the deposit and set it to 0.
                    if self.menuFunds < (amount - amount_to_deposit):
                        amount_to_deposit += self.menuFunds
                        self.handler.setMenuFunds(0)
                    # If it can cover, deduct the difference and ship the full amount as usual.
                    else:
                        self.handler.addMenuFunds(-(amount - amount_to_deposit))
                        amount_to_deposit = amount
                # If game Funds are sufficient, deduct that amount and ship it off to the server.
                else:
                    amount_to_deposit = amount
                    self.handler.addGameFunds(-amount_to_deposit)
        elif currency_type == CURRENCY_BULLET_MONEY_ID:
            # Check if the game is in the menu.
            # If it is, skip.
            if not self.checkIfGameInStage():
                logger.info("There is no Bullet Money to deposit. Enter a stage first.")
                return
            # If not, check for Bullet Money.
            else:
                currentBulletMoney = self.handler.getBulletMoney()
                if currentBulletMoney < amount:
                    amount_to_deposit = currentBulletMoney
                else: amount_to_deposit = amount

                self.handler.addBulletMoney(-amount_to_deposit)
        else:
            logger.info(INVALID_CURRENCY_STRING)
            return

        if amount_to_deposit <= 0:
            currency_name = CURRENCY_NAME_FUNDS
            if currency_type == CURRENCY_BULLET_MONEY_ID:
                currency_name = CURRENCY_NAME_BULLET_MONEY

            logger.info(f"Not enough {currency_name} to deposit.")
            return
        await self.send_deposit_msg(amount_to_deposit, currency_type)

    # 1. Check the amount against what the player already has and the maximum they can have.
    # 2. Subtract down to a number they will get without overflowing the maximum money counter.
    # 3. Send a request to withdraw energy from the server (attach currency type in tags and compare later).
    # 4. Convert the withdrawn energy into the received amount (may differ due to the exchange rates).
    # 5. Add that amount into the game accordingly.
    async def withdraw_currency(self, amount: int, currency_type: int):
        current_currency_amount: int = 0
        amount_to_withdraw: int = 0

        # Grab the current amount of currency on hand.
        # Check for currency type here to read the correct amount.
        # If the retrieved amount is at max, immediately cancel the entire operation.
        if currency_type == CURRENCY_FUNDS_ID:
            if not self.checkIfGameInStage():
                current_currency_amount = self.handler.getGameFunds()
            else:
                current_currency_amount = self.handler.getMenuFunds()

            if current_currency_amount >= MAX_FUNDS:
                logger.info("Cannot withdraw any more Funds. Maximum amount reached.")
                return
        elif currency_type == CURRENCY_BULLET_MONEY_ID:
            if not self.checkIfGameInStage():
                logger.info(BULLET_MONEY_CANNOT_WITHDRAW)
                return

            current_currency_amount = self.handler.getBulletMoney()

            if current_currency_amount >= MAX_BULLET_MONEY:
                logger.info("Cannot withdraw any more Bullet Money. Maximum amount reached.")
        else:
            logger.info(INVALID_CURRENCY_STRING)
            return

        # Check against what the player already has. Check for currency type here as well.
        # Invalid currency types have already been filtered out above, so no need to do it here.
        #
        # Take the maximum and subtract from the current amount to get the difference.
        # Clamp the withdrawable amount to that range.
        difference_amount: int = 0
        if currency_type == CURRENCY_FUNDS_ID:
            difference_amount = MAX_FUNDS - current_currency_amount
        elif currency_type == CURRENCY_BULLET_MONEY_ID:
            difference_amount = MAX_BULLET_MONEY - current_currency_amount

        amount_to_withdraw = clamp(amount, 0, difference_amount)

        await self.send_withdraw_msg(amount_to_withdraw, currency_type)


    async def process_received_currency(self, received_amount: int, currency_type: int):
        # SetReply received.
        # Check if anything was actually withdrawn.
        if received_amount <= 0:
            logger.info("Nothing was withdrawn from the Energy Link pool.")
            return

        # Compare the actual deducted amount (positive integer).
        # The received amount should have already been converted from joules.
        # If the received amount is 0, don't do anything.
        # Run another in-game value check to make sure the withdrawn amount can be given.
        withdrawn_currency_name: str = CURRENCY_NAME_FUNDS
        current_currency_amount: int = 0
        difference_amount: int = 0

        if currency_type == CURRENCY_FUNDS_ID:
            if self.checkIfGameInStage():
                current_currency_amount = self.handler.getGameFunds()
            else:
                current_currency_amount = self.handler.getMenuFunds()
        elif currency_type == CURRENCY_BULLET_MONEY_ID:
            withdrawn_currency_name = CURRENCY_NAME_BULLET_MONEY
            if self.checkIfGameInStage():
                current_currency_amount = self.handler.getBulletMoney()
            else:
                logger.info(BULLET_MONEY_CANNOT_WITHDRAW)
                await self.send_deposit_msg(received_amount, currency_type, True)
                return

        # Subtract the maximum from the current in-game amount.
        # Compare that to the received amount.
        # Clamp the received amount to only the difference.
        # Return the rest to the server afterwards.
        if currency_type == CURRENCY_FUNDS_ID:
            difference_amount = MAX_FUNDS - current_currency_amount
        elif currency_type == CURRENCY_BULLET_MONEY_ID:
            difference_amount = MAX_BULLET_MONEY - current_currency_amount

        amount_to_withdraw = clamp(received_amount, 0, difference_amount)
        remaining_currency = received_amount - amount_to_withdraw

        if currency_type == CURRENCY_FUNDS_ID:
            if self.checkIfGameInStage():
                self.handler.addGameFunds(amount_to_withdraw)
            else:
                self.handler.addMenuFunds(amount_to_withdraw)
        elif currency_type == CURRENCY_BULLET_MONEY_ID:
            if self.checkIfGameInStage():
                self.handler.addBulletMoney(amount_to_withdraw)
            else:
                logger.info(BULLET_MONEY_CANNOT_WITHDRAW)
                await self.send_deposit_msg(received_amount, currency_type, True)
                return

        if remaining_currency > 0:
            await self.send_deposit_msg(remaining_currency, currency_type, True)

        logger.info(f"Withdrawn {received_amount} {withdrawn_currency_name} from the Energy Link pool.")

    async def send_deposit_msg(self, final_amount: int, currency_type: int, was_return: bool = False):
        currency_name: str = CURRENCY_NAME_FUNDS
        if currency_type == CURRENCY_BULLET_MONEY_ID:
            currency_name = CURRENCY_NAME_BULLET_MONEY
        if not was_return:
            logger.info(f"Deposited {final_amount} {currency_name} to the Energy Link pool.")
        else:
            logger.info(f"Returned {final_amount} {currency_name} to the Energy Link pool.")

        await self.send_direct_deposit_msg(convert_currency_to_joules(final_amount, currency_type))

    async def send_direct_deposit_msg(self, final_amount: int):
        await self.send_msgs([
            {
                "cmd": "Set",
                "key": f"EnergyLink{self.team}",
                "default": 0,
                "operations": [
                    {"operation": "add", "value": final_amount}
                ]
            }
        ])

    async def send_withdraw_msg(self, final_amount: int, currency_type: int):
        currency_name: str = "Funds"
        if currency_type == CURRENCY_BULLET_MONEY_ID:
            currency_name = "Bullet Money"

        # No need to use slot number and team number here.
        # Team number can be checked via the EnergyLink pool key.
        # Slot number will be sent in the SetReply package.
        await self.send_msgs([
            {
                "cmd": "Set",
                "key": f"EnergyLink{self.team}",
                "tag": get_energy_withdraw_tag(self.seed_name, currency_type),
                "default": 0,
                "want_reply": True,
                "operations": [
                    {"operation": "add", "value": 0 - convert_currency_to_joules(final_amount, currency_type)},
                    {"operation": "max", "value": 0}
                ]
            }
        ])


async def game_watcher(ctx: TouhouHBMContext):
    """
    Client loop that watches the gameplay progress.
    Start the different loops once connected that will handle the game.
	It will also attempt to reconnect if the connection to the game is lost.
    """
    await ctx.wait_for_initial_connection_info()
    await ctx.initial_load_last_item_list()

    while not ctx.exit_event.is_set():
        # Client was disconnected from the server
        if not ctx.server:
            # Reset the context in that case
            if ctx.is_connected:
                logger.info("Client was disconnected from the server.")
            ctx.reset()
            await ctx.wait_for_initial_connection_info()
            await ctx.initial_load_last_item_list()
        else:
            if not ctx.retrievedCustomData:
                try:
                    await ctx.get_custom_data_from_server()
                except Exception as e:
                    ctx.inError = True
                    logger.error("Failed to retrieve save data.")
                    logger.error(traceback.format_exc())

        # Trying to make first connection to the game
        if ctx.handler is None and not ctx.inError:
            logger.info(f"Trying to find {SHORT_NAME} game process...")
            asyncio.create_task(ctx.connect_to_game())
            while ctx.handler is None and not ctx.exit_event.is_set():
                await asyncio.sleep(1)

        # Trying to reconnect to the game after an error
        if ctx.inError or (
                ctx.handler.gameController is None and not ctx.exit_event.is_set()) and ctx.retrievedCustomData:
            if ctx.inError:
                logger.info(f"Connection was lost. Attempting reconnection...")
            ctx.handler.gameController = None
            ctx.loadingDataSetup = True

            asyncio.create_task(ctx.reconnect_to_game())
            await asyncio.sleep(1)

            while ctx.handler.gameController is None and not ctx.exit_event.is_set():
                await asyncio.sleep(1)

        # No connection issues. Start loops.
        if ctx.handler and ctx.handler.gameController:
            ctx.inError = False

            if not ctx.is_game_running:
                ctx.is_game_running = ctx.handler.gameController.check_if_in_game()
                await asyncio.sleep(1)
                continue

            if ctx.loadingDataSetup:
                logger.info(f"Found {SHORT_NAME} process! Now loading...")

                if ctx.options["death_link"]:
                    await ctx.update_death_link(True)
                    ctx.deathlink_enabled = True

                if ctx.options["death_link_trigger"]:
                    ctx.deathlink_trigger = ctx.options["death_link_trigger"]

                if ctx.options["energy_link"]:
                    ctx.energylink_enabled = True
                    if ctx.ui:
                        ctx.ui.enable_energy_link()

                if "energy_link_bullet_money" in ctx.options:
                    ctx.energylink_bulletmoney_enabled = ctx.options["energy_link_bullet_money"]

                asyncio.create_task(ctx.load_save_data())
                ctx.loadingDataSetup = False
                continue

            # Start the different loops.
            loops = []
            loops.append(asyncio.create_task(ctx.main_loop()))
            loops.append(asyncio.create_task(ctx.menu_loop()))
            loops.append(asyncio.create_task(ctx.game_loop()))
            if ctx.deathlink_enabled:
                loops.append(asyncio.create_task(ctx.deathlink_loop()))

            # Infinitely loop if there is no error.
            await asyncio.sleep(0.5)
            # If there is, exit to restart the connection.
            # Stop all loops if possible at this phase.
            if ctx.exit_event.is_set():
                # Save last item index and then quit.
                pass

            if ctx.inError or ctx.exit_event.is_set() or not ctx.server:
                for loop in loops:
                    try:
                        loop.cancel()
                    except:
                        pass


def launch():
    """
    Launch a client instance (wrapper / args parser)
    """

    async def main(args):
        """
        Launch a client instance (threaded)
        """
        ctx = TouhouHBMContext(args.connect, args.password)
        ctx.server_task = asyncio.create_task(server_loop(ctx))
        if gui_enabled: ctx.run_gui()
        ctx.run_cli()
        watcher = asyncio.create_task(
            game_watcher(ctx),
            name="GameProgressionWatcher"
        )
        await ctx.exit_event.wait()
        await watcher
        await ctx.shutdown()

    parser = get_base_parser(description=SHORT_NAME + " Client")
    args, _ = parser.parse_known_args()

    colorama.init()
    asyncio.run(main(args))
    colorama.deinit()
