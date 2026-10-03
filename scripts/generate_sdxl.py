"""Generate a content-matched image set with a local diffusion model.

    python scripts/generate_sdxl.py --n 200 --out data/generated/sdxl_pilot
    python scripts/generate_sdxl.py --model sd15 --n 200 --out data/generated/sd15_pilot
    python scripts/generate_sdxl.py --model flux --stratum three_direction_rich --n 250 --out data/generated/flux_rich

Flux (FLUX.1-schnell) does not fit an 8 GB card at full precision, so it runs in two
phases: the T5 text encoder (9 GB) encodes every pending prompt with its weights streamed
through the GPU, then a 4-bit GGUF copy of the transformer (6.3 GB), streamed block by block,
makes the images (about 55 s each on an 8 GB laptop GPU).
The official repo is gated (licence accepted on huggingface.co, then `hf auth login`).

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
    "flux": "black-forest-labs/FLUX.1-schnell",
}
FLUX_GGUF = ("city96/FLUX.1-schnell-gguf", "flux1-schnell-Q4_K_S.gguf")
FLUX_TOKENS = 256        # schnell's maximum prompt length; our prompts are far shorter


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


def flux_encode(prompts: list[str], batch: int = 16):
    """Phase 1: T5 + CLIP embeddings for every prompt, kept on the CPU."""
    from diffusers import FluxPipeline
    enc = FluxPipeline.from_pretrained(MODELS["flux"], transformer=None, vae=None,
                                       torch_dtype=torch.bfloat16)
    enc.enable_sequential_cpu_offload()      # T5 is larger than the card: stream its layers
    embeds = []
    with torch.no_grad():
        for k in range(0, len(prompts), batch):
            pe, pooled, _ = enc.encode_prompt(prompts[k:k + batch], prompt_2=None,
                                              max_sequence_length=FLUX_TOKENS)
            embeds += list(zip(pe.cpu(), pooled.cpu()))
    del enc
    torch.cuda.empty_cache()
    return embeds


def load_flux():
    """Phase 2: 4-bit transformer + VAE, no text encoders."""
    from diffusers import FluxPipeline, FluxTransformer2DModel, GGUFQuantizationConfig
    from huggingface_hub import hf_hub_download
    transformer = FluxTransformer2DModel.from_single_file(
        hf_hub_download(*FLUX_GGUF), config=MODELS["flux"], subfolder="transformer",
        quantization_config=GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
        torch_dtype=torch.bfloat16)
    pipe = FluxPipeline.from_pretrained(MODELS["flux"], transformer=transformer, text_encoder=None,
                                        text_encoder_2=None, tokenizer=None, tokenizer_2=None,
                                        torch_dtype=torch.bfloat16)
    # The 6.3 GB transformer plus activations just exceeds 8 GB, and Windows then spills into shared
    # memory (150 s per step).  Streaming blocks onto the GPU as needed keeps it near 2 GB: 12 s per step.
    transformer.enable_group_offload(onload_device=torch.device("cuda"), offload_device=torch.device("cpu"),
                                     offload_type="block_level", num_blocks_per_group=4, use_stream=True)
    pipe.vae.to("cuda")
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
    ap.add_argument("--limit", type=int, default=None, help="stop after this many new images (test runs)")
    args = ap.parse_args()
    if args.model == "sd15" and args.width == 1024:
        args.width, args.height = 640, 480
    if args.model == "flux":     # schnell is distilled for 4 steps without guidance
        args.steps, args.cfg = 4, 0.0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log = out / "metadata.jsonl"
    done = set()
    if log.exists():
        done = {json.loads(l)["file"] for l in log.read_text().splitlines() if l.strip()}

    prompts = STRATA[args.stratum](args.n, seed=0)
    todo = [(i, p) for i, p in enumerate(prompts) if f"{args.model}_{i:04d}.png" not in done]
    todo = todo[:args.limit]
    if args.model == "flux":
        embeds = flux_encode([p[0] for _, p in todo])
        pipe = load_flux()
    else:
        pipe = load_pipeline(args.model)
    t0 = time.time()
    n_new = 0
    with log.open("a") as fh:
        for k, (i, (prompt, neg, stratum)) in enumerate(todo):
            fname = f"{args.model}_{i:04d}.png"
            seed = args.seed + i
            g = torch.Generator("cuda").manual_seed(seed)
            common = {"width": args.width, "height": args.height, "num_inference_steps": args.steps,
                      "guidance_scale": args.cfg, "generator": g}
            if args.model == "flux":     # no negative prompt: schnell has no classifier-free guidance
                neg = None
                pe, pooled = embeds[k]
                img = pipe(prompt_embeds=pe[None].to("cuda"), pooled_prompt_embeds=pooled[None].to("cuda"),
                           max_sequence_length=FLUX_TOKENS, **common).images[0]
            else:
                img = pipe(prompt=prompt, negative_prompt=neg, **common).images[0]
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
