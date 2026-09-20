"""Prompt strata for content-matched generation (plan section 3.4).

`yorkurban_matched` mirrors the YorkUrban content: a university campus and
downtown Toronto -- brick and concrete building facades, corridors, lecture
halls, offices, stairwells, streets with storefronts -- photographed with a
consumer point-and-shoot at 4:3.  Photorealistic only; no stylised prompts.
"""

import random

_SUBJECTS_OUTDOOR = [
    "the brick facade of a university building with rows of rectangular windows",
    "a downtown street with three-storey brick storefronts and parked cars",
    "a concrete campus building with a covered walkway and square columns",
    "a modern glass office building seen from the sidewalk across the street",
    "an old stone library building with tall windows and a flight of steps",
    "a row of terraced brick houses along a straight residential street",
    "a parking garage entrance with concrete pillars and painted lines",
    "a pedestrian plaza between two rectangular office buildings",
    "a corner of a city block with a cafe on the ground floor",
    "a loading dock behind a warehouse with roll-up doors",
]
_SUBJECTS_INDOOR = [
    "a long corridor in a university building with doors on both sides and fluorescent lights",
    "an empty lecture hall with rows of fixed seats and a whiteboard at the front",
    "an office with a desk, filing cabinets, bookshelves and a window",
    "a stairwell with concrete steps and a metal handrail",
    "a hallway junction with lockers, notice boards and a drinking fountain",
    "a computer lab with rows of desks and monitors",
    "an atrium with a tiled floor, balconies and a glass ceiling",
    "a seminar room with a long table, chairs and a projector screen",
    "a building lobby with an elevator bank and a reception desk",
    "a laboratory bench with cabinets above and equipment on the counter",
]
_COND_OUT = ["on an overcast afternoon", "in bright sunlight with hard shadows",
             "in the early morning", "on a clear day"]
_COND_IN = ["with fluorescent lighting", "with daylight from the windows",
            "in the evening with the lights on", ""]
_STYLE = ("photograph taken with a compact digital camera, 4:3, wide angle, "
          "realistic, sharp focus, no people")
_NEGATIVE = ("painting, illustration, cartoon, render, cgi, fisheye, tilt-shift, "
             "panorama, blurry, text, watermark, people")


def yorkurban_matched(n: int, seed: int = 0):
    """Return n (prompt, negative_prompt, stratum) triples, alternating
    outdoor / indoor and cycling through subjects and lighting conditions."""
    rng = random.Random(seed)
    pools = [("outdoor", _SUBJECTS_OUTDOOR, _COND_OUT), ("indoor", _SUBJECTS_INDOOR, _COND_IN)]
    out = []
    i = 0
    while len(out) < n:
        stratum, subjects, conds = pools[i % 2]
        subj = subjects[(i // 2) % len(subjects)]
        cond = rng.choice(conds)
        prompt = f"{subj} {cond}, {_STYLE}".replace("  ", " ").replace(" ,", ",")
        out.append((prompt, _NEGATIVE, stratum))
        i += 1
    return out
