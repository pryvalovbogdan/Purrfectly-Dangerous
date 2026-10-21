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
    "hero": ((44, 36), {"run": 8, "stop": 4, "idle": 4, "jump": 2, "fall": 2, "double": 4, "throw": 4, "dash": 4,
                        "pounce": 4, "hurt": 2, "death": 6, "peek": 4, "cheer": 4, "sit_happy": 4, "ko": 2,
                        "ghost": 4, "menu": 4}),
    "yarn": ((12, 12), {"fly": 4, "impact": 5}),
    # World 1, forest
    "squirrel": ((36, 36), {"walk": 6, "death": 4}),
    "acorn": ((14, 14), {"roll": 4, "death": 4}),
    "branch_squirrel": ((40, 40), {"idle": 2, "throw": 4, "death": 4}),
    "acorn_thrown": ((14, 14), {"fly": 4}),
    "hedgehog": ((36, 28), {"walk": 4, "curl": 3, "rolled": 4, "death": 4}),
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
    "ravine_forest_deep_fade": ((16, 32), {"still": 1}),
    "ravine_forest_fill": ((8, 48), {"still": 1}),
    "boss_squirrel": ((112, 132), {"idle": 4, "throw": 6, "roll": 6, "climb": 6, "hurt": 2, "death": 8}),
    # World 2, frost
    "snowball": ((16, 16), {"roll": 4, "death": 4}),
    "penguin": ((36, 16), {"slide": 4, "death": 4}),
    "icicle": ((12, 22), {"hang": 2, "fall": 2, "shatter": 4}),
    "snowdrift": ((24, 11), {"still": 1}),
    "ice": ((32, 6), {"still": 1}),
    "ice_ledge": ((48, 14), {"still": 1, "crumble": 4}),
    "boss_icedragon": ((190, 134), {"idle": 6, "shards": 6, "breath": 8, "dive": 6, "hurt": 2, "death": 8}),
    # World 3, haunted
    "ghost_cat": ((38, 26), {"float": 4, "fade": 4}),
    "bat": ((22, 16), {"fly": 4, "death": 3}),
    "skeleton_mouse": ((24, 28), {"idle": 2, "throw": 4, "death": 4}),
    "bone": ((10, 10), {"fly": 4}),
    "skull": ((20, 14), {"fly": 4, "death": 3}),
    "bell": ((24, 30), {"idle": 2, "ring": 4}),
    "tombstone": ((20, 26), {"still": 1}),
    "vanish": ((48, 10), {"solid": 1, "fading": 4}),
    "boss_phantom": ((84, 126), {"idle": 4, "summon": 6, "teleport": 6, "split": 4, "hurt": 2, "death": 8}),
    # World 4, citadel
    "vent": ((22, 68), {"idle": 1, "warn": 2, "fire": 4}),
    "piston": ((24, 76), {"up": 1, "warn": 2, "slam": 3}),
    "cannon": ((30, 20), {"idle": 1, "fire": 3, "death": 4}),
    "cannonball": ((16, 10), {"fly": 4}),
    "debris": ((18, 22), {"hang": 2, "fall": 2, "shatter": 4}),
    "mech_mouse": ((32, 20), {"run": 4, "death": 4}),
    "gear": ((30, 30), {"spin": 4}),
    "crate_wall": ((24, 124), {"still": 1, "break": 5}),
    "boss_mecha": ((168, 124), {"idle": 4, "rockets": 6, "tail": 6, "core": 4, "hurt": 2, "death": 8}),
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


@pytest.fixture(scope="module")
def sprites():
    return {s.name: s for s in build.all_sprites()}


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
                assert frame.size == sprite.size, f"{sprite.name}/{name}[{index}]"
                # The last frames of a death may dissolve to nothing; everything else must draw something.
                if name != "death":
                    assert frame.getbbox() is not None, f"{sprite.name}/{name}[{index}] is empty"


@pytest.mark.parametrize("name", ["hero", "boss_squirrel", "boss_icedragon", "boss_phantom", "boss_mecha",
                                  "squirrel", "hedgehog", "ghost_cat", "skeleton_mouse", "penguin", "mech_mouse",
                                  "mushroom_cat", "forest_bat", "plant_cat", "bee_cat", "stump_cat", "snail_cat"])
def test_big_creatures_are_not_clipped(sprites, name):
    """A sprite that reaches the side or top of its canvas loses a snout, tail or club: widen the canvas."""
    for anim, data in sprites[name].anims.items():
        for index, frame in enumerate(data.frames):
            width, height = frame.size
            alpha = frame.getchannel("A")
            edges = {"left": (0, 0, 1, height), "right": (width - 1, 0, width, height), "top": (0, 0, width, 1)}
            for edge, box in edges.items():
                assert alpha.crop(box).getbbox() is None, f"{name}/{anim}[{index}] touches the {edge} edge"


def test_hero_stands_on_its_ground_line(sprites):
    """Grounded hero poses put their feet on the anchor row (plus the outline below it), and no frame reaches
    lower, so the bottom edge never clips a paw, cape or tail."""
    hero = sprites["hero"]
    for anim in ("idle", "stop", "throw"):
        for index, frame in enumerate(hero.anims[anim].frames):
            assert frame.getbbox()[3] == hero.ground + 2, f"hero/{anim}[{index}] is not standing on the ground"
    for anim, data in hero.anims.items():
        for index, frame in enumerate(data.frames):
            box = frame.getbbox()
            assert box is None or box[3] <= hero.ground + 2, f"hero/{anim}[{index}] reaches below the ground"


def test_output_is_deterministic(sprites):
    again = {s.name: s for s in build.all_sprites()}
    for name, sprite in sprites.items():
        for anim, data in sprite.anims.items():
            for a, b in zip(data.frames, again[name].anims[anim].frames):
                assert a.tobytes() == b.tobytes(), f"{name}/{anim} differs between runs"


def test_animation_actually_moves(sprites):
    for name in ("hero", "squirrel", "hedgehog", "penguin", "ghost_cat", "mech_mouse", "boss_squirrel",
                 "boss_icedragon", "boss_phantom", "boss_mecha"):
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
                frame_name = export.frame_name(name, anim, index)
                path = export.ATLAS / f"{frame_name}.imageset" / f"{frame_name}.png"
                assert path.exists(), f"{path.name} missing: run Tools/sprites/build.py"
                assert Image.open(path).convert("RGBA").tobytes() == frame.tobytes(), f"{frame_name} is stale"


def test_every_thing_the_game_can_show_has_a_sprite(sprites):
    resources = ROOT / "App" / "Resources"
    needed = set()
    for path in sorted((resources / "Levels").glob("level_*.json")):
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
