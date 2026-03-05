import pymem
import pymem.exception

from .Tools import *
from .variables.card_const import *
from .variables.meta_data import *
from .variables.address_gameplay import *
from .variables.boss_and_stage import *

class GameController:
    """Class accessing the game's memory."""

    # I honestly have no idea why it's written this way.
    # I consider the implementation of memory editing the game below magic.
    # The helper function that gets addresses from pointers I also consider to be magic.
    # But it works so I don't really care.
    def __init__(self):
        self.pm = pymem.Pymem(process_name=FILE_NAME)

        # Gameplay only.
        # Read straight from them as is to get the value.
        self.addrCurrentStage = self.pm.base_address+ADDR_CURRENT_STAGE_PTR # Check if pointer itself is valid.
        self.addrGameFunds = self.pm.base_address+ADDR_GAME_FUNDS_PTR
        self.addrBulletMoney = self.pm.base_address+ADDR_BULLET_MONEY_PTR
        self.addrLives = self.pm.base_address+ADDR_LIVES_PTR
        self.addrBlackMarketStatus = self.pm.base_address+ADDR_BLACK_MARKET_PTR

        self.addrShotAttack = self.pm.base_address+ADDR_SHOT_ATTACK
        self.addrMagicCircleAttack = self.pm.base_address+ADDR_CIRCLE_ATTACK
        self.addrMagicCircleSize = self.pm.base_address+ADDR_CIRCLE_SIZE
        self.addrMagicCircleDuration = self.pm.base_address+ADDR_CIRCLE_DURATION
        self.addrMagicCircleGraze = self.pm.base_address+ADDR_CIRCLE_GRAZE_RANGE
        self.addrMoveSpeed = self.pm.base_address+ADDR_MOVEMENT_SPEED

        # Menu and record-keeping.
        # These use pointers.
        self.addrMenuFunds = self.getAddressFromPointerWithBase(ADDR_MENU_FUNDS_PTR)

    # Helper function
    def getAddressFromPointerWithBase(self, offset):
        """
        Helper function. Essentially just tacks the static base address for the menu onto getAddressFromPointer.
        """
        static_base_pointer = self.pm.base_address + ADDR_BASE_MENU_PTR
        return getPointerAddress(self.pm, static_base_pointer, [offset])

    def getAddressFromPointerCustomBase(self, base, offset):
        static_base_pointer = self.pm.base_address + base
        return getPointerAddress(self.pm, static_base_pointer, [offset])

    def check_if_in_stage(self) -> bool:
        """
        Returns True if in a stage.
        """
        return int.from_bytes(self.pm.read_bytes(self.pm.base_address + ADDR_CURRENT_STAGE_PTR, 2)) != 0

    def check_if_in_game(self):
        """
        Returns True if the game is open and not the window resolution selection dialogue box.
        """
        try:
            card_slot = self.pm.read_int(self.getAddressFromPointerWithBase(ADDR_EQUIP_SLOT_COUNT))
            if card_slot <= 0: return False
        except Exception as e:
            return False
        # If this does not raise an exception, the game is running.
        return True

    def check_if_black_market(self) -> bool:
        """
        Returns True if a Black Market is open in a stage.
        """
        try:
            black_market_int = self.pm.read_int(self.addrBlackMarketStatus)
        except Exception as e:
            return False

        return black_market_int != 0

    # Gameplay.
    # Lives (in-game) functions
    def getLives(self) -> int:
        return self.pm.read_int(self.addrLives)

    def setLives(self, value):
        self.pm.write_int(self.addrLives, clamp(value, 0, 7))

    # Funds (in-game) functions
    def getGameFunds(self) -> int:
        return self.pm.read_int(self.addrGameFunds)

    def setGameFunds(self, value):
        self.pm.write_int(self.addrGameFunds, value)

    def addGameFunds(self, value):
        newGameFunds = clamp(self.pm.read_int(self.addrGameFunds) + value, 0, MAX_FUNDS)
        self.pm.write_int(self.addrGameFunds, newGameFunds)

    # Bullet Money (in-game) functions
    def getBulletMoney(self) -> int:
        return self.pm.read_uint(self.addrBulletMoney)

    def setBulletMoney(self, value):
        self.pm.write_uint(self.addrBulletMoney, value)

    def addBulletMoney(self, value):
        oldBulletMoney = self.pm.read_int(self.addrBulletMoney)
        newBulletMoney = clamp(oldBulletMoney + value, 0, MAX_BULLET_MONEY)
        self.pm.write_uint(self.addrBulletMoney, newBulletMoney)

    # More gameplay only changes
    # Invincibility
    def addInvincibility(self, value):
        addrInvincInt = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_INVINC_OFFSET_INT)
        addrInvincFloat = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_INVINC_OFFSET_FLOAT)

        newValue: int = self.pm.read_int(addrInvincInt) + value

        self.pm.write_int(addrInvincInt, newValue)
        self.pm.write_float(addrInvincFloat, float(newValue))

    def clearInvincibility(self):
        addrInvincInt = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_INVINC_OFFSET_INT)
        addrInvincFloat = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_INVINC_OFFSET_FLOAT)

        self.pm.write_int(addrInvincInt, 0)
        self.pm.write_float(addrInvincFloat, 0.0)

    def getInvincibility(self) -> int:
        addrInvincInt = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_INVINC_OFFSET_INT)
        return self.pm.read_int(addrInvincInt)

    # Shot Attack %
    def addShotAttack(self, value):
        newValue = clamp(self.pm.read_short(self.addrShotAttack) + value, 0, 1000)
        self.pm.write_short(self.addrShotAttack, newValue)

    # Magic Circle Attack %
    def addMagicCircleAttack(self, value):
        newValue = clamp(self.pm.read_short(self.addrMagicCircleAttack) + value, 0, 1000)
        self.pm.write_short(self.addrMagicCircleAttack, newValue)

    # Magic Circle Size %
    def addMagicCircleSize(self, value):
        newValue = clamp(self.pm.read_short(self.addrMagicCircleSize) + value, 0, 1000)
        self.pm.write_short(self.addrMagicCircleSize, newValue)

    # Magic Circle Duration %
    def addMagicCircleDuration(self, value):
        newValue = clamp(self.pm.read_short(self.addrMagicCircleDuration) + value, 0, 1000)
        self.pm.write_short(self.addrMagicCircleDuration, newValue)

    # Magic Circle Graze Range %
    def addMagicCircleGraze(self, value):
        newValue = clamp(self.pm.read_short(self.addrMagicCircleGraze) + value, 0, 1000)
        self.pm.write_short(self.addrMagicCircleGraze, newValue)

    # Movement Speed %
    def addSpeed(self, value):
        newValue = clamp(self.pm.read_short(self.addrMoveSpeed) + value, 0, 1000)
        self.pm.write_short(self.addrMoveSpeed, newValue)

    # Recordkeeping starts here.
    # Funds (menu) functions
    def getMenuFunds(self) -> int:
        self.addrMenuFunds = self.getAddressFromPointerWithBase(ADDR_MENU_FUNDS_PTR)
        return self.pm.read_int(self.addrMenuFunds)

    def setMenuFunds(self, value):
        self.addrMenuFunds = self.getAddressFromPointerWithBase(ADDR_MENU_FUNDS_PTR)
        self.pm.write_int(self.addrMenuFunds, value)

    def addMenuFunds(self, value):
        self.addrMenuFunds = self.getAddressFromPointerWithBase(ADDR_MENU_FUNDS_PTR)
        oldFunds = self.pm.read_int(self.addrMenuFunds)
        newFunds = clamp(oldFunds + value, 0, MAX_FUNDS)
        self.pm.write_int(self.addrMenuFunds, newFunds)

    # Loadout Ability Card Slots functions
    def getCardSlots(self) -> int:
        addrCardSlot = self.getAddressFromPointerWithBase(ADDR_EQUIP_SLOT_COUNT)
        return clamp(self.pm.read_int(addrCardSlot), 1, 34)

    def setCardSlots(self, value: int):
        addrCardSlot = self.getAddressFromPointerWithBase(ADDR_EQUIP_SLOT_COUNT)
        self.pm.write_int(addrCardSlot, clamp(value, 1, 34))

    # Equipment Cost functions
    def getEquipCost(self) -> int:
        addrEquipCost = self.getAddressFromPointerWithBase(ADDR_EQUIP_COST)
        retrievedCost = self.pm.read_int(addrEquipCost)
        if retrievedCost < 100: return 100
        return retrievedCost

    def setEquipCost(self, value: int):
        addrEquipCost = self.getAddressFromPointerWithBase(ADDR_EQUIP_COST)

        final_value: int = value
        if value < 100: final_value = 100

        self.pm.write_int(addrEquipCost, final_value)

    # Stage lock functions
    def getStageStatus(self, stage_id: int) -> bool:
        stageLockAddress = self.getAddressFromPointerWithBase(ADDR_STAGE_ID_TO_PTR[stage_id])
        return bool.from_bytes(self.pm.read_bytes(stageLockAddress, 1))

    def setStageStatus(self, stage_id: int, value: int):
        stageLockAddress = self.getAddressFromPointerWithBase(ADDR_STAGE_ID_TO_PTR[stage_id])
        self.pm.write_bytes(stageLockAddress, bytes([value]), 1)

    # Functions that control boss records
    def getBossRecord(self, stage: int, boss: int, category: int) -> bool:
        boss_address_list_normal = ADDR_BOSS_ID_TO_PTR[stage][boss]

        if stage != STAGE_CHALLENGE_ID:
            bossRecordAddress = self.getAddressFromPointerWithBase(boss_address_list_normal[category])
        else:
            bossRecordAddress = self.getAddressFromPointerWithBase(ADDR_BOSS_ID_TO_PTR[stage][boss])
        return self.pm.read_bytes(bossRecordAddress, 1) != bytes([0x00])

    def setBossRecord(self, stage: int, boss: int, value: int, category: int):
        if stage != STAGE_CHALLENGE_ID:
            bossRecordAddress = self.getAddressFromPointerWithBase(ADDR_BOSS_ID_TO_PTR[stage][boss][category])
        else:
            bossRecordAddress = self.getAddressFromPointerWithBase(ADDR_BOSS_ID_TO_PTR[stage][boss])
        self.pm.write_bytes(bossRecordAddress, bytes([value]), 1)

    def getHiddenBossDefeat(self, stage: int, boss: int) -> bool:
        """
        Retrieves the hidden boss defeat records from the game.
        This can keep track of Challenge Market defeats as well, but only for the bosses on the Final Wave.
        The game never saves defeat records for non-Final Wave bosses.
        """
        finalOffset = OFFSET_HIDDEN_DEFEAT_STAT + (stage * OFFSET_MULT_STAGE_STAT) + boss
        addrHiddenBossRecord = self.getAddressFromPointerWithBase(finalOffset)
        return self.pm.read_bytes(addrHiddenBossRecord, 1) != bytes([0x00])

    def setHiddenBossDefeat(self, stage: int, boss: int, value: int):
        """
        Sets the hidden boss stats that the achievements and 4th boss unlocks use.
        Arguments here won't be sanitized when executed. Sanitize before calling this function.
        Check address_menu.py in variables on how it should be sanitized.
        """
        finalOffset = OFFSET_HIDDEN_DEFEAT_STAT + (stage * OFFSET_MULT_STAGE_STAT) + boss
        addrHiddenBossRecord = self.getAddressFromPointerWithBase(finalOffset)
        self.pm.write_bytes(addrHiddenBossRecord, bytes([value]), 1)

    # Card Shop functions
    def getShopCardData(self, card_id: str) -> bytes:
        if card_id == NAZRIN_CARD_1 or card_id == NAZRIN_CARD_2: return bytes([0x00])
        addrFromCardShop = self.getAddressFromPointerWithBase(ADDR_CARD_TO_SHOP[card_id])
        return self.pm.read_bytes(addrFromCardShop, 1)

    def setShopCardData(self, card_id: str, value: bytes):
        addrFromCardShop = self.getAddressFromPointerWithBase(ADDR_CARD_TO_SHOP[card_id])
        self.pm.write_bytes(addrFromCardShop, value, 1)

    # Card Dex functions
    def getDexCardData(self, card_id: str) -> bool:
        addrFromCardDex = self.getAddressFromPointerWithBase(ADDR_CARD_TO_DEX[card_id])
        return self.pm.read_bytes(addrFromCardDex, 1) != bytes([0x00])

    def setDexCardData(self, card_id: str, value: bytes):
        addrFromCardDex = self.getAddressFromPointerWithBase(ADDR_CARD_TO_DEX[card_id])
        self.pm.write_bytes(addrFromCardDex, value, 1)

    # Music Room functions
    def getMusicRecordData(self, track_id: int) -> bool:
        addrFromMusicRoom = self.getAddressFromPointerWithBase(ADDR_MUSIC_ROOM_OFFSET + track_id)
        return self.pm.read_bytes(addrFromMusicRoom, 1) != bytes([0x00])

    def setMusicRecordData(self, track_id: int, value: bytes):
        addrFromMusicRoom = self.getAddressFromPointerWithBase(ADDR_MUSIC_ROOM_OFFSET + track_id)
        self.pm.write_bytes(addrFromMusicRoom, value, 1)

    # Achievement functions
    def getAchieveData(self, achievement_id: int) -> bool:
        addrFromAchievement = self.getAddressFromPointerWithBase(ADDR_ACHIEVEMENT_OFFSET + achievement_id)
        return self.pm.read_bytes(addrFromAchievement, 1) != bytes([0x00])

    def setAchieveData(self, achievement_id: int, value: bytes):
        addrFromAchievement = self.getAddressFromPointerWithBase(ADDR_ACHIEVEMENT_OFFSET + achievement_id)
        self.pm.write_bytes(addrFromAchievement, value, 1)

    # Stage Select cursor functions
    def setStageCursorIndex(self, stage_id: int) -> None:
        self.pm.write_int(self.pm.base_address + ADDR_STAGE_CURSOR_STATIC, stage_id)

    # Things to do on boot-up before anything else.
    def initGamePrep(self):
        # Disable the anti-cheat.
        self.pm.write_bytes(self.pm.base_address + ADDR_ANTICHEAT_HACK, bytes([0x90, 0x90]), 2)
        # Disable the annoying stage unlock alerts.
        self.pm.write_bytes(self.pm.base_address + ADDR_ALERT_POPUP_PTR, bytes([0x90, 0x90]), 2)
        self.pm.write_bytes(self.pm.base_address + ADDR_ALERT_POPUP_FUNC, bytes([0x90, 0x90, 0x90, 0x90, 0x90]), 5)
        # Disable cursor jumping to the next stage on the list whenever finishing a run.
        # There's 8 lines to modify, from 1 to 7.
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_STAGE1, bytes([0x01]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_STAGE2, bytes([0x02]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_STAGE3, bytes([0x03]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_STAGE4, bytes([0x04]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_STAGE5, bytes([0x05]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_STAGE6, bytes([0x06]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_CHIMATA, bytes([0x07]), 1)
        self.pm.write_bytes(self.pm.base_address + ADDR_CURSOR_SET_CHALLENGE, bytes([0x07]), 1)
        # Forcibly unlock the option to equip no cards at all.
        self.setNoCardData()

    def setNoCardData(self):
        addrFromCardDex = self.getAddressFromPointerWithBase(ADDR_DEX_NO_CARD)
        self.pm.write_bytes(addrFromCardDex, bytes([0x01]), 1)

    # Check if the player's state.
    # Does not check if the player is in a stage or if the player is at the end of a stage.
    def checkForPlayerState(self) -> bytes:
        addrPlayerState = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_PLAYER_STATUS_OFFSET)
        return self.pm.read_bytes(addrPlayerState, 1)

    # Kills the player, complete with animations.
    # Plays no sound this way.
    def setPlayerDeath(self):
        addrPlayerState = self.getAddressFromPointerCustomBase(ADDR_GAMEPLAY_BASE_PTR, ADDR_PLAYER_STATUS_OFFSET)
        self.pm.write_bytes(addrPlayerState, bytes([0x04]), 1)