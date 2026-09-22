"""Phase 2b: real photographs from many different cameras (Wikimedia Commons).

    python scripts/collect_commons.py --per-query 60 --out data/real/commons

Searches Commons for the same content strata as the generated sets, keeps
JPEGs that carry EXIF camera model + focal length (so each photo comes from
an identifiable real camera), landscape aspect between 1.2 and 1.8, width
>= 1024 and EXIF orientation 1/absent, and downloads the 1024-px rendition.
metadata.jsonl records title, page URL, licence, author, camera, focal
length (mm and 35 mm-equivalent) and an approximate pixel focal length
f_px = width * f35 / 36 when the 35 mm-equivalent focal is present.
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = "projgeo-research/0.1 (student computer-vision project; python-requests)"

QUERIES = {
    "outdoor": [
        "building facade windows street photograph",
        "city street buildings sidewalk photograph",
        "office building exterior glass facade",
        "brick building rows of windows",
        "university campus building exterior",
        "terraced houses street",
        "parking garage concrete pillars",
    ],
    "indoor": [
        "corridor interior doors fluorescent",
        "hallway interior building",
        "lecture hall interior seats",
        "office interior desk shelves",
        "stairwell interior handrail",
        "computer lab interior desks",
        "lobby interior building elevator",
        "seminar room interior table chairs",
    ],
}


def api(session, **params):
    params.update({"format": "json", "formatversion": "2"})
    for attempt in range(4):
        try:
            r = session.get(API, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            time.sleep(2 * (attempt + 1))
    return {}


def search_titles(session, query, n):
    titles, offset = [], 0
    while len(titles) < n:
        d = api(session, action="query", list="search", srnamespace=6, srlimit=50,
                sroffset=offset, srsearch=f"{query} filemime:image/jpeg")
        hits = d.get("query", {}).get("search", [])
        if not hits:
            break
        titles += [h["title"] for h in hits]
        offset += len(hits)
        if "continue" not in d:
            break
        time.sleep(0.3)
    return titles[:n]


def _num(v):
    """EXIF rationals arrive as '50/1' or '4.5' strings; return float or None."""
    if v is None:
        return None
    try:
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        if "/" in s:
            a, b = s.split("/")
            return float(a) / float(b)
        m = re.match(r"[-+]?\d*\.?\d+", s)
        return float(m.group()) if m else None
    except (ValueError, ZeroDivisionError):
        return None


def image_infos(session, titles):
    out = []
    for i in range(0, len(titles), 25):
        chunk = titles[i:i + 25]
        d = api(session, action="query", titles="|".join(chunk), prop="imageinfo",
                iiprop="url|size|mime|metadata|extmetadata", iiurlwidth=1024)
        for p in d.get("query", {}).get("pages", []):
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]
            md = {m["name"]: m["value"] for m in (ii.get("metadata") or []) if isinstance(m, dict)}
            ext = ii.get("extmetadata") or {}
            out.append({"pageid": p["pageid"], "title": p["title"], "ii": ii, "md": md, "ext": ext})
        time.sleep(0.3)
    return out


def accept(rec):
    ii, md = rec["ii"], rec["md"]
    if ii.get("mime") != "image/jpeg":
        return False
    w, h = ii.get("width", 0), ii.get("height", 0)
    if w < 1024 or h < 600 or not (1.2 <= w / max(h, 1) <= 1.8):
        return False
    if not md.get("Model") or _num(md.get("FocalLength")) is None:
        return False
    if _num(md.get("Orientation")) not in (None, 1.0):
        return False
    if "thumburl" not in ii:
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=60)
    ap.add_argument("--out", default="data/real/commons")
    ap.add_argument("--max-total", type=int, default=400)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log = out / "metadata.jsonl"
    have = set()
    if log.exists():
        have = {json.loads(l)["pageid"] for l in log.read_text(encoding="utf-8").splitlines() if l.strip()}

    s = requests.Session()
    s.headers["User-Agent"] = UA
    n_new = 0
    with log.open("a", encoding="utf-8") as fh:
        for stratum, queries in QUERIES.items():
            for q in queries:
                titles = search_titles(s, q, args.per_query * 3)
                kept = 0
                for rec in image_infos(s, titles):
                    if kept >= args.per_query or len(have) >= args.max_total:
                        break
                    if rec["pageid"] in have or not accept(rec):
                        continue
                    ii, md, ext = rec["ii"], rec["md"], rec["ext"]
                    try:
                        r = s.get(ii["thumburl"], timeout=60)
                        r.raise_for_status()
                    except Exception:
                        continue
                    fname = f"{rec['pageid']}.jpg"
                    (out / fname).write_bytes(r.content)
                    f35 = _num(md.get("FocalLengthIn35mmFilm"))
                    tw = ii.get("thumbwidth", 1024)
                    meta = {
                        "file": fname, "pageid": rec["pageid"], "title": rec["title"],
                        "page_url": ii.get("descriptionurl"), "stratum": stratum, "query": q,
                        "license": (ext.get("LicenseShortName") or {}).get("value"),
                        "author": re.sub("<[^>]+>", "", (ext.get("Artist") or {}).get("value", ""))[:120],
                        "camera_make": md.get("Make"), "camera_model": md.get("Model"),
                        "focal_mm": _num(md.get("FocalLength")), "focal_35mm": f35,
                        "orig_width": ii.get("width"), "orig_height": ii.get("height"),
                        "thumb_width": tw, "thumb_height": ii.get("thumbheight"),
                        "f_px_est": (tw * f35 / 36.0) if f35 else None,
                    }
                    fh.write(json.dumps(meta, ensure_ascii=False) + "\n")
                    fh.flush()
                    have.add(rec["pageid"])
                    kept += 1
                    n_new += 1
                    time.sleep(0.4)
                print(f"{stratum:8s} '{q}': kept {kept}  (total {len(have)})", flush=True)
                if len(have) >= args.max_total:
                    break
    print("new images:", n_new, " total:", len(have))


if __name__ == "__main__":
    main()
