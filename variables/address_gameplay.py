"""
Variables: Memory addresses used during stage gameplay.
"""
# Combine the below with the base game address.

# All of the below uses 4-byte decimals.
# These are offsets to a static base address.
# Read from them as is to get their values.
ADDR_CURRENT_STAGE_PTR = 0x000D7B0C # If pointer is valid, game is in stage. If not, game is not.
ADDR_GAME_FUNDS_PTR = 0x000D106C
ADDR_BULLET_MONEY_PTR = 0x000D1074
ADDR_BULLET_MONEY_2_PTR = 0x000D1070
ADDR_LIVES_PTR = 0x000D10BC
ADDR_ANTICHEAT_HACK = 0x000744A6 # NOP opcodes should be used.
ADDR_ALERT_POPUP_PTR = 0x0004819f # Set this to FF.
ADDR_ALERT_POPUP_FUNC = 0x000481a7 # Set this to 90, 90, 90, 90, 90.
ADDR_BLACK_MARKET_PTR = 0x000D7AC4 # If does not return 0, Black Market is open.

# This is mainly for menu cursor stuff. Override in order from 1-7.
# Address of the line that sets the cursor in the menu to Stage #.
ADDR_STAGE_CURSOR_STATIC = 0x000CDCAC # Set this when first loading into the game.
ADDR_CURSOR_SET_STAGE1 = 0x0004a3e8 + 6 # 1
ADDR_CURSOR_SET_STAGE2 = 0x0004a42a + 6 # 2
ADDR_CURSOR_SET_STAGE3 = 0x0004a4ae + 6 # 3
ADDR_CURSOR_SET_STAGE4 = 0x0004a532 + 6 # 4
ADDR_CURSOR_SET_STAGE5 = 0x0004a5b6 + 6 # 5
ADDR_CURSOR_SET_STAGE6 = 0x0004a64b + 6 # 6
ADDR_CURSOR_SET_CHIMATA = 0x0004a6cf + 6 # 7
ADDR_CURSOR_SET_CHALLENGE = 0x0004a73e + 6 # 7

# These are specifically for invincibility. Both fields must be changed at the same time
ADDR_GAMEPLAY_BASE_PTR = 0X000D7C3C
ADDR_INVINC_OFFSET_INT = 0X00048078 # Use 4-byte integers.
ADDR_INVINC_OFFSET_FLOAT = 0X0004807C # Use floats.
# Death Link stuff. 1-byte.
# 0x00 - Respawning from death. Clears bullets. Not recommended to set to.
# 0x01 - Normal.
# 0x02 - Player disappears from screen and returns to screen. Changes to 0x00 quickly after that.
# 0x04 - Kill the player on the spot. No sounds.
ADDR_PLAYER_STATUS_OFFSET = 0x00047FAC

# All of the below uses 2-bytes.
# All of them max out at 1000.
ADDR_SHOT_ATTACK = 0x000D1088
ADDR_CIRCLE_ATTACK = 0x000D108C
ADDR_CIRCLE_SIZE = 0x000D1090
ADDR_CIRCLE_DURATION = 0x000D1098
ADDR_CIRCLE_GRAZE_RANGE = 0x000D10A0
ADDR_MOVEMENT_SPEED = 0x000D10AC