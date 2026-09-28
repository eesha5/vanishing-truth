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


# ---------------------------------------------------------------------------
# Three-direction stratum (plan 7.14): scenes that *guarantee* three visible
# mutually orthogonal directions, so the L3 camera test is applicable.
# Each prompt names a corner where two surfaces meet plus vertical edges.
# ---------------------------------------------------------------------------

_SUBJ_3D_INDOOR = [
    "the inside corner of an empty room where two walls meet the floor, skirting boards visible along both walls",
    "an empty office corner with a tiled floor, two plain walls meeting at the corner and a door frame on one wall",
    "the corner of a corridor where it turns, doors along both walls and a tiled floor",
    "an empty classroom corner with a whiteboard on one wall, windows on the other and a linoleum floor",
    "a stairwell corner with concrete steps, a handrail and two plain walls meeting",
    "the corner of a warehouse interior with steel shelving along both walls and a concrete floor",
    "an empty shop interior corner with a counter along one wall and a tiled floor",
    "the corner of a hotel room with a window on one wall, a wardrobe against the other and a carpeted floor",
]
_SUBJ_3D_OUTDOOR = [
    "the corner of a brick office building where two facades meet, rows of windows receding along both walls and a pavement below",
    "a street corner showing two facades of the same concrete building, with kerb and road markings receding",
    "the outside corner of a modern glass building, window mullions visible along both faces",
    "the corner of a car park structure with concrete beams along both faces and painted lines on the deck",
    "a building corner with a fire escape on one facade and brickwork courses receding along the other",
    "the corner of a school building with a tiled roof edge, windows along both walls and a paved yard",
    "a warehouse corner in an industrial estate with roller doors along one wall and a loading apron",
    "the corner of a town hall with stone courses along two facades and steps at the base",
]
_COND_3D = ["on an overcast day", "in flat daylight", "in bright daylight", "with even lighting"]


def three_direction(n: int, seed: int = 0):
    """Prompts whose scenes contain three visible orthogonal directions.

    Same photographic style and negative prompt as `yorkurban_matched`, so
    the two strata differ only in scene structure.
    """
    rng = random.Random(seed)
    pools = [("3d-outdoor", _SUBJ_3D_OUTDOOR), ("3d-indoor", _SUBJ_3D_INDOOR)]
    out = []
    i = 0
    while len(out) < n:
        stratum, subjects = pools[i % 2]
        subj = subjects[(i // 2) % len(subjects)]
        cond = rng.choice(_COND_3D)
        prompt = f"{subj}, {cond}, {_STYLE}".replace("  ", " ").replace(" ,", ",")
        out.append((prompt, _NEGATIVE, stratum))
        i += 1
    return out


# ---------------------------------------------------------------------------
# Three-direction stratum, v2 (plan 7.18).  The v1 corner scenes were
# line-*sparse* (empty rooms, plain walls): median 318 detected segments vs
# 426 for the street/facade stratum, so the weakest VP family often fell below
# the support threshold and the selection rate dropped to 30 %.  Every
# template below pairs the corner with at least two repeating, line-rich
# features (tiles, shelving, window grids, panelling, brick courses) so that
# all three directions carry enough line length to be identifiable.
# ---------------------------------------------------------------------------

_SUBJ_RICH_INDOOR = [
    "the corner of a tiled bathroom where two walls of square tiles meet a tiled floor, straight grout lines along both walls",
    "the corner of a warehouse aisle with tall steel shelving along both walls, a concrete floor with painted lane markings and a panelled ceiling",
    "the corner of a library reading room with bookshelves along both walls, a parquet floor and a coffered ceiling",
    "the corner of a data centre aisle with server racks along both walls, a raised floor of square panels and cable trays overhead",
    "the corner of a supermarket aisle with shelving along both walls, a tiled floor and a grid of ceiling panels",
    "the corner of a school corridor with lockers along both walls, a chequerboard tiled floor and strip lights in a panelled ceiling",
    "the corner of a gym with wall bars along both walls, a wooden floor with painted court lines and a girdered ceiling",
    "the corner of an office with floor-to-ceiling window mullions on one wall, filing cabinets along the other and a grid ceiling",
]
_SUBJ_RICH_OUTDOOR = [
    "the corner of a brick building where two facades meet, many rows of identical windows along both facades and paving slabs below",
    "the corner of a multi-storey car park, concrete beams and railings along both faces and painted parking bays on the deck",
    "the corner of a glass office tower, a dense grid of window mullions on both faces and paving stones at the base",
    "a street corner of a Victorian terrace, brick courses and sash windows along both streets and a kerb with paving slabs",
    "the corner of a warehouse with corrugated cladding on both walls, roller shutter doors and a concrete apron with expansion joints",
    "the corner of a stadium exterior with repeating concrete fins on both faces and a paved forecourt",
    "the corner of a hospital block with balcony railings along both facades and a tiled plaza below",
    "the corner of a modern apartment building with balconies stacked along both facades and block paving at street level",
]


def three_direction_rich(n: int, seed: int = 0):
    """Three visible orthogonal directions *and* high line density."""
    rng = random.Random(seed)
    pools = [("rich-outdoor", _SUBJ_RICH_OUTDOOR), ("rich-indoor", _SUBJ_RICH_INDOOR)]
    out = []
    i = 0
    while len(out) < n:
        stratum, subjects = pools[i % 2]
        subj = subjects[(i // 2) % len(subjects)]
        cond = rng.choice(_COND_3D)
        prompt = f"{subj}, {cond}, {_STYLE}".replace("  ", " ").replace(" ,", ",")
        out.append((prompt, _NEGATIVE, stratum))
        i += 1
    return out
