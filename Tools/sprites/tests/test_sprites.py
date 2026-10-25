"""Checks the generated art against docs/sprite-spec.md and against the game's content files."""
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

TOOL = Path(__file__).resolve().parents[1]
ROOT = TOOL.parents[1]
sys.path.insert(0, str(TOOL))

import build  # noqa: E402
import export  # noqa: E402

# sprite -> (size, {animation: frames}). Mirrors docs/sprite-spec.md; change both together.
SPEC = {
    # Fluffy, cut from the user's painting (characters/hero_painted.py), 3x PNGs; stop, not painted, borrows idle's
    # frames, and a few rows leave out a winking or dusty cat.
    # The code-drawn hero (`hero.drawn_hero`: run 8, stop 4, idle 4, jump 2, fall 2, double 4, throw 4, dash 4,
    # pounce 4, hurt 2, death 6, peek 4, cheer 4, sit_happy 4, ko 2, ghost 4, menu 4) is not exported; it is the
    # model the code-drawn skins match (`test_hero_skins_match_the_hero`).
    "hero": ((44, 36), {"run": 8, "stop": 4, "idle": 6, "jump": 3, "fall": 6, "double": 6, "throw": 6, "dash": 6,
                        "pounce": 4, "hurt": 4, "death": 4, "peek": 4, "cheer": 4, "sit_happy": 4, "ko": 4,
                        "ghost": 5, "menu": 4}),
    "hero_sakura": ((44, 36), {"run": 9, "stop": 8, "idle": 6, "jump": 5, "fall": 6, "double": 8, "throw": 9,
                               "dash": 7, "pounce": 8, "hurt": 4, "death": 9, "peek": 7, "cheer": 7, "sit_happy": 8,
                               "ko": 4, "ghost": 8, "menu": 6}),
    "yarn": ((12, 12), {"fly": 4, "impact": 5}),
    # World 1, forest
    # Cut from the user's painting (characters/squirrel_painted.py), 3x PNGs; every painted frame of WALK and DEATH
    # (the spear lying past the frame in DEATH 1-3 cut off in front of the face).
    "squirrel": ((36, 36), {"walk": 4, "death": 4}),
    "acorn": ((14, 14), {"roll": 4, "death": 4}),
    # Cut from the user's painting (characters/branch_squirrel_painted.py), 3x PNGs; every painted frame of IDLE, THROW
    # and DEATH (the acorn dropping under DEATH 4 cleared), the branch painted under it in each; the thrown acorn is the
    # first DROP ACORN (motion lines cut off) turned a quarter turn a frame.
    "branch_squirrel": ((40, 40), {"idle": 4, "throw": 4, "death": 4}),
    "acorn_thrown": ((14, 14), {"fly": 4}),
    # Cut from the user's painting (characters/hedgehog_painted.py), 3x PNGs; curl and rolled from its ROLL row (the
    # fourth ball, its face turned back, left out).
    "hedgehog": ((36, 28), {"walk": 4, "curl": 2, "rolled": 3, "death": 5}),
    "slime": ((30, 24), {"walk": 4, "death": 4}),
    "mushroom_cat": ((34, 34), {"idle": 2, "throw": 4, "death": 4}),
    "spore": ((10, 10), {"fly": 4}),
    "forest_bat": ((46, 32), {"fly": 4, "death": 3}),
    "plant_cat": ((40, 42), {"idle": 2, "warn": 2, "bite": 3, "death": 4}),
    "bee_cat": ((38, 30), {"fly": 4, "throw": 3, "death": 4}),
    "sting": ((12, 6), {"fly": 4}),
    "stump_cat": ((34, 38), {"idle": 2, "throw": 3, "death": 4}),
    "leaf": ((10, 8), {"fly": 4}),
    "snail_cat": ((40, 26), {"walk": 4, "hide": 3, "shell": 2, "death": 4}),
    "spider_cat": ((50, 56), {"hang": 2, "drop": 2, "walk": 4, "death": 4}),
    "bush": ((30, 16), {"still": 1}),
    "stump": ((22, 26), {"still": 1}),
    "milk": ((32, 6), {"still": 1}),
    "bridge": ((48, 12), {"still": 1, "crumble": 4}),
    "island": ((48, 24), {"still": 1}),
    "island_frost": ((48, 24), {"still": 1}),
    "island_haunted": ((48, 24), {"still": 1}),
    "island_citadel": ((48, 24), {"still": 1}),
    "bridge_citadel": ((48, 12), {"still": 1, "crumble": 4}),
    "terrain_forest_top": ((16, 16), {"still": 1}),
    "terrain_forest_edge": ((8, 16), {"still": 1}),
    "terrain_forest_wall": ((8, 16), {"still": 1}),
    "terrain_forest_fill": ((16, 16), {"still": 1}),
    # The forest ravine is a waterfall pit (characters/waterfall.py)
    "ravine_forest": ((8, 16), {"still": 1}),
    "ravine_forest_b": ((8, 16), {"still": 1}),
    "ravine_forest_rim": ((12, 24), {"still": 1}),
    "ravine_forest_vines": ((6, 24), {"still": 1}),
    "ravine_forest_back": ((16, 16), {"still": 1}),
    "ravine_forest_falls": ((16, 16), {"flow": 4}),
    "ravine_forest_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_forest_lip": ((16, 6), {"flow": 4}),
    "ravine_forest_surface": ((16, 8), {"wave": 4}),
    "ravine_forest_pool": ((16, 24), {"churn": 4}),
    "ravine_forest_splash": ((16, 12), {"splash": 4}),
    "ravine_forest_deep": ((16, 16), {"still": 1}),
    "ravine_forest_floor": ((16, 16), {"still": 1}),
    "ravine_forest_fill": ((8, 48), {"still": 1}),
    # Cut from the user's painting (characters/boss_squirrel_painted.py), 3x PNGs; ROLL and CLIMB hold and repeat painted
    # frames so each release lands on its hazard's time (the roll's ball is a spin).
    "boss_squirrel": ((164, 132), {"idle": 9, "throw": 10, "roll": 28, "climb": 32, "hurt": 1, "death": 10}),
    # World 2, frost
    "snowball": ((16, 16), {"roll": 4, "death": 4}),
    "penguin": ((36, 16), {"slide": 4, "death": 4}),
    "icicle": ((12, 22), {"hang": 2, "fall": 2, "shatter": 4}),
    "snowdrift": ((24, 11), {"still": 1}),
    "ice": ((32, 6), {"still": 1}),
    "ice_ledge": ((48, 14), {"still": 1, "crumble": 4}),
    # The Frostpaw Mountains critters (characters/frost_critters.py)
    "ice_slime": ((34, 34), {"idle": 2, "walk": 4, "attack": 3, "hit": 2, "death": 4}),
    "snow_cat": ((40, 34), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "ice_bat": ((46, 32), {"fly": 4, "attack": 3, "hit": 2, "death": 3}),
    "ice_golem": ((52, 42), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "penguin_soldier": ((48, 34), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "spear": ((16, 6), {"fly": 2}),
    "snowy_owl": ((46, 36), {"fly": 4, "attack": 3, "hit": 2, "death": 4}),
    "icicle_shot": ((8, 14), {"fly": 2}),
    "ice_hedgehog": ((36, 28), {"walk": 4, "curl": 3, "roll": 4, "hit": 2, "death": 4}),
    "snowman": ((44, 44), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "snowball_shot": ((10, 10), {"fly": 4}),
    "icicle_plant": ((38, 36), {"closed": 2, "open": 2, "attack": 3, "hit": 2, "death": 4}),
    "icicle_bolt": ((14, 7), {"fly": 2}),
    "mini_yeti": ((60, 46), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    # The frost world's waterfall pit and terrain (characters/frostpaw.py), the forest contracts
    "ravine_frost": ((8, 16), {"still": 1}),
    "ravine_frost_b": ((8, 16), {"still": 1}),
    "ravine_frost_rim": ((12, 24), {"still": 1}),
    "ravine_frost_vines": ((6, 24), {"still": 1}),
    "ravine_frost_back": ((16, 16), {"still": 1}),
    "ravine_frost_falls": ((16, 16), {"flow": 4}),
    "ravine_frost_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_frost_lip": ((16, 6), {"flow": 4}),
    "ravine_frost_surface": ((16, 8), {"wave": 4}),
    "ravine_frost_pool": ((16, 24), {"churn": 4}),
    "ravine_frost_splash": ((16, 12), {"splash": 4}),
    "ravine_frost_floor": ((16, 16), {"still": 1}),
    "ravine_frost_fill": ((8, 48), {"still": 1}),
    "ravine_frost_deep": ((16, 16), {"still": 1}),
    "terrain_frost_top": ((16, 16), {"still": 1}),
    "terrain_frost_edge": ((8, 16), {"still": 1}),
    "terrain_frost_wall": ((8, 16), {"still": 1}),
    "terrain_frost_fill": ((16, 16), {"still": 1}),
    # Cut from the user's painting (characters/boss_icedragon_painted.py), 3x PNGs; DIVE plays some painted frames twice.
    "boss_icedragon": ((190, 134), {"idle": 9, "shards": 10, "breath": 7, "dive": 13, "hurt": 2, "death": 6}),
    # World 3, haunted
    "ghost_cat": ((38, 32), {"float": 4, "fade": 4, "attack": 3, "hit": 2}),
    "bat": ((40, 28), {"fly": 4, "attack": 3, "hit": 2, "death": 3}),
    # The Haunted Meowseum critters (characters/haunted_critters.py, with ghost_cat and bat above)
    "spirit_ball": ((10, 10), {"fly": 4}),
    "haunted_portrait": ((36, 36), {"idle": 2, "move": 4, "attack": 3, "hit": 2, "death": 4}),
    "magic_shot": ((12, 8), {"fly": 2}),
    "cursed_armor": ((56, 50), {"statue": 1, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "candle_cat": ((28, 36), {"idle": 2, "move": 4, "attack": 3, "hit": 2, "death": 4}),
    "fire_orb": ((10, 10), {"fly": 4}),
    "poltergeist_book": ((36, 28), {"idle": 2, "move": 4, "attack": 3, "hit": 2, "death": 4}),
    "magic_bolt": ((10, 10), {"fly": 2}),
    "gargoyle_cat": ((46, 46), {"idle": 1, "prepare": 2, "leap": 3, "walk": 4, "hit": 2, "death": 4}),
    "shadow_cat": ((56, 34), {"idle": 2, "teleport": 4, "attack": 4, "hit": 2, "death": 4}),
    "skeleton_mouse": ((24, 28), {"idle": 2, "throw": 4, "death": 4}),
    "bone": ((10, 10), {"fly": 4}),
    "skull": ((20, 14), {"fly": 4, "death": 3}),
    "bell": ((24, 30), {"idle": 2, "ring": 4}),
    "tombstone": ((20, 26), {"still": 1}),
    "vanish": ((48, 10), {"solid": 1, "fading": 4}),
    # The haunted world's fog pit and terrain (characters/meowseum.py), the forest contracts
    "ravine_haunted": ((8, 16), {"still": 1}),
    "ravine_haunted_b": ((8, 16), {"still": 1}),
    "ravine_haunted_rim": ((12, 24), {"still": 1}),
    "ravine_haunted_vines": ((6, 24), {"still": 1}),
    "ravine_haunted_back": ((16, 16), {"still": 1}),
    "ravine_haunted_falls": ((16, 16), {"flow": 4}),
    "ravine_haunted_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_haunted_lip": ((16, 6), {"flow": 4}),
    "ravine_haunted_surface": ((16, 8), {"wave": 4}),
    "ravine_haunted_pool": ((16, 24), {"churn": 4}),
    "ravine_haunted_splash": ((16, 12), {"splash": 4}),
    "ravine_haunted_floor": ((16, 16), {"still": 1}),
    "ravine_haunted_fill": ((8, 48), {"still": 1}),
    "ravine_haunted_deep": ((16, 16), {"still": 1}),
    "terrain_haunted_top": ((16, 16), {"still": 1}),
    "terrain_haunted_edge": ((8, 16), {"still": 1}),
    "terrain_haunted_wall": ((8, 16), {"still": 1}),
    "terrain_haunted_fill": ((16, 16), {"still": 1}),
    # Cut from the user's painting (characters/boss_phantom_painted.py), 3x PNGs; SUMMON's cast and some SPECTRAL WAVES
    # frames play twice, split is IDLE with a drawn glow.
    "boss_phantom": ((156, 126), {"idle": 7, "summon": 12, "teleport": 25, "split": 7, "hurt": 5, "death": 7}),
    # World 4, citadel
    "vent": ((22, 68), {"idle": 1, "warn": 2, "fire": 4}),
    "piston": ((24, 76), {"up": 1, "warn": 2, "slam": 3}),
    "cannon": ((30, 20), {"idle": 1, "fire": 3, "death": 4}),
    "cannonball": ((16, 10), {"fly": 4}),
    "debris": ((18, 22), {"hang": 2, "fall": 2, "shatter": 4}),
    "mech_mouse": ((32, 20), {"run": 4, "death": 4}),
    # The Cataclysm Citadel critters (characters/citadel_critters.py)
    "lava_slime": ((36, 30), {"idle": 2, "move": 4, "attack": 3, "hit": 2, "death": 4}),
    "lava_glob": ((10, 10), {"fly": 4}),
    "fire_imp": ((44, 38), {"fly": 4, "attack": 3, "hit": 2, "death": 4}),
    "fireball_shot": ((12, 10), {"fly": 4}),
    "stone_guard": ((60, 46), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "magma_blast": ((14, 12), {"fly": 4}),
    "hell_hound": ((58, 34), {"idle": 2, "run": 6, "attack": 4, "hit": 2, "death": 4}),
    "ember_bat": ((50, 34), {"fly": 4, "attack": 3, "hit": 2, "death": 3}),
    "flame_archer": ((46, 36), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "flame_arrow": ((16, 6), {"fly": 2}),
    "chainsaw_cat": ((70, 48), {"idle": 2, "walk": 4, "attack": 4, "hit": 2, "death": 4}),
    "fire_wisp": ((50, 54), {"idle": 2, "move": 4, "attack": 4, "hit": 2, "death": 4}),
    "lava_puddle": ((22, 8), {"burn": 4}),
    "fire_ring": ((48, 16), {"burn": 4}),
    # The Void critters (characters/void_critters.py)
    "void_slime": ((36, 30), {"idle": 2, "move": 4, "attack": 3, "hit": 2, "death": 4}),
    "void_orb": ((12, 12), {"fly": 4}),
    "void_bat": ((50, 34), {"fly": 4, "attack": 3, "hit": 2, "death": 3}),
    "void_sentinel": ((60, 46), {"idle": 2, "move": 4, "charge": 3, "attack": 3, "hit": 2, "death": 4}),
    "void_laser": ((16, 4), {"fly": 2}),
    "rift_hound": ((58, 34), {"idle": 2, "run": 6, "attack": 4, "hit": 2, "death": 4}),
    "void_mage": ((50, 46), {"idle": 2, "walk": 4, "summon": 4, "attack": 4, "hit": 2, "death": 4}),
    "void_bolt": ((14, 10), {"fly": 4}),
    "rift_turret": ((44, 44), {"idle": 2, "charge": 4, "attack": 3, "hit": 2, "death": 4}),
    "crystal_shot": ((16, 6), {"fly": 2}),
    "void_wisp": ((50, 54), {"idle": 2, "move": 4, "attack": 3, "hit": 2, "death": 4}),
    "homing_orb": ((14, 12), {"fly": 4}),
    "mini_void_cat": ((56, 34), {"idle": 2, "teleport": 4, "attack": 4, "hit": 2, "death": 4}),
    # Sakura world, level 1 critters (characters/sakura_critters.py)
    "sakura_slime": ((34, 28), {"idle": 2, "walk": 4, "attack": 3, "hurt": 2, "death": 4}),
    # Cut from the user's painting (characters/sakura_bunny_painted.py), 3x PNGs; run is JUMP then FALL, attack drops
    # the painted projectile frame.
    "sakura_bunny": ((44, 36), {"idle": 6, "walk": 8, "run": 12, "attack": 5, "hurt": 3, "death": 6}),
    "lantern_spirit": ((34, 38), {"idle": 2, "float": 4, "attack": 3, "hurt": 2, "death": 4}),
    "blossom_shot": ((12, 12), {"fly": 4}),
    # Cut from the user's painting (characters/bird_crow_painted.py), 3x PNGs; attack drops the painted feathers.
    "bird_crow": ((48, 34), {"idle": 7, "fly": 9, "attack": 6, "hurt": 4, "death": 8}),
    "spike_plant": ((36, 32), {"idle": 2, "open": 2, "attack": 3, "hurt": 2, "death": 4}),
    # Cut from the user's painting (characters/rolling_onigiri_painted.py), 3x PNGs; every painted frame of each row.
    "rolling_onigiri": ((44, 28), {"idle": 6, "roll": 11, "attack": 6, "hurt": 4, "death": 6}),
    "sakura_spirit": ((24, 24), {"float": 8, "death": 6}),
    # Sakura world, level 2 (dusk) critters (characters/sakura_dusk_critters.py)
    "lantern_slime": ((34, 32), {"idle": 2, "walk": 4, "attack": 3, "hurt": 2, "death": 4}),
    "lantern_flame": ((12, 12), {"fly": 4}),
    "ninja_tanuki": ((48, 40), {"idle": 2, "walk": 4, "attack": 4, "hurt": 2, "death": 4}),
    # Cut from the user's painting (characters/sakura_bat_painted.py), 3x PNGs; attack drops the painted projectile cell.
    "sakura_bat": ((46, 32), {"fly": 8, "attack": 6, "hurt": 4, "death": 8}),
    "shadow_spirit": ((38, 38), {"idle": 2, "cast": 3, "attack": 3, "hurt": 2, "death": 4}),
    "spirit_flame": ((14, 12), {"fly": 4}),
    "spike_kappa": ((40, 32), {"closed": 2, "open": 2, "attack": 3, "hurt": 2, "death": 4}),
    "spike_ball": ((12, 12), {"fly": 4}),
    # Sakura world, level 3 (night) critters (characters/sakura_night_critters.py)
    "shadow_slime": ((40, 34), {"idle": 2, "walk": 4, "attack": 3, "hurt": 2, "death": 4}),
    # Cut from the user's painting (characters/samurai_ronin_painted.py), 3x PNGs; every painted frame of each row.
    "samurai_ronin": ((52, 40), {"idle": 6, "walk": 9, "attack": 6, "hurt": 4, "death": 8}),
    "oni_cat": ((76, 56), {"idle": 2, "walk": 4, "attack": 4, "hurt": 2, "death": 4}),
    "oni_rock": ((12, 12), {"fly": 4}),
    "tengu_crow": ((54, 44), {"fly": 4, "idle": 2, "attack": 3, "hurt": 2, "death": 4}),
    "spirit_wisp": ((38, 38), {"float": 4, "idle": 2, "attack": 3, "hurt": 2, "death": 4}),
    "wisp_shot": ((14, 12), {"fly": 4}),
    "gear": ((30, 30), {"spin": 4}),
    "crate_wall": ((24, 124), {"still": 1, "break": 5}),
    # The citadel's lava pit and terrain (characters/cataclysm.py), the forest contracts
    "ravine_citadel": ((8, 16), {"still": 1}),
    "ravine_citadel_b": ((8, 16), {"still": 1}),
    "ravine_citadel_rim": ((12, 24), {"still": 1}),
    "ravine_citadel_vines": ((6, 24), {"still": 1}),
    "ravine_citadel_back": ((16, 16), {"still": 1}),
    "ravine_citadel_falls": ((16, 16), {"flow": 4}),
    "ravine_citadel_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_citadel_lip": ((16, 6), {"flow": 4}),
    "ravine_citadel_surface": ((16, 8), {"wave": 4}),
    "ravine_citadel_pool": ((16, 24), {"churn": 4}),
    "ravine_citadel_splash": ((16, 12), {"splash": 4}),
    "ravine_citadel_floor": ((16, 16), {"still": 1}),
    "ravine_citadel_fill": ((8, 48), {"still": 1}),
    "ravine_citadel_deep": ((16, 16), {"still": 1}),
    "terrain_citadel_top": ((16, 16), {"still": 1}),
    "terrain_citadel_edge": ((8, 16), {"still": 1}),
    "terrain_citadel_wall": ((8, 16), {"still": 1}),
    "terrain_citadel_fill": ((16, 16), {"still": 1}),
    # World 5, the void (characters/voidrealm.py), the forest contracts
    "ravine_void": ((8, 16), {"still": 1}),
    "ravine_void_b": ((8, 16), {"still": 1}),
    "ravine_void_rim": ((12, 24), {"still": 1}),
    "ravine_void_vines": ((6, 24), {"still": 1}),
    "ravine_void_back": ((16, 16), {"still": 1}),
    "ravine_void_falls": ((16, 16), {"flow": 4}),
    "ravine_void_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_void_lip": ((16, 6), {"flow": 4}),
    "ravine_void_surface": ((16, 8), {"wave": 4}),
    "ravine_void_pool": ((16, 24), {"churn": 4}),
    "ravine_void_splash": ((16, 12), {"splash": 4}),
    "ravine_void_floor": ((16, 16), {"still": 1}),
    "ravine_void_fill": ((8, 48), {"still": 1}),
    "ravine_void_deep": ((16, 16), {"still": 1}),
    "terrain_void_top": ((16, 16), {"still": 1}),
    "terrain_void_edge": ((8, 16), {"still": 1}),
    "terrain_void_wall": ((8, 16), {"still": 1}),
    "terrain_void_fill": ((16, 16), {"still": 1}),
    "island_void": ((48, 24), {"still": 1}),
    "bridge_void": ((48, 12), {"still": 1, "crumble": 4}),
    # Sakura's Blossom Path (characters/sakura_world.py), the forest contracts
    "ravine_sakura": ((8, 16), {"still": 1}),
    "ravine_sakura_b": ((8, 16), {"still": 1}),
    "ravine_sakura_rim": ((12, 24), {"still": 1}),
    "ravine_sakura_vines": ((6, 24), {"still": 1}),
    "ravine_sakura_back": ((16, 16), {"still": 1}),
    "ravine_sakura_falls": ((16, 16), {"flow": 4}),
    "ravine_sakura_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_sakura_lip": ((16, 6), {"flow": 4}),
    "ravine_sakura_surface": ((16, 8), {"wave": 4}),
    "ravine_sakura_pool": ((16, 24), {"churn": 4}),
    "ravine_sakura_splash": ((16, 12), {"splash": 4}),
    "ravine_sakura_floor": ((16, 16), {"still": 1}),
    "ravine_sakura_fill": ((8, 48), {"still": 1}),
    "ravine_sakura_deep": ((16, 16), {"still": 1}),
    "terrain_sakura_top": ((16, 16), {"still": 1}),
    "terrain_sakura_edge": ((8, 16), {"still": 1}),
    "terrain_sakura_wall": ((8, 16), {"still": 1}),
    "terrain_sakura_fill": ((16, 16), {"still": 1}),
    "island_sakura": ((48, 24), {"still": 1}),
    "bridge_sakura": ((48, 12), {"still": 1, "crumble": 4}),
    "platform_sakura_moving": ((48, 12), {"still": 1}),
    "bamboo_spikes": ((22, 20), {"idle": 1, "warn": 2, "rise": 3}),
    # Sakura route level 2, "Petal Bridges" (characters/sakura_dusk.py), the forest contracts
    "ravine_sakura_dusk": ((8, 16), {"still": 1}),
    "ravine_sakura_dusk_b": ((8, 16), {"still": 1}),
    "ravine_sakura_dusk_rim": ((12, 24), {"still": 1}),
    "ravine_sakura_dusk_vines": ((6, 24), {"still": 1}),
    "ravine_sakura_dusk_back": ((16, 16), {"still": 1}),
    "ravine_sakura_dusk_falls": ((16, 16), {"flow": 4}),
    "ravine_sakura_dusk_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_sakura_dusk_lip": ((16, 6), {"flow": 4}),
    "ravine_sakura_dusk_surface": ((16, 8), {"wave": 4}),
    "ravine_sakura_dusk_pool": ((16, 24), {"churn": 4}),
    "ravine_sakura_dusk_splash": ((16, 12), {"splash": 4}),
    "ravine_sakura_dusk_floor": ((16, 16), {"still": 1}),
    "ravine_sakura_dusk_fill": ((8, 48), {"still": 1}),
    "ravine_sakura_dusk_deep": ((16, 16), {"still": 1}),
    "terrain_sakura_dusk_top": ((16, 16), {"still": 1}),
    "terrain_sakura_dusk_edge": ((8, 16), {"still": 1}),
    "terrain_sakura_dusk_wall": ((8, 16), {"still": 1}),
    "terrain_sakura_dusk_fill": ((16, 16), {"still": 1}),
    "island_sakura_dusk": ((48, 24), {"still": 1}),
    "bridge_sakura_dusk": ((48, 12), {"still": 1, "crumble": 4}),
    "platform_sakura_dusk_moving": ((48, 12), {"still": 1}),
    # Sakura route level 3, the night (characters/sakura_night.py), the forest contracts
    "ravine_sakura_night": ((8, 16), {"still": 1}),
    "ravine_sakura_night_b": ((8, 16), {"still": 1}),
    "ravine_sakura_night_rim": ((12, 24), {"still": 1}),
    "ravine_sakura_night_vines": ((6, 24), {"still": 1}),
    "ravine_sakura_night_back": ((16, 16), {"still": 1}),
    "ravine_sakura_night_falls": ((16, 16), {"flow": 4}),
    "ravine_sakura_night_falls_edge": ((4, 16), {"flow": 4}),
    "ravine_sakura_night_lip": ((16, 6), {"flow": 4}),
    "ravine_sakura_night_surface": ((16, 8), {"wave": 4}),
    "ravine_sakura_night_pool": ((16, 24), {"churn": 4}),
    "ravine_sakura_night_splash": ((16, 12), {"splash": 4}),
    "ravine_sakura_night_floor": ((16, 16), {"still": 1}),
    "ravine_sakura_night_fill": ((8, 48), {"still": 1}),
    "ravine_sakura_night_deep": ((16, 16), {"still": 1}),
    "terrain_sakura_night_top": ((16, 16), {"still": 1}),
    "terrain_sakura_night_edge": ((8, 16), {"still": 1}),
    "terrain_sakura_night_wall": ((8, 16), {"still": 1}),
    "terrain_sakura_night_fill": ((16, 16), {"still": 1}),
    "island_sakura_night": ((48, 24), {"still": 1}),
    "bridge_sakura_night": ((48, 12), {"still": 1, "crumble": 4}),
    "platform_sakura_night_moving": ((48, 12), {"still": 1}),
    "lantern_pendulum": ((20, 40), {"swing": 8}),
    "falling_lantern": ((14, 18), {"hang": 2, "fall": 2, "burn": 4}),
    # Cut from the user's painting (characters/boss_mecha_painted.py), 3x PNGs; IDLE and CORE ping-pong, ROCKETS plays
    # its aim and launch twice, HURT is IDLE 1 knocked back (no HURT row painted).
    "boss_mecha": ((192, 140), {"idle": 16, "rockets": 15, "tail": 10, "core": 6, "hurt": 3, "death": 6}),
    # Final world. Cut from the user's painting (characters/boss_voidcat_painted.py), 3x PNGs; attacks replay painted
    # frames so each strike lands on its hazard's time, HURT is IDLE 0 knocked back, DEATH IDLE 0 dissolving (no HURT or
    # DEATH row painted). The frame is wide: PHASE RUSH's streak trails 213 points behind the head.
    "boss_voidcat": ((400, 140), {"idle": 10, "paws": 24, "stars": 19, "portal": 28, "rift": 26, "phase": 24,
                                  "storm": 20, "hurt": 3, "death": 10}),
    "portal": ((26, 36), {"open": 4, "close": 4}),
    "hazard_shadow_paw": ((40, 14), {"fly": 6}),
    "hazard_falling_star": ((12, 16), {"fly": 6}),
    "hazard_void_wave": ((26, 12), {"fly": 3}),
    "hazard_star_shard": ((22, 8), {"fly": 6}),
    # Sakura route boss
    # Cut from the user's painting (characters/boss_kitsune_painted.py), 3x PNGs; every painted frame once.
    "boss_kitsune": ((150, 120), {"idle": 12, "claw": 18, "bloom": 16, "summon": 16, "hurt": 3, "death": 12}),
    # Cut from the user's painting (characters/boss_toad_painted.py), 3x PNGs; every painted frame once (SLAM 17-18,
    # painted without the toad, left out).
    "boss_toad": ((160, 136), {"idle": 9, "walk": 8, "prepare": 6, "tongue": 11, "lanterns": 14, "slam": 18,
                               "hurt": 4, "death": 8}),
    "boss_guardian_cat": ((160, 136), {"idle": 4, "walk": 6, "prepare": 3, "volley": 6, "spin": 6, "slam": 8, "beam": 7,
                                       "summon": 6, "enrage": 6, "hurt": 2, "death": 8}),
    # Pickups and award art
    "fish": ((16, 12), {"spin": 6}),
    "yarn_basket": ((28, 28), {"glow": 4}),
    "medal": ((32, 32), {"bronze": 1, "silver": 1, "gold": 1}),
    # Start, level-complete and game-over screens (no text baked in)
    "title_wreath": ((280, 110), {"still": 1}),
    "title_wreath_small": ((240, 96), {"still": 1}),
    "title_wreath_stone": ((250, 120), {"still": 1}),
    "title_cat": ((64, 40), {"blink": 4}),
    # Jump buttons (48x48, round, transparent outside) and the double-jump burst
    "button_jump": ((48, 48), {"still": 1}),
    "button_jump_pressed": ((48, 48), {"still": 1}),
    "button_jump_disabled": ((48, 48), {"still": 1}),
    "button_double": ((48, 48), {"sparkle": 6}),
    "button_double_pressed": ((48, 48), {"sparkle": 6}),
    "button_double_disabled": ((48, 48), {"still": 1}),
    "paw_trail": ((16, 16), {"burst": 5}),
    **{name: ((48, 48), {"still": 1}) for name in (
        "button_yarn", "button_yarn_pressed", "button_yarn_cooldown", "button_dash", "button_dash_pressed",
        "button_dash_cooldown", "button_pounce")},
    "button_pounce_charged": ((48, 48), {"sparkle": 6}),
    # HUD
    "hud_panel": ((24, 24), {"still": 1}),
    "hud_level_tab": ((64, 32), {"still": 1}),
    "heart_full": ((16, 14), {"still": 1}),
    "heart_half": ((16, 14), {"still": 1}),
    "heart_empty": ((16, 14), {"still": 1}),
    "heart_lose": ((24, 22), {"burst": 5}),
    "heart_gain": ((24, 22), {"glow": 6}),
    "xp_bar_frame": ((24, 10), {"still": 1}),
    "xp_bar_fill": ((1, 6), {"still": 1}),
    "level_up_arrows": ((32, 28), {"rise": 6}),
    "boss_bar_frame": ((40, 12), {"still": 1}),
    "boss_bar_fill": ((1, 4), {"still": 1}),
    "boss_bar_fill_low": ((1, 4), {"still": 1}),
    "boss_bar_flash": ((1, 4), {"still": 1}),
    "menu_scene_portrait": ((210, 230), {"still": 1}),
    "menu_scene_landscape": ((440, 150), {"still": 1}),
    # The Sakura start screen's backdrop, composed from the user's painted asset sheet (characters/menu_sakura_painted.py),
    # 3x PNGs, transparent above the scenery.
    "menu_scene_sakura_portrait": ((210, 230), {"still": 1}),
    "menu_scene_sakura_landscape": ((440, 150), {"still": 1}),
    "menu_sky": ((16, 64), {"still": 1}),
    "menu_clouds": ((120, 40), {"still": 1}),
    "menu_waterfall": ((12, 44), {"loop": 4}),
    **{f"icon_{name}": ((16, 16), {"still": 1}) for name in ("trophy", "cat", "retry", "home", "play", "paw", "lock")},
    **{f"confetti_{name}": ((8, 8), {"loop": 6}) for name in ("red", "yellow", "blue", "green")},
    "sparkle_big": ((12, 12), {"loop": 4}),
    "sunburst": ((160, 160), {"still": 1}),
    "cat_silhouette": ((44, 36), {"still": 1}),
    "sign_cat": ((18, 22), {"still": 1}),
    "life_lost": ((18, 16), {"still": 1}),
    "leaf_drift": ((10, 8), {"loop": 4}),
    "stars_dizzy": ((16, 8), {"loop": 4}),
}


# Recoloured heroes (`hero_<id>`): every one must match the code-drawn hero in size, anchor and animations (see
# `test_hero_skins_match_the_hero` for what painted skins, and `hero` itself, may differ in).
HERO_SKINS = ("shadow", "misty", "sakura", "honey", "pixie", "clover", "snowball", "napster", "toffee", "cabage",
              "sharky")


@pytest.fixture(scope="module")
def sprites():
    return {s.name: s for s in build.all_sprites()}


@pytest.fixture(scope="module")
def drawn_hero():
    """The code-drawn hero, built in memory: `hero` itself is now painted (Fluffy)."""
    from characters.hero import drawn_hero
    return drawn_hero()


@pytest.mark.parametrize("name", sorted(SPEC))
def test_sprite_matches_spec(sprites, name):
    size, animations = SPEC[name]
    sprite = sprites[name]
    assert sprite.size == size
    assert {anim: len(a.frames) for anim, a in sprite.anims.items()} == animations


def test_every_frame_has_its_sprite_size_and_is_not_blank(sprites):
    for sprite in sprites.values():
        for name, anim in sprite.anims.items():
            for index, frame in enumerate(anim.frames):
                # Painted sprites (`Sprite.scale` > 1) keep more pixels per point; the size is in points.
                assert frame.size == (sprite.size[0] * sprite.scale, sprite.size[1] * sprite.scale), \
                    f"{sprite.name}/{name}[{index}]"
                # The last frames of a death may dissolve to nothing; everything else must draw something.
                if name != "death":
                    assert frame.getbbox() is not None, f"{sprite.name}/{name}[{index}] is empty"


# Painted frames cut off at the frame's edge on purpose: the ronin's slash crescents and raised sword (attack), and the
# scarf trailing behind it as it lies down (death), wider than the frame (characters/samurai_ronin_painted.py).
CROPPED_ON_PURPOSE = {("samurai_ronin", "attack"), ("samurai_ronin", "death")}


@pytest.mark.parametrize("name", ["hero", *(f"hero_{skin}" for skin in HERO_SKINS), "boss_squirrel",
                                  "boss_icedragon", "boss_phantom", "boss_mecha", "boss_voidcat", "boss_kitsune", "boss_toad",
                                  "boss_guardian_cat",
                                  "squirrel", "hedgehog", "ghost_cat", "skeleton_mouse", "penguin", "mech_mouse",
                                  "mushroom_cat", "forest_bat", "plant_cat", "bee_cat", "stump_cat", "snail_cat",
                                  "ice_slime", "snow_cat", "ice_bat", "ice_golem", "penguin_soldier", "snowy_owl",
                                  "ice_hedgehog", "snowman", "icicle_plant", "mini_yeti",
                                  "bat", "haunted_portrait", "cursed_armor", "candle_cat", "poltergeist_book",
                                  "gargoyle_cat", "shadow_cat",
                                  "lava_slime", "fire_imp", "stone_guard", "hell_hound", "ember_bat", "flame_archer",
                                  "chainsaw_cat", "fire_wisp",
                                  "void_slime", "void_bat", "void_sentinel", "rift_hound", "void_mage", "rift_turret",
                                  "void_wisp", "mini_void_cat",
                                  "sakura_slime", "sakura_bunny", "lantern_spirit", "bird_crow", "spike_plant",
                                  "rolling_onigiri", "sakura_spirit",
                                  "lantern_slime", "ninja_tanuki", "sakura_bat", "shadow_spirit", "spike_kappa",
                                  "shadow_slime", "samurai_ronin", "oni_cat", "tengu_crow", "spirit_wisp"])
def test_big_creatures_are_not_clipped(sprites, name):
    """A sprite that reaches the side or top of its canvas loses a snout, tail or club: widen the canvas."""
    for anim, data in sprites[name].anims.items():
        if (name, anim) in CROPPED_ON_PURPOSE:
            continue
        for index, frame in enumerate(data.frames):
            width, height = frame.size
            alpha = frame.getchannel("A")
            edges = {"left": (0, 0, 1, height), "right": (width - 1, 0, width, height), "top": (0, 0, width, 1)}
            for edge, box in edges.items():
                assert alpha.crop(box).getbbox() is None, f"{name}/{anim}[{index}] touches the {edge} edge"


def test_hero_stands_on_its_ground_line(sprites, drawn_hero):
    """Grounded hero poses put their feet on the anchor row (plus the outline below it), and no frame reaches
    lower, so the bottom edge never clips a paw, cape or tail: the painted `hero` (in its 3x pixels) and the
    code-drawn one the skins copy."""
    for label, hero in (("hero", sprites["hero"]), ("drawn hero", drawn_hero)):
        floor = (hero.ground + 2) * hero.scale
        for anim in ("idle", "stop", "throw"):
            for index, frame in enumerate(hero.anims[anim].frames):
                assert frame.getbbox()[3] == floor, f"{label}/{anim}[{index}] is not standing on the ground"
        for anim, data in hero.anims.items():
            for index, frame in enumerate(data.frames):
                box = frame.getbbox()
                assert box is None or box[3] <= floor, f"{label}/{anim}[{index}] reaches below the ground"


def test_output_is_deterministic(sprites):
    again = {s.name: s for s in build.all_sprites()}
    for name, sprite in sprites.items():
        for anim, data in sprite.anims.items():
            for a, b in zip(data.frames, again[name].anims[anim].frames):
                assert a.tobytes() == b.tobytes(), f"{name}/{anim} differs between runs"


def test_animation_actually_moves(sprites):
    for name in ("hero", "squirrel", "hedgehog", "penguin", "ghost_cat", "mech_mouse", "boss_squirrel",
                 "boss_icedragon", "boss_phantom", "boss_mecha", "boss_voidcat", "boss_kitsune", "boss_toad",
                 "boss_guardian_cat"):
        anim = next(iter(sprites[name].anims.values()))
        assert len({frame.tobytes() for frame in anim.frames}) > 1, f"{name}: all frames identical"


def test_manifest_and_atlas_match_the_code(sprites):
    """Fails when someone edits a character but forgets to run build.py."""
    manifest = json.loads(export.MANIFEST.read_text())
    assert set(manifest) == set(sprites)
    for name, sprite in sprites.items():
        assert (manifest[name]["width"], manifest[name]["height"]) == sprite.size
        for anim, data in sprite.anims.items():
            assert manifest[name]["animations"][anim]["frames"] == len(data.frames)
            for index, frame in enumerate(export.frames_of(sprite, anim)):
                stored = export.stored_frame_index(manifest[name]["animations"][anim], index)
                frame_name = export.frame_name(name, anim, stored)
                path = export.ATLAS / f"{frame_name}.imageset" / f"{frame_name}.png"
                assert path.exists(), f"{path.name} missing: run Tools/sprites/build.py"
                assert Image.open(path).convert("RGBA").tobytes() == frame.tobytes(), f"{frame_name} is stale"


def test_atlas_stores_each_frame_of_an_animation_once():
    """Repeats within an animation are written once and replayed through the manifest's `sequence`: every index
    it names has an imageset, stored frames are numbered 0..k-1 with none left over, and no two are identical."""
    manifest = json.loads(export.MANIFEST.read_text())
    for name, entry in manifest.items():
        for anim, info in entry["animations"].items():
            sequence = info.get("sequence", list(range(info["frames"])))
            assert len(sequence) == info["frames"], f"{name}/{anim}"
            assert "sequence" not in info or sequence != list(range(info["frames"])), f"{name}/{anim}: needless sequence"
            assert sorted(set(sequence)) == list(range(max(sequence) + 1)), f"{name}/{anim}: gaps in {sequence}"
            prefix = f"{name}_{anim}_"
            on_disk = {int(p.stem[len(prefix):]) for p in export.ATLAS.glob(f"{prefix}*.imageset")
                       if p.stem[len(prefix):].isdigit()}
            assert on_disk == set(sequence), f"{name}/{anim}: stored {sorted(on_disk)}, sequence {sequence}"
            pixels = [Image.open(export.ATLAS / f"{prefix}{i}.imageset" / f"{prefix}{i}.png").tobytes()
                      for i in sorted(on_disk)]
            assert len(set(pixels)) == len(pixels), f"{name}/{anim}: identical stored frames"


def test_every_thing_the_game_can_show_has_a_sprite(sprites):
    resources = ROOT / "App" / "Resources"
    needed = set()
    levels = sorted((resources / "Levels").glob("level_*.json")) + sorted((resources / "Levels").glob("route_*.json"))
    for path in levels:                                  # the main levels and every cat's route
        level = json.loads(path.read_text())
        needed |= {item["kind"] for item in level["items"]}
        needed |= {level["boss"], f"ground_{level['background']}", f"ground_{level['background']}_fill",
                   f"ground_{level['background']}_earth", f"bg_{level['background']}_sky_top"}
        needed |= {f"bg_{level['background']}_{layer}" for layer in ("sky", "far", "near", "clouds", "puffs", "bushes")}
        if level.get("ravines"):
            needed |= {f"ravine_{level['background']}", f"ravine_{level['background']}_fill",
                       f"ravine_{level['background']}_deep"}
    for boss in json.loads((resources / "Bosses.json").read_text()):
        for attack in boss["attacks"]:
            needed |= {f"hazard_{h['kind']}" for h in attack["hazards"]}
            needed |= {s["kind"] for s in attack.get("summons", [])}
    needed |= {"hero", "yarn", "fish", "yarn_basket", "medal", "heart_full", "heart_empty", "spark_star", "spark_ember",
               "spark_feather", "acorn_thrown", "bone", "cannonball"}
    needed |= {f"ability_{name}" for name in ("yarnShot", "doublePounce", "ghostDash", "superPounce")}
    assert needed - set(sprites) == set()


@pytest.mark.parametrize("skin", ("fluffy", *HERO_SKINS))
def test_hero_skins_match_the_hero(sprites, drawn_hero, skin):
    """A skin is the same hero in another coat: same frame size, anchor, animations and loop flags as the code-drawn
    hero (`hero.drawn_hero`, built in memory, since `hero` itself is cut from Fluffy's painted sheet). A code-drawn
    skin also has its frame counts and fps. A cat cut from a painted sheet (`characters/hero_painted.py`, painted to
    `docs/hero-sheet-brief.md`: Fluffy as `hero`, the others as `hero_<id>`) plays its own painted frames, so its
    counts and fps may differ, but each animation lasts about as long as the code-drawn hero's (within 25%); the
    throw fits the 0.25 s throw window and the hurt the 0.3 s hurt window (`GameScene`'s `hurtUntil`), which the
    brief gives one full cycle."""
    from characters.hero_painted import PAINTED, sprite_name
    hero, other = drawn_hero, sprites[sprite_name(skin)]
    assert (other.size, other.cx, other.ground, other.faces_left) == (hero.size, hero.cx, hero.ground, hero.faces_left)
    assert {a: d.loop for a, d in other.anims.items()} == {a: d.loop for a, d in hero.anims.items()}
    if skin in PAINTED:
        for name, data in other.anims.items():
            seconds, hero_seconds = len(data.frames) / data.fps, len(hero.anims[name].frames) / hero.anims[name].fps
            if name == "throw":
                assert seconds <= 0.25 + 1e-9, f"{other.name}/throw lasts {seconds:.3f} s"
            elif name == "hurt":
                assert hero_seconds <= seconds <= 0.31, f"{other.name}/hurt lasts {seconds:.3f} s"
            else:
                assert abs(seconds / hero_seconds - 1) <= 0.25, \
                    f"{other.name}/{name} lasts {seconds:.3f} s, the hero {hero_seconds:.3f} s"
    else:
        assert {a: d.fps for a, d in other.anims.items()} == {a: d.fps for a, d in hero.anims.items()}
        for name, data in other.anims.items():
            assert len(data.frames) == len(hero.anims[name].frames), f"{other.name}/{name}"
    differs = sum(a.tobytes() != b.tobytes() for name in hero.anims
                  for a, b in zip(hero.anims[name].frames, other.anims[name].frames))
    assert differs > 0, f"{other.name} looks exactly like the code-drawn hero"


THEMES = ("forest", "frost", "haunted", "citadel", "void", "sakura", "sakura_dusk", "sakura_night")
THEME_LAYERS = ("sky", "sky_top", "puffs", "clouds", "far", "near", "bushes")
PIT_PIECES = ("", "_b", "_rim", "_vines", "_back", "_falls", "_falls_edge", "_lip", "_surface", "_pool", "_splash", "_floor",
              "_fill", "_deep")


@pytest.mark.parametrize("theme", THEMES)
def test_every_theme_has_its_whole_set(sprites, theme):
    """Each world draws the same pieces under its own name, so the renderer picks them up by theme; the parallax
    strips share their sizes so they tile and stand on the ground line alike."""
    names = [f"bg_{theme}_{layer}" for layer in THEME_LAYERS]
    names += [f"ground_{theme}", f"ground_{theme}_earth", f"ground_{theme}_fill"]
    names += [f"ravine_{theme}{piece}" for piece in PIT_PIECES]
    names += [f"terrain_{theme}_{piece}" for piece in ("top", "edge", "wall", "fill")]
    assert [n for n in names if n not in sprites] == []
    assert sprites[f"bg_{theme}_sky"].size == (16, 200)
    for layer in ("puffs", "clouds", "far", "near", "bushes"):
        assert sprites[f"bg_{theme}_{layer}"].size[0] == 320, f"bg_{theme}_{layer} must tile at 320"
    assert sprites[f"ground_{theme}"].size == (32, 48) and sprites[f"ground_{theme}_earth"].size == (32, 36)


def test_painted_heroes_are_cut_cleanly(sprites):
    """Heroes cut from a painted sheet: hard alpha (no glow halo on dark backgrounds) except the see-through
    ghost, and grounded poses standing on the frame's bottom row like `hero`."""
    from characters.hero_painted import PAINTED, sprite_name
    for skin in PAINTED:
        sprite = sprites[sprite_name(skin)]
        for name, data in sprite.anims.items():
            for index, frame in enumerate(data.frames):
                alpha = frame.getchannel("A").histogram()
                if name == "ghost":
                    assert sum(alpha[200:]) == 0, f"{sprite.name}/ghost[{index}] is not see-through"
                else:
                    assert sum(alpha[1:255]) == 0, f"{sprite.name}/{name}[{index}] has soft alpha"
                if name in ("run", "idle", "stop", "throw", "dash", "menu", "sit_happy", "peek", "ko"):
                    assert frame.getbbox()[3] == frame.height, f"{sprite.name}/{name}[{index}] is off the ground"



def test_painted_bosses_are_cut_cleanly(sprites):
    """Bosses and their projectiles cut from a painted sheet (`sheet_boss.py`): 3x PNGs with hard alpha (no glow
    halo on dark backgrounds); the boss's grounded poses stand on its ground row and nothing reaches below it."""
    from characters import (boss_icedragon_painted, boss_kitsune_painted, boss_mecha_painted, boss_phantom_painted,
                            boss_squirrel_painted, boss_toad_painted, boss_voidcat_painted)
    in_air = {("boss_icedragon", "dive", i) for i in boss_icedragon_painted.IN_AIR}     # the dive's airborne frames
    in_air |= {("boss_voidcat", "death", i) for i in boss_voidcat_painted.DEATH_IN_AIR}  # only rising stars left
    for module, boss_name in ((boss_kitsune_painted, "boss_kitsune"), (boss_toad_painted, "boss_toad"),
                              (boss_icedragon_painted, "boss_icedragon"), (boss_mecha_painted, "boss_mecha"),
                              (boss_phantom_painted, "boss_phantom"), (boss_squirrel_painted, "boss_squirrel"),
                              (boss_voidcat_painted, "boss_voidcat")):
        for name in module.NAMES:
            sprite = sprites[name]
            assert sprite.scale == 3, name
            for anim, data in sprite.anims.items():
                for index, frame in enumerate(data.frames):
                    assert sum(frame.getchannel("A").histogram()[1:255]) == 0, f"{name}/{anim}[{index}] has soft alpha"
        boss = sprites[boss_name]
        bottom = (boss.ground + 1) * boss.scale
        for anim, data in boss.anims.items():
            for index, frame in enumerate(data.frames):
                if (boss_name, anim, index) in in_air:
                    assert frame.getbbox()[3] < bottom, f"{boss_name}/{anim}[{index}] should be in the air"
                else:
                    assert frame.getbbox()[3] == bottom, f"{boss_name}/{anim}[{index}] is not on the ground row"


def test_painted_squirrel_king_releases_on_time(sprites):
    """The Great Squirrel King's attack rows show their release frame when Bosses.json lets the hazard go (GameScene
    plays an attack once from the start of its wind-up, so entry N shows at N / fps), and end before the next wind-up
    (ActorNode does not restart an animation that is still playing)."""
    from characters import boss_squirrel_painted as painted
    boss = next(b for b in json.loads((ROOT / "App" / "Resources" / "Bosses.json").read_text())
                if b["id"] == "boss_squirrel")
    anims = {"acorn_arc": "throw", "acorn_roll": "roll", "giant_acorn": "climb"}      # GameScene.attackAnimation
    sprite = sprites["boss_squirrel"]
    for attack in boss["attacks"]:
        anim = sprite.anims[anims[attack["name"]]]
        times = sorted({attack["telegraph"] + h["delay"] for h in attack["hazards"]})
        shown = [entry / anim.fps for entry in painted.RELEASES[anims[attack["name"]]]]
        assert len(shown) == len(times), attack["name"]
        assert all(abs(a - b) <= 0.05 for a, b in zip(shown, times)), (attack["name"], shown, times)
        assert len(anim.frames) / anim.fps <= attack["telegraph"] + attack["duration"] + attack["recover"], attack["name"]


def test_painted_void_cat_strikes_on_time(sprites):
    """The Void Cat's attack animations show a strike frame when Bosses.json lets each hazard go or opens the portals
    (entry N shows at N / fps from the start of the wind-up), and end before the next wind-up."""
    from characters import boss_voidcat_painted as painted
    boss = next(b for b in json.loads((ROOT / "App" / "Resources" / "Bosses.json").read_text())
                if b["id"] == "boss_voidcat")
    sprite = sprites["boss_voidcat"]
    for attack in boss["attacks"]:
        name = painted.ATTACKS[attack["name"]]
        anim = sprite.anims[name]
        times = sorted({round(attack["telegraph"] + h["delay"], 3)
                        for h in attack["hazards"] + attack.get("portals", [])})
        shown = [entry / anim.fps for entry in painted.RELEASES[name]]
        assert len(shown) == len(times), attack["name"]
        assert all(abs(a - b) <= 0.05 for a, b in zip(shown, times)), (attack["name"], shown, times)
        cycle = attack["telegraph"] + attack["duration"] + attack["recover"]
        assert len(anim.frames) / anim.fps <= cycle, attack["name"]


def test_floral_boss_bar_matches_the_hud():
    """The floral boss bar's pieces (`FLORAL_BAR_CUTS`, built by `titles()`) have the sizes, field and track that
    `PaintedBossHealth.Style.floral` (App/UI/PaintedBossHealth.swift) places the name and the fill by; the fill's
    pieces are the track's height, with the frame ring around them cleared."""
    folder = export.ATLAS.parent

    def piece(name):
        return Image.open(folder / f"{name}.imageset" / f"{name}.png").convert("RGBA")

    sizes = {"boss_plate_floral": (1416, 226), "boss_bar_frame_floral": (1264, 81),
             "boss_bar_fill_floral_left": (30, 48), "boss_bar_fill_floral_mid": (8, 48),
             "boss_bar_fill_floral_right": (64, 48)}
    for name, size in sizes.items():
        im = piece(name)
        assert im.size == size, name
        assert sum(im.getchannel("A").histogram()[1:255]) == 0, f"{name} has soft alpha"
    for name in ("paw", "leaf", "flower", "petal"):
        assert piece(f"boss_bar_{name}_floral").getbbox(), name

    def dark(p):
        return p[3] == 255 and max(p[:3]) < 110

    plate, frame = piece("boss_plate_floral"), piece("boss_bar_frame_floral")
    # The name's box (x 262-1153, y 88-154) is all dark field; so is the track's middle (x 20-1244, y 16-64).
    assert all(dark(plate.getpixel((x, y))) for x in range(262, 1153, 7) for y in range(88, 154, 3))
    assert all(dark(frame.getpixel((x, y))) for x in range(40, 1224, 7) for y in range(20, 60, 3))
    left, right = piece("boss_bar_fill_floral_left"), piece("boss_bar_fill_floral_right")
    for im in (left, right):
        assert im.getpixel((im.width // 2, 24))[0] > 200          # bright orange in the middle
    assert left.getpixel((0, 0))[3] == 0 and left.getpixel((0, 47))[3] == 0     # rounded: corners clear
    assert right.getpixel((63, 0))[3] == 0 and right.getpixel((63, 47))[3] == 0


def test_complete_looks_match_the_screen():
    """Each world's level-complete pieces (`COMPLETE_CUTS`, built by `titles()`) have the sizes `CompleteLook`
    (App/UI/ResultView.swift) lays out by, hard alpha, and an empty parchment and blank button labels where the
    screen writes its own text: no painted letters, stars or icons left there."""
    folder = export.ATLAS.parent

    def piece(name):
        return Image.open(folder / f"{name}.imageset" / f"{name}.png").convert("RGBA")

    # piece: (size, the rectangles the screen writes in (where the painted text was), in the piece's pixels)
    looks = {
        "frost": {"title": ((533, 455), None), "boss": ((546, 548), None),
                  "card": ((732, 673), [(115, 161, 498, 343), (177, 501, 325, 36)]),
                  "next": ((629, 176), (120, 44, 445, 78)), "retry": ((422, 142), (108, 27, 236, 73)),
                  "menu": ((366, 134), (83, 26, 204, 73)), "flake": ((100, 112), None), "crystal": ((51, 103), None)},
        "haunted": {"title": ((613, 405), None), "boss": ((411, 594), None),
                    "card": ((622, 635), [(99, 172, 404, 304), (139, 476, 308, 50)]),
                    "next": ((695, 166), (190, 60, 379, 60)), "retry": ((351, 113), (98, 30, 192, 61)),
                    "menu": ((316, 113), (54, 30, 184, 61)), "ghost": ((124, 130), None), "flame": ((59, 109), None)},
        "citadel": {"title": ((568, 375), None), "boss": ((454, 642), None),
                    "card": ((589, 574), [(112, 142, 362, 126), (86, 268, 408, 181), (142, 449, 296, 47)]),
                    "next": ((638, 175), (100, 51, 438, 87)), "retry": ((348, 121), (87, 22, 188, 67)),
                    "menu": ((331, 121), (60, 22, 198, 67))},
    }
    assert {(t, p) for t, _, p, _ in export.COMPLETE_CUTS} == {(t, p) for t, pieces in looks.items() for p in pieces}
    for theme, pieces in looks.items():
        for name, (size, text) in pieces.items():
            im = piece(f"{name}_complete_{theme}")
            assert im.size == size, f"{name}_complete_{theme}"
            assert sum(im.getchannel("A").histogram()[1:255]) == 0, f"{name}_complete_{theme} has soft alpha"
            for x, y, w, h in [text] if isinstance(text, tuple) else text or []:
                inner = [im.getpixel((px, py)) for px in range(x + 4, x + w - 4, 3)
                         for py in range(y + 4, y + h - 4, 3)]
                if name == "next":      # all orange: no dark outlines, no white letters
                    left = [p for p in inner if p[3] < 255 or max(p[:3]) < 170 or min(p[:3]) > 190]
                else:                   # all cream: no ink, no yellow stars, no blue fish
                    left = [p for p in inner if p[3] < 255 or min(p[:3]) < 120]
                assert not left, f"{name}_complete_{theme} has something left where the screen writes: {left[:3]}"
