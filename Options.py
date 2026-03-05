from Options import *
from .variables.boss_and_stage import TUTORIAL_NAME_FULL, STAGE1_NAME_FULL, STAGE2_NAME_FULL, STAGE3_NAME_FULL, STAGE4_NAME_FULL, \
    STAGE5_NAME_FULL, STAGE6_NAME_FULL, ENDSTAGE_NAME_FULL, CHALLENGE_NAME_FULL


class StartingMarket(Choice):
    """
    Choose which stage to have unlocked at the start of the game.

    If Progressive Markets is enabled:
    - Unlock items for stages preceding the Starting Market will not appear.
    - Any stages preceding the Starting Market will be unlocked.
    """

    display_name = "Starting Market"

    option_Tutorial = 0
    option_Stage1 = 1
    option_Stage2 = 2
    option_Stage3 = 3
    option_Stage4 = 4
    option_Stage5 = 5
    option_Stage6 = 6
    option_Stage7 = 7
    option_Challenge = 8

    default = option_Tutorial

    @classmethod
    def get_option_name(cls, value: T) -> str:
        if value == cls.option_Tutorial:
            return TUTORIAL_NAME_FULL
        elif value == cls.option_Stage1:
            return STAGE1_NAME_FULL
        elif value == cls.option_Stage2:
            return STAGE2_NAME_FULL
        elif value == cls.option_Stage3:
            return STAGE3_NAME_FULL
        elif value == cls.option_Stage4:
            return STAGE4_NAME_FULL
        elif value == cls.option_Stage5:
            return STAGE5_NAME_FULL
        elif value == cls.option_Stage6:
            return STAGE6_NAME_FULL
        elif value == cls.option_Stage7:
            return ENDSTAGE_NAME_FULL
        elif value == cls.option_Challenge:
            return CHALLENGE_NAME_FULL
        return super().get_option_name(value)


class ProgressiveStages(DefaultOnToggle):
    """
    Stages will be unlocked in order as the game progresses.
    """

    display_name = "Progressive Markets"


class DisableChallengeLogic(DefaultOnToggle):
    """
    Challenge Market will not count for Market Card Reward locations.
    Does not exclude boss encounters in Challenge Market.
    Disable this option to turn off the above handicap.
    """

    display_name = "Disable Challenge Market in Logic"


class TrapChance(Range):
    """
    Percentage chance that any given filler Item will be replaced by a trap item.
    """

    display_name = "Trap Chance"

    range_start = 0
    range_end = 100
    default = 10


class LowSkillLogic(DefaultOnToggle):
    """
    Whether the generation logic should include certain Ability Cards as compulsory before challenging late-game stages.

    This includes: Life Explosion Elixir, Princess Kaguya's Secret Stash, Soot-covered Uchiwa,
    Esteemed Authority, Gluttonous Centipede, and Money Is The Best Lawyer In Hell.
    """

    display_name = "Recommended Loadout in Logic"


class IncludeGameplayFiller(DefaultOnToggle):
    """
    Whether filler items that are not Funds or Bullet Money will appear during generation.
    Also affects Traps.
    """

    display_name = "Include Non-Money Filler"


class DeathLinkTrigger(Choice):
    """
    Determines when a Death Link would be sent. Only takes effect if Death Link is enabled.
    Can be temporarily changed during gameplay.

    0. Upon losing a life. This means Life Explosion Elixir will also trigger Death Link.
    1. Upon failing a stage attempt. All lives must be lost before this triggers.
    """

    display_name = "Death Link Trigger"

    option_life = 0
    option_stage = 1

    default = option_life

    @classmethod
    def get_option_name(cls, value: T) -> str:
        if value == cls.option_life:
            return "Upon losing a life"
        if value == cls.option_stage:
            return "Upon failing a stage attempt"
        return super().get_option_name(value)

class InvincAgainstDeathLink(DefaultOnToggle):
    """
    Determines whether invincibility can protect against incoming Death Links.
    """

    display_name = "Anti-Death Link Invincibility"


class EnergyLink(Toggle):
    """
    Allows usage of the EnergyLink pool.
    Funds can be deposited and withdrawn at a certain exchange rate.
    However, undeposited and withdrawn Funds will not be automatically saved.
    """

    display_name = "Energy Link"


class EnergyLinkBulletMoney(Toggle):
    """
    If enabled, EnergyLink exchanges permit exchanging energy for Bullet Money as well.
    Conversion rates for Bullet Money differ from that for Funds.
    Bullet Money cannot be deposited nor withdrawn outside of stages.
    """

    display_name = "Energy Link Bullet Money Exchanges"


class MusicRoomChecks(Toggle):
    """
    Whether soundtrack unlocks in the Music Room also counts as checks.
    """

    display_name = "Enable Music Room Checks"


