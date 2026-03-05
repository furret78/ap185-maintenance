from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld
from .Options import option_groups, option_presets
from .variables.meta_data import DISPLAY_NAME


class TouhouHBMWebWorld(WebWorld):
    game = DISPLAY_NAME
    theme = "partyTime"

    setup_en = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up 100th Black Market for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Yuureiki"]
    )]

    tutorials = [setup_en]

    option_groups = option_groups
    options_presets = option_presets