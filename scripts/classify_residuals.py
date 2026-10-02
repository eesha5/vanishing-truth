"""Detect generated images from geometric residuals alone (syllabus Unit 3:
classification algorithms; research: comparison with Sarkar et al.'s learned
classifiers on geometric features).

    python scripts/classify_residuals.py --csv results/four_set_summary.csv

Every classifier sees only the per-image residual vector produced by the
constraint suite - never pixels.  Feature groups are ablated because some
columns describe the *camera configuration* or the *content* rather than a
violation of projective geometry, and a classifier that wins on those has not
detected geometric inconsistency:

  L2         line concurrency residuals and VP bootstrap uncertainty
  ATLANTA    focal consistency over (horizontal, vertical) VP pairs only (plan 7.20)
  MANHATTAN  three-VP orthogonality and orthocentre (valid measurement, but
             penalises real non-Manhattan scenes; plan 7.20)
  LOCALITY   residual variogram indices
  NUISANCE   fitted HFOV, distortion k1, segment count, VP counts
             (configuration / content - reported separately, never in "geometry")

Excluded from every geometry condition (plan 7.22, 7.24): features that turn
VP pairs into focal lengths without knowing the pair is perpendicular -
f_spread, f_boot_cv, n_negative_f2 - and the REGIONAL group, whose per-window
camera comes from camera.fit_focal (one f making *all* VPs mutually
orthogonal), an assumption that is untested on Atlanta-world scenes.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score, roc_curve

GROUPS = {
    "L2": ["l2_rms_deg", "l2_mean_deg", "l2_capped_mean_deg", "l2_unexplained_frac", "n_outliers",
           "vp_std_max_deg"],
    "ATLANTA": ["atl_logf_spread", "atl_frac_impossible"],
    "MANHATTAN": ["ortho_err_max_deg", "ortho_err_rms_deg", "orthocenter_offset", "ortho_err_max_boot_std"],
    "LOCALITY": ["loc_index", "loc_rho_near", "loc_rho_far", "loc_index_undist"],
    "NUISANCE": ["hfov_deg", "f_fit", "k1", "n_segments", "n_vps", "n_reliable_vps", "atl_n_pairs"],
}
GEOMETRY = ["L2", "ATLANTA", "MANHATTAN", "LOCALITY"]
EXCLUDED = ["f_spread", "f_boot_cv", "n_negative_f2"]   # + every reg_* column, see module docstring


def join_atlanta(df, atlanta_csv):
    """Attach Atlanta residuals (computed only for images that pass the
    applicability rule) and a `selected` flag."""
    a = pd.read_csv(atlanta_csv)
    a["set"] = a.set.replace({"yorkurban": "real"})
    a = a.rename(columns={"logf_spread": "atl_logf_spread", "frac_impossible": "atl_frac_impossible",
                          "n_pairs": "atl_n_pairs"})[["set", "path", "atl_logf_spread",
                                                      "atl_frac_impossible", "atl_n_pairs"]]
    a["selected"] = True
    df = df.merge(a, on=["set", "path"], how="left")
    df["selected"] = df.selected.fillna(False).astype(bool)
    return df

MODELS = {
    "logistic regression": LogisticRegression(max_iter=2000, C=1.0),
    "decision tree": DecisionTreeClassifier(max_depth=4, random_state=0),
    "SVM (RBF)": SVC(probability=True, random_state=0),
    "random forest": RandomForestClassifier(n_estimators=400, min_samples_leaf=2, random_state=0),
    "naive Bayes": GaussianNB(),
    "k-nearest neighbours": KNeighborsClassifier(n_neighbors=15),
}


def make_pipe(model):
    return Pipeline([("impute", SimpleImputer(strategy="median")),
                     ("scale", StandardScaler()),
                     ("clf", model)])


def evaluate(X, y, seed=0):
    """5-fold stratified CV AUC (mean +- sd over folds) for every model."""
    out = {}
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    for name, model in MODELS.items():
        aucs = []
        for tr, te in cv.split(X, y):
            p = make_pipe(model).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
            aucs.append(roc_auc_score(y[te], p))
        out[name] = (float(np.mean(aucs)), float(np.std(aucs)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/four_set_summary.csv")
    ap.add_argument("--out", default="outputs/classify")
    ap.add_argument("--hfov-band", nargs=2, type=float, default=[40, 60])
    ap.add_argument("--atlanta", default="results/frontier.csv",
                    help="per-image Atlanta residuals (atlanta_compare.py output)")
    ap.add_argument("--selected-only", action="store_true",
                    help="only images that pass the applicability rule")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df = join_atlanta(pd.read_csv(args.csv), args.atlanta)
    if args.selected_only:
        df = df[df.selected]
    df["generated"] = df.set.isin(["sd15_pilot", "sdxl_pilot"]).astype(int)
    tasks = {
        "curated real (YorkUrban) vs SDXL": df[df.set.isin(["real", "sdxl_pilot"])],
        "curated real (YorkUrban) vs SD 1.5": df[df.set.isin(["real", "sd15_pilot"])],
        "wild real (Commons) vs SDXL": df[df.set.isin(["real-commons", "sdxl_pilot"])],
        "all real vs all generated": df,
        f"HFOV {args.hfov_band[0]:.0f}-{args.hfov_band[1]:.0f}, all real vs generated":
            df[(df.hfov_deg >= args.hfov_band[0]) & (df.hfov_deg <= args.hfov_band[1])],
    }

    report = {}
    lines = ["# Geometric-residual classifiers (no pixels)", "",
             f"Images: {'selected only (pass the applicability rule)' if args.selected_only else 'all'}. "
             f"Excluded as assumption-dependent: {', '.join(EXCLUDED)}, all reg_* columns.", ""]
    for task, d in tasks.items():
        y = d.generated.values
        feat_geom = [c for g in GEOMETRY for c in GROUPS[g] if c in d]
        feat_all = feat_geom + [c for c in GROUPS["NUISANCE"] if c in d]
        res_geom = evaluate(d[feat_geom].astype(float).values, y)
        res_all = evaluate(d[feat_all].astype(float).values, y)
        report[task] = {"n_real": int((y == 0).sum()), "n_gen": int((y == 1).sum()),
                        "geometry": res_geom, "geometry+nuisance": res_all}
        lines += [f"## {task}  (n real = {(y == 0).sum()}, n generated = {(y == 1).sum()})", "",
                  "| classifier | AUC, geometry only | AUC, + camera/content features |", "|---|---|---|"]
        for m in MODELS:
            lines.append(f"| {m} | {res_geom[m][0]:.3f} ± {res_geom[m][1]:.3f} | "
                         f"{res_all[m][0]:.3f} ± {res_all[m][1]:.3f} |")
        lines.append("")

        # single-group ablation on the same task (random forest)
        abl = {}
        for g in GEOMETRY:
            cols = [c for c in GROUPS[g] if c in d]
            abl[g] = evaluate(d[cols].astype(float).values, y)["random forest"][0]
        cols_nu = [c for c in GROUPS["NUISANCE"] if c in d]
        abl["NUISANCE"] = evaluate(d[cols_nu].astype(float).values, y)["random forest"][0]
        report[task]["group_auc_rf"] = abl
        lines += ["Random-forest AUC from each feature group alone: " +
                  ", ".join(f"**{g}** {v:.3f}" for g, v in abl.items()), ""]

    # feature importance + ROC for the headline task
    d = tasks["curated real (YorkUrban) vs SDXL"]
    y = d.generated.values
    feat_geom = [c for g in GEOMETRY for c in GROUPS[g] if c in d]
    X = d[feat_geom].astype(float).values
    # held-out permutation importance, averaged over folds (fitting and
    # scoring on the same data saturates the forest and hides every feature)
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    imps = []
    for tr, te in cv.split(X, y):
        pipe = make_pipe(MODELS["random forest"]).fit(X[tr], y[tr])
        imps.append(permutation_importance(pipe, X[te], y[te], n_repeats=20,
                                           random_state=0, scoring="roc_auc").importances_mean)
    imp_mean = np.mean(imps, axis=0)
    order = np.argsort(-imp_mean)[:12]
    lines += ["## Permutation importance (random forest, curated real vs SDXL)", "",
              "| feature | drop in AUC when shuffled |", "|---|---|"]
    for i in order:
        lines.append(f"| {feat_geom[i]} | {imp_mean[i]:.3f} |")
    report["importance"] = {feat_geom[i]: float(imp_mean[i]) for i in order}

    (out / "classifier_report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "classifier_report.json").write_text(json.dumps(report, indent=1))
    print("\n".join(lines))

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, (task, d) in zip(axes, [("curated real (YorkUrban) vs SDXL", tasks["curated real (YorkUrban) vs SDXL"]),
                                    ("wild real (Commons) vs SDXL", tasks["wild real (Commons) vs SDXL"])]):
        y = d.generated.values
        feats = [c for g in GEOMETRY for c in GROUPS[g] if c in d]
        X = d[feats].astype(float).values
        for m in ("logistic regression", "random forest", "SVM (RBF)"):
            p = cross_val_predict(make_pipe(MODELS[m]), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=0),
                                  method="predict_proba")[:, 1]
            fpr, tpr, _ = roc_curve(y, p)
            ax.plot(fpr, tpr, label=f"{m} (AUC {roc_auc_score(y, p):.2f})")
        ax.plot([0, 1], [0, 1], "k--", lw=.8)
        ax.set_xlabel("false positive rate")
        ax.set_ylabel("true positive rate")
        ax.set_title(task, fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(alpha=.3)
    fig.suptitle("Detecting generated images from geometric residuals only")
    fig.tight_layout()
    fig.savefig(out / "roc.png", dpi=110)


if __name__ == "__main__":
    main()