class AchieveChecks(Toggle):
    """
    Whether Achievements also counts as checks.
    """

    display_name = "Enable Achievement Checks"


class CompletionType(Choice):
    """
    A goal to reach.

    1. Full Story Clear - Defeat Chimata Tenkyuu, Nitori Kawashiro, Takane Yamashiro.
    2. Minimum Story Clear - Defeat Takane Yamashiro.
    3. All Ability Cards Owned.
    4. All Bosses Defeated - Challenge Market does not count.
    5. Clear everything.
    """

    display_name = "Completion Goal"

    option_full = 0
    option_min = 1
    option_cards = 2
    option_bosses = 3
    option_all = 4

    default = option_full

    @classmethod
    def get_option_name(cls, value: T) -> str:
        if value == cls.option_full:
            return "Full Story Clear"
        elif value == cls.option_min:
            return "Minimum Story Clear"
        elif value == cls.option_cards:
            return "All Ability Cards Owned"
        elif value == cls.option_bosses:
            return "All Bosses Defeated"
        elif value == cls.option_all:
            return "Clear everything"
        return super().get_option_name(value)


@dataclass()
class TouhouHBMDataclass(PerGameCommonOptions):
    starting_market: StartingMarket
    progressive_stages: ProgressiveStages
    disable_challenge_logic: DisableChallengeLogic
    trap_chance: TrapChance
    low_skill_logic: LowSkillLogic
    include_gameplay_filler: IncludeGameplayFiller
    death_link: DeathLink
    death_link_trigger: DeathLinkTrigger
    death_link_invincibility: InvincAgainstDeathLink
    energy_link: EnergyLink
    energy_link_bullet_money: EnergyLinkBulletMoney
    music_room_checks: MusicRoomChecks
    achievement_checks: AchieveChecks
    completion_type: CompletionType
    start_inventory_from_pool: StartInventoryPool


option_groups = [
    OptionGroup(
        "Game Options",
        [DeathLinkTrigger, InvincAgainstDeathLink, EnergyLink, EnergyLinkBulletMoney]
    ),
    OptionGroup(
        "Generation Options",
        [StartingMarket, ProgressiveStages, MusicRoomChecks, AchieveChecks, DisableChallengeLogic, LowSkillLogic, TrapChance, IncludeGameplayFiller, CompletionType]
    )
]

option_presets = {
    "easy": {
        "starting_market": 0,
        "progressive_stages": True,
        "disable_challenge_logic": True,
        "trap_chance": 0,
        "low_skill_logic": True,
        "include_gameplay_filler": False,
        "death_link": False,
        "death_link_trigger": 0,
        "death_link_invincibility": True,
        "energy_link": False,
        "energy_link_bullet_money": False,
        "music_room_checks": False,
        "achievement_checks": False,
        "completion_type": 0 # Full Main Story
    },
    "normal": {
        "starting_market": 1, # 1st Market
        "progressive_stages": True,
        "disable_challenge_logic": True,
        "trap_chance": 5,
        "low_skill_logic": True,
        "include_gameplay_filler": False,
        "death_link": False,
        "death_link_trigger": 0,
        "death_link_invincibility": True,
        "energy_link": False,
        "energy_link_bullet_money": False,
        "music_room_checks": False,
        "achievement_checks": False,
        "completion_type": 0 # Full Main Story
    },
    "hard": {
        "starting_market": 3, # 3rd Market
        "progressive_stages": True,
        "disable_challenge_logic": True,
        "trap_chance": 10,
        "low_skill_logic": False,
        "include_gameplay_filler": True,
        "death_link": True,
        "death_link_trigger": 1,
        "death_link_invincibility": False,
        "energy_link": False,
        "energy_link_bullet_money": False,
        "music_room_checks": True,
        "achievement_checks": False,
        "completion_type": 1 # Minimum Main Story
    },
    "lunatic": {
        "starting_market": 5, # 5th Market
        "progressive_stages": False,
        "disable_challenge_logic": False,
        "trap_chance": 20,
        "low_skill_logic": False,
        "include_gameplay_filler": True,
        "death_link": True,
        "death_link_trigger": 0,
        "death_link_invincibility": False,
        "energy_link": False,
        "energy_link_bullet_money": False,
        "music_room_checks": True,
        "achievement_checks": False,
        "completion_type": 3 # All Bosses Defeated
    },
    "overdrive": {
        "starting_market": 8, # Challenge Market
        "progressive_stages": False,
        "disable_challenge_logic": False,
        "trap_chance": 50,
        "low_skill_logic": False,
        "include_gameplay_filler": True,
        "death_link": True,
        "death_link_trigger": 0,
        "death_link_invincibility": False,
        "energy_link": False,
        "energy_link_bullet_money": False,
        "music_room_checks": True,
        "achievement_checks": True,
        "completion_type": 4 # Full Clear
    }
}
