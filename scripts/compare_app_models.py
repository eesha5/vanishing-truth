"""Could a different classifier, or another input, give the demo app a better score?

    python scripts/compare_app_models.py

Same images, features and 5-fold protocol as train_app_model.py (applicability rule
passed, demo examples held out), AUC averaged over three fold splits.  Also checks
one shortcut that must stay out: image shape.  Every generated image here is 4:3
because the prompts asked for it, while some Commons photos are 3:2 or 16:9, so
shape alone separates the classes without any geometry.

Writes results/app_model_comparison.md.  Needs the cached features
(outputs/app_features.csv, from train_app_model.py) and the images, for their shape.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from projgeo.appmodel import make_model
from projgeo.explain import FEATURES

FOLDERS = {"real-commons": "data/real/commons", "sd15_rich": "data/generated/sd15_rich",
           "sd15_pilot": "data/generated/sd15_pilot", "sdxl_rich": "data/generated/sdxl_rich",
           "sdxl_pilot": "data/generated/sdxl_pilot", "gemini": "data/generated/gemini",
           "gptimage": "data/generated/gptimage"}
SEEDS = (0, 1, 2)


def imputer():
    return SimpleImputer(strategy="median", add_indicator=True)


MODELS = {
    "Random forest + calibration (the app)": lambda: make_model(0),
    "Random forest, no calibration": lambda: make_pipeline(imputer(), RandomForestClassifier(
        500, min_samples_leaf=3, class_weight="balanced", random_state=0, n_jobs=-1)),
    "Extra trees": lambda: make_pipeline(imputer(), ExtraTreesClassifier(
        500, min_samples_leaf=2, class_weight="balanced", random_state=0, n_jobs=-1)),
    "Gradient boosting": lambda: HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.05, max_leaf_nodes=15, class_weight="balanced", random_state=0),
    "Logistic regression": lambda: make_pipeline(imputer(), StandardScaler(), LogisticRegression(
        C=1, class_weight="balanced", max_iter=2000)),
}


def aspect(row):
    if row.set == "yorkurban":
        return 640 / 480                      # every York Urban image is 640 x 480
    w, h = Image.open(f"{FOLDERS[row.set]}/{row.path}").size
    return w / h


def cv_auc(df, make, cols, seed):
    X, y = df[cols].astype(float).values, df.is_ai.values
    p = np.zeros(len(df))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(X, y):
        p[te] = make().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, p)


def main():
    df = pd.read_csv("outputs/app_features.csv")
    held = {(e["set"], e["file"]) for e in json.loads(Path("app/examples.json").read_text(encoding="utf-8"))}
    df = df[df.admitted & ~df.apply(lambda r: (r.set, r.path) in held, axis=1)].reset_index(drop=True)
    df["aspect"] = df.apply(aspect, axis=1)

    lines = ["# Demo app model: alternatives and shortcuts", "",
             f"{len(df)} images ({(df.is_ai == 0).sum()} real, {(df.is_ai == 1).sum()} generated), "
             f"5-fold CV AUC, mean over fold seeds {', '.join(map(str, SEEDS))}.", "",
             "## Classifier, same 10 geometry features", "", "| classifier | AUC |", "|---|---|"]
    for name, make in MODELS.items():
        lines.append(f"| {name} | {np.mean([cv_auc(df, make, FEATURES, s) for s in SEEDS]):.3f} |")
    gb = MODELS["Gradient boosting"]
    lines += ["", "## Image shape (width / height): a shortcut, not used", "", "| input | AUC |", "|---|---|",
              f"| shape alone | {np.mean([cv_auc(df, gb, ['aspect'], s) for s in SEEDS]):.3f} |",
              f"| 10 features + shape | {np.mean([cv_auc(df, gb, FEATURES + ['aspect'], s) for s in SEEDS]):.3f} |",
              "", "## Each feature on its own (AUC, direction-free)", "", "| feature | AUC |", "|---|---|"]
    for f in FEATURES:
        a = roc_auc_score(df.is_ai, df[f].fillna(df[f].median()))
        lines.append(f"| {f} | {max(a, 1 - a):.3f} |")
    Path("results/app_model_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
