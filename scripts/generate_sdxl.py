"""Generate a content-matched image set with a local diffusion model.

    python scripts/generate_sdxl.py --n 200 --out data/generated/sdxl_pilot
    python scripts/generate_sdxl.py --model sd15 --n 200 --out data/generated/sd15_pilot

Every image gets a JSONL record with model id, prompt, seed, steps, CFG,
resolution, sampler and timestamp (plan section 3.6: log everything).
Re-running resumes: images already listed in metadata.jsonl are skipped.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

from projgeo.prompts import three_direction, three_direction_rich, yorkurban_matched

STRATA = {"yorkurban": yorkurban_matched, "three_direction": three_direction,
          "three_direction_rich": three_direction_rich}

MODELS = {
    "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
    "sd15": "stable-diffusion-v1-5/stable-diffusion-v1-5",
}


def load_pipeline(name: str):
    from diffusers import DiffusionPipeline
    pipe = DiffusionPipeline.from_pretrained(MODELS[name], torch_dtype=torch.float16,
                                             use_safetensors=True, variant="fp16")
    # 8 GB card: keep only the active sub-model on the GPU
    pipe.enable_model_cpu_offload()
    if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_slicing"):
        pipe.vae.enable_slicing()
    pipe.set_progress_bar_config(disable=True)
    return pipe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sdxl", choices=list(MODELS))
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--out", default="data/generated/sdxl_pilot")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--cfg", type=float, default=6.0)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--stratum", default="yorkurban", choices=list(STRATA))
    args = ap.parse_args()
    if args.model == "sd15" and args.width == 1024:
        args.width, args.height = 640, 480

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log = out / "metadata.jsonl"
    done = set()
    if log.exists():
        done = {json.loads(l)["file"] for l in log.read_text().splitlines() if l.strip()}

    pipe = load_pipeline(args.model)
    prompts = STRATA[args.stratum](args.n, seed=0)
    t0 = time.time()
    n_new = 0
    with log.open("a") as fh:
        for i, (prompt, neg, stratum) in enumerate(prompts):
            fname = f"{args.model}_{i:04d}.png"
            if fname in done:
                continue
            seed = args.seed + i
            g = torch.Generator("cuda").manual_seed(seed)
            img = pipe(prompt=prompt, negative_prompt=neg, width=args.width, height=args.height,
                       num_inference_steps=args.steps, guidance_scale=args.cfg,
                       generator=g).images[0]
            img.save(out / fname)
            rec = {"file": fname, "model": MODELS[args.model], "prompt": prompt,
                   "negative_prompt": neg, "stratum": stratum, "seed": seed,
                   "steps": args.steps, "cfg": args.cfg, "width": args.width,
                   "prompt_set": args.stratum,
                   "height": args.height, "scheduler": type(pipe.scheduler).__name__,
                   "date": datetime.now(timezone.utc).isoformat()}
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            n_new += 1
            print(f"[{i + 1}/{len(prompts)}] {fname}  {(time.time() - t0) / n_new:.1f}s/img", flush=True)


if __name__ == "__main__":
    main()
