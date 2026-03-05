import random
import sys

from . import MAX_BULLET_MONEY
from .GameController import GameController
from .Tools import clamp, get_boss_and_stage_id
from .variables.card_const import *

class GameHandler:
    """Class keeping tracking of what's unlocked and handles game interactions."""
    game_funds: int = 0
    menu_funds: int = 0
    end_stage_card_chosen: dict = {}
    permashop_card_new: list = []
    permashop_card: dict = {}
    dex_card_unlocked: dict = {}
    gameController = None
    bosses_beaten: dict = {}
    bosses_met: dict = {}
    stages_unlocked: dict = {}
    previous_location_checked: list = []

    def __init__(self):
        self.gameController = GameController()
        self.reset()
        self.initGame()

    # Init Resources
    def reconnect(self):
        self.gameController = GameController()
        self.initGame()

    def reset(self):
        """
        Initialize everything to defaults.
        """
        self.spare_lives = 0
        self.game_funds = 0
        self.menu_funds = 0
        self.end_stage_card_chosen = {}
        self.permashop_card_new = []
        self.permashop_card = {}
        self.dex_card_unlocked = {}
        self.gameController = None
        self.bosses_beaten = {}
        self.bosses_met = {}
        self.stages_unlocked = {}
        self.previous_location_checked = []

        for i in ABILITY_CARD_LIST:
            self.dex_card_unlocked[i] = False
            if i != NAZRIN_CARD_1 and i != NAZRIN_CARD_2:
                self.end_stage_card_chosen[i] = False
                self.permashop_card[i] = False

        self.bosses_beaten = {
            TUTORIAL_ID: {BOSS_MIKE: False},
            STAGE1_ID: {BOSS_MIKE: False, BOSS_MINORIKO: False, BOSS_ETERNITY: False, BOSS_NEMUNO: False},
            STAGE2_ID: {BOSS_CIRNO: False, BOSS_WAKASAGI: False, BOSS_SEKIBANKI: False, BOSS_URUMI: False},
            STAGE3_ID: {BOSS_EBISU: False, BOSS_KUTAKA: False, BOSS_NARUMI: False, BOSS_KOMACHI: False},
            STAGE4_ID: {BOSS_SANAE: False, BOSS_SAKUYA: False, BOSS_YOUMU: False, BOSS_REIMU: False, BOSS_NITORI: False},
            STAGE5_ID: {BOSS_TSUKASA: False, BOSS_MEGUMU: False, BOSS_CLOWNPIECE: False, BOSS_TENSHI: False},
            STAGE6_ID: {BOSS_SUIKA: False, BOSS_MAMIZOU: False, BOSS_SAKI: False, BOSS_MOMOYO: False, BOSS_TAKANE: False},
            STAGE_CHIMATA_ID: {BOSS_CHIMATA: False},
        }

        self.bosses_met = self.bosses_beaten
        self.bosses_met[STAGE_CHALLENGE_ID] = {
                BOSS_MIKE: False, BOSS_MINORIKO: False, BOSS_ETERNITY: False, BOSS_NEMUNO: False,
                BOSS_CIRNO: False, BOSS_WAKASAGI: False, BOSS_SEKIBANKI: False, BOSS_URUMI: False,
                BOSS_EBISU: False, BOSS_KUTAKA: False, BOSS_NARUMI: False, BOSS_KOMACHI: False,
                BOSS_SANAE: False, BOSS_SAKUYA: False, BOSS_YOUMU: False, BOSS_REIMU: False,
                BOSS_TSUKASA: False, BOSS_MEGUMU: False, BOSS_CLOWNPIECE: False, BOSS_TENSHI: False,
                BOSS_SUIKA: False, BOSS_MAMIZOU: False, BOSS_SAKI: False, BOSS_MOMOYO: False
            }

        for stage_name in STAGE_LIST:
            self.stages_unlocked[stage_name] = False

    def initGame(self):
        if self.gameController is None: return
        self.gameController.initGamePrep()

    # Get Handler functions
    def isGameInStage(self):
        """Check if the game is currently in any stage. Returns True if yes."""
        return self.gameController.check_if_in_stage()

    def isBlackMarketOpen(self) -> bool:
        return self.gameController.check_if_black_market()

    def getGameFunds(self) -> int:
        return self.gameController.getGameFunds()

    def setMenuFunds(self, value: int):
        """
        Forcibly sets the menu funds to this amount.
        Only for initial save data loading.
        """
        self.menu_funds = value
        self.gameController.setMenuFunds(value)

    def getBulletMoney(self) -> int:
        return self.gameController.getBulletMoney()

    def getShopCardData(self, card_string_id: str) -> int:
        """
        0x00 = Not unlocked (0)
        0x01 - 0x79 = Unlocked but not new (1)
        0x80 - ??? = Unlocked and new (2)
        """
        bytes_read: bytes = self.gameController.getShopCardData(card_string_id)
        if bytes_read == bytes([0x00]): return 0
        decoded_bytes = int.from_bytes(bytes_read, sys.byteorder, signed=False)
        if decoded_bytes < 0x80: return 1
        else: return 2

    def setShopCardData(self, card_string_id: str, value: bytes):
        """
        Must use bytes. ( bytes([value_here]) )
        """
        self.gameController.setShopCardData(card_string_id, value)

    def getDexCardData(self, card_string_id: str) -> bool:
        """
        Gets whether a card is unlocked in the dex or not.
        This checks if the value is not 0x00. If True, the card has been unlocked in-game.
        """
        return self.gameController.getDexCardData(card_string_id)

    def setDexCardData(self, card_string_id: str, value: bool):
        """
        Writes data to the memory for this particular Ability Card in the dex.
        This one is for loading in the dex when reconnecting to the server.
        """
        final_bytes = bytes([0x00])
        if value: final_bytes = bytes([0x01])

        self.gameController.setDexCardData(card_string_id, final_bytes)
        self.dex_card_unlocked[card_string_id] = value

    def getDexCardDataHandler(self, card_string_id: str) -> int:
        return self.dex_card_unlocked[card_string_id]

    # Received Item functions
    def addLife(self, value: int = 1):
        if value == 0: return
        currentLives = self.gameController.getLives()
        #if currentLives == 11: self.spare_lives += value
        newLives = clamp(currentLives + value, 0, 11)
        self.gameController.setLives(newLives)

    def addGameFunds(self, value: int):
        if value == 0: return
        self.gameController.addGameFunds(value)

    def addMenuFunds(self, value: int):
        if value == 0: return
        self.gameController.addMenuFunds(value)

    def getMenuFunds(self) -> int:
        return self.gameController.getMenuFunds()

    def addBulletMoney(self, value: int):
        if value == 0: return
        self.gameController.addBulletMoney(value)

    def addEquipCost(self, value: int):
        newEquipCost = clamp(self.getEquipCost() + value, 100, MAX_BULLET_MONEY)
        self.gameController.setEquipCost(newEquipCost)

    # Stage functions
    def updateStageList(self):
        """
        Updates the unlock state of stages.
        Since there are no checks to scan for these, this is primarily to sync the game with the handler.
        """
        for stage in STAGE_LIST:
            unlockStatus = self.gameController.getStageStatus(STAGE_NAME_TO_ID[stage])

            if unlockStatus == 0x00 and self.stages_unlocked[stage] == True:
                self.gameController.setStageStatus(STAGE_NAME_TO_ID[stage], 0x01)
            if unlockStatus == 0x01 and self.stages_unlocked[stage] == False:
                self.gameController.setStageStatus(STAGE_NAME_TO_ID[stage], 0x00)

    def setLoadMenuIndex(self, starting_market: int):
        self.gameController.setStageCursorIndex(clamp(starting_market + 1, 1, 9))

    def getLastStageIndex(self) -> int:
        """
        If this returns 0, the player hasn't even started anything yet.
        """
        return self.gameController.getLastStageIndex()

    # Other functions
    def getBossRecordHandler(self, stage_id: int, boss_id: int, type: int = 0):
        """
        Gets the stats of a boss in a specific stage from the handler.
        Type 0 is checking for encounters, and type 1 is checking for defeat.
        Challenge Market skips the type check and always returns the encounter value.
        """
        if stage_id == STAGE_CHALLENGE_ID:
            return self.bosses_met[STAGE_CHALLENGE_ID][boss_id]

        match type:
            case 0: # Encounters
                return self.bosses_met[stage_id][boss_id]
            case 1: # Defeat
                return self.bosses_beaten[stage_id][boss_id]
            case _: return False

    def setBossRecordHandler(self, stage_id: int, boss_id: int, value: bool, type: int = 0) -> None:
        """
        Sets the stats of a boss in a specific stage in the handler's data.
        Type 0 is for encounters, type 1 for defeat.
        Challenge Market exclusively has encounter stats.
        """
        if stage_id == STAGE_CHALLENGE_ID:
            self.bosses_met[STAGE_CHALLENGE_ID][boss_id] = value

        match type:
            case 0: self.bosses_met[stage_id][boss_id] = value
            case 1: self.bosses_beaten[stage_id][boss_id] = value

    def getBossRecordGame(self, stage_id: int, boss_id: int, type: int = 0) -> bool:
        """
        Gets the stats of a boss in a specific stage from the game itself.
        Type 0 is checking for encounters, and type 1 is checking for defeat.
        Challenge Market only stores data for boss defeats of the Final Wave.
        The Final Wave consists of Stage 6 bosses.
        """
        if type == DEFEAT_ID:
            hidden_records = get_boss_and_stage_id(stage_id, boss_id)
            return self.gameController.getHiddenBossDefeat(hidden_records[0], hidden_records[1])
        else: return self.gameController.getBossRecord(stage_id, boss_id, type)

    def setBossRecordGame(self, stage_id: int, boss_id: int, value: bool, record_type: int = 0) -> None:
        """
        Sets the stats of a boss in a specific stage in the game memory itself.
        Type 0 is for encounters, type 1 is for defeat.
        Challenge Market exclusively has encounter stats.
        """
        final_value: int = 0
        if value: final_value = random.randint(1, 255)
        self.gameController.setBossRecord(stage_id, boss_id, final_value, record_type)

        # This part is mainly so that the achievements for stage-exclusive bosses work properly.
        # The all-bosses achievement doesn't do this.
        if record_type != DEFEAT_ID: return
        hidden_records = get_boss_and_stage_id(stage_id, boss_id)
        self.gameController.setHiddenBossDefeat(hidden_records[0], hidden_records[1], final_value)

    def unlockNoCard(self):
        """
        Backup function that forces the No Card option to be available,
        even if the score file disables it somehow.
        """
        self.gameController.setNoCardData()

    def unconditionalDexUnlock(self, card_string_id: str):
        """
        Function specifically for unlocking Starting Cards and/or save data loading.
        Technically this can unlock every other dex entry, but that will break locations.
        """
        self.dex_card_unlocked[card_string_id] = True
        self.gameController.setDexCardData(card_string_id, bytes([0x01]))

    def unlockCardInMenuShop(self, card_string_id: str):
        """
        Function for unlocking cards in menu shop.
        The function that actually touches memory is elsewhere.
        """
        self.permashop_card[card_string_id] = True
        self.permashop_card_new.append(card_string_id)
        self.unlockCardInMenuShop_Memory(card_string_id)

    def unlockCardInMenuShop_Memory(self, card_string_id: str):
        """
        Function that actually changes game memory to show card shop unlocks.
        If the game is currently not in the menu, this function cancels itself.
        """
        if self.isGameInStage(): return
        final_value = 0x00
        if self.permashop_card[card_string_id]:
            final_value = 0x01
        if card_string_id in self.permashop_card_new:
            final_value = 0x81

        self.setShopCardData(card_string_id, bytes([final_value]))

    def getCardShopRecordHandler(self, card_string_id: str):
        return self.permashop_card[card_string_id]

    def setCardShopRecordHandler(self, card_string_id: str, value: bool):
        self.permashop_card[card_string_id] = value

    def getCardShopRecordGame(self, card_string_id: str) -> int:
        return self.getShopCardData(card_string_id)

    def setCardShopRecordGame(self, card_string_id: str, value: bool):
        """
        Updates the game memory to align with the Permanent Card Shop records.
        """
        if value:
            final_value = 0x01
            if card_string_id in self.permashop_card_new:
                final_value = 0x80

            self.setShopCardData(card_string_id, bytes([final_value]))
        else:
            self.setShopCardData(card_string_id, bytes([0x00]))

    def getCardSlots(self) -> int:
        return self.gameController.getCardSlots()

    def setCardSlots(self, value: int):
        self.gameController.setCardSlots(value)

    def getEquipCost(self) -> int:
        return self.gameController.getEquipCost()

    def setEquipCost(self, value: int):
        self.gameController.setEquipCost(value)

    # Music Room and Achievements
    def getMusicRecord(self, track_id: int) -> bool:
        sanitized_track_id = clamp(track_id, 0, 9)
        return self.gameController.getMusicRecordData(sanitized_track_id)

    def setMusicRecord(self, track_id: int, value: bool):
        sanitized_track_id = clamp(track_id, 0, 9)
        final_bytes = bytes([0x00])
        if value: final_bytes = bytes([0x01])

        self.gameController.setMusicRecordData(sanitized_track_id, final_bytes)

    def getAchievementStatus(self, achievement_id: int) -> bool:
        sanitized_achieve_id = clamp(achievement_id, 0, 11)
        return self.gameController.getAchieveData(sanitized_achieve_id)

    def setAchievementStatus(self, achievement_id: int, value: bool):
        sanitized_achieve_id = clamp(achievement_id, 0, 11)
        final_bytes = bytes([0x00])
        if value: final_bytes = bytes([0x01])

        self.gameController.setAchieveData(sanitized_achieve_id, final_bytes)

    # Death Link functionalities
    # If True, the player died and has just teleported below the screen in order to recover.
    # Does not check if the player is not in a stage.
    def checkForPlayerDeath(self) -> bool:
        bytes_read = self.gameController.checkForPlayerState()
        return bytes_read == bytes([0x02]) or bytes_read == bytes([0x04])

    # If True, the player's state is Normal.
    def checkForPlayerNormal(self) -> bool:
        return self.gameController.checkForPlayerState() == bytes([0x01])

    # Returns True if the player is invincible.
    def checkInvincibility(self) -> bool:
        return self.gameController.getInvincibility() > 0

    def killPlayer(self):
        self.gameController.setPlayerDeath()