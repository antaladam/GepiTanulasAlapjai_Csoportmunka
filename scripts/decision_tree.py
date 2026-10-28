"""Decision tree for in-hospital death (hospdead).

    python scripts/decision_tree.py

Input:
    data/processed/train.csv, data/processed/test.csv   (unscaled: trees need no scaling)
Result, in results/decision_tree/:
    cv_results.csv            every setting tried, with mean train and cross-validation AUROC
    leaf_limit_summary.csv    per min_samples_leaf (unlimited depth): number of leaves, train
                              and cross-validation AUROC, and the gap between them
    test_metrics.csv          final test results of the chosen tree (with and without class weights)
    complexity_curve.png      train vs cross-validation AUROC by tree depth
    tree_top3.png             the top 3 levels of the chosen tree
    feature_importance.png    the most important features (up to 15, importance >= 0.001)

The tree size (max_depth, min_samples_leaf) is chosen by 5-fold cross-validation
on the training set only. The test set is used once, at the end.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # write files, no window
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier, plot_tree

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "results" / "decision_tree"

TARGET = "hospdead"
SEED = 42
PARAM_GRID = {
    "max_depth": [2, 3, 4, 5, 6, 8, 10, 15, None],
    "min_samples_leaf": [1, 10, 25, 50, 100, 200, 400],
}

# Chart colours (reference palette of the dataviz guidelines, categorical slots 1-2).
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_SOFT, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load(name):
    df = pd.read_csv(PROCESSED / name)
    return df.drop(columns=["id", TARGET]), df[TARGET]


def tune(X, y, class_weight=None):
    search = GridSearchCV(
        DecisionTreeClassifier(class_weight=class_weight, random_state=SEED),
        PARAM_GRID,
        scoring="roc_auc",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED),
        return_train_score=True,
    )
    return search.fit(X, y)


def test_metrics(name, model, X, y):
    pred = model.predict(X)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {
        "model": name,
        "max_depth": model.max_depth,
        "min_samples_leaf": model.min_samples_leaf,
        "leaves": model.get_n_leaves(),
        "auroc": roc_auc_score(y, model.predict_proba(X)[:, 1]),
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred),
        "recall": recall_score(y, pred),
        "f1": f1_score(y, pred),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def leaf_limit_summary(cv, X, y):
    """How the leaf limit alone changes tree size and scores (depth unlimited)."""
    rows = []
    for leaf in PARAM_GRID["min_samples_leaf"]:
        r = cv[(cv["param_min_samples_leaf"] == leaf) & cv["param_max_depth"].isna()].iloc[0]
        tree = DecisionTreeClassifier(min_samples_leaf=leaf, random_state=SEED).fit(X, y)
        rows.append({
            "min_samples_leaf": leaf,
            "leaves": tree.get_n_leaves(),
            "depth": tree.get_depth(),
            "train_auroc": r["mean_train_score"],
            "cv_auroc": r["mean_test_score"],
            "gap": r["mean_train_score"] - r["mean_test_score"],
        })
    return pd.DataFrame(rows)


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SOFT)
    ax.tick_params(colors=INK_SOFT)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_complexity(cv, best_leaf, path):
    """Train vs CV AUROC by depth: without a leaf limit (overfitting) and at the chosen limit."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, leaf, title in [(axes[0], 1, "min_samples_leaf = 1 (no leaf limit)"),
                            (axes[1], best_leaf, f"min_samples_leaf = {best_leaf} (chosen)")]:
        rows = cv[cv["param_min_samples_leaf"] == leaf].copy()
        rows["depth"] = rows["param_max_depth"].fillna(0).astype(int)
        rows = rows.sort_values("depth", key=lambda d: d.replace(0, 10**6))
        labels = [str(d) if d else "none" for d in rows["depth"]]
        x = range(len(rows))
        for col, colour, name in [("mean_train_score", ORANGE, "Training"),
                                  ("mean_test_score", BLUE, "Cross-validation")]:
            ax.plot(x, rows[col], color=colour, linewidth=2, marker="o", markersize=7, label=name)
            ax.annotate(name, (len(rows) - 1, rows[col].iloc[-1]), xytext=(8, 0),
                        textcoords="offset points", va="center", color=INK, fontsize=9)
        best = rows["mean_test_score"].idxmax()
        bx = list(rows.index).index(best)
        ax.annotate(f"best CV: {rows.loc[best, 'mean_test_score']:.3f}",
                    (bx, rows.loc[best, "mean_test_score"]), xytext=(0, -16),
                    textcoords="offset points", ha="center", color=INK, fontsize=9)
        ax.set_xticks(list(x), labels)
        ax.set_xlabel("max_depth", color=INK)
        ax.set_title(title, color=INK, fontsize=10, loc="left")
        style(ax)
        ax.set_xlim(-0.3, len(rows) - 1 + 2.4)  # room for the direct labels
    axes[0].set_ylabel("AUROC (mean of 5 folds)", color=INK)
    axes[0].legend(frameon=False, loc="lower left")
    fig.suptitle("Decision tree: training vs cross-validation AUROC by tree depth",
                 color=INK, fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_importance(model, features, path, top=15):
    imp = pd.Series(model.feature_importances_, index=features).sort_values().tail(top)
    imp = imp[imp >= 0.001]  # leave out features the tree barely used
    fig, ax = plt.subplots(figsize=(7.5, 0.35 * len(imp) + 1.2))
    ax.barh(imp.index, imp.values, color=BLUE, height=0.7)
    for i, v in enumerate(imp.values):
        ax.text(v, i, f" {v:.3f}", va="center", color=INK_SOFT, fontsize=9)
    ax.set_xlabel("Importance (share of total impurity reduction)", color=INK)
    ax.set_title("Decision tree: most important features", color=INK, fontsize=11, loc="left")
    style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_top_levels(model, features, path, depth=3):
    fig, ax = plt.subplots(figsize=(18, 8))
    plot_tree(model, max_depth=depth, feature_names=features, class_names=["survived", "died"],
              filled=False, impurity=False, proportion=True, rounded=True, fontsize=9, ax=ax)
    ax.set_title(f"Decision tree: top {depth} levels (value = share survived / died in the node)",
                 color=INK, fontsize=12, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    X_train, y_train = load("train.csv")
    X_test, y_test = load("test.csv")
    OUT.mkdir(parents=True, exist_ok=True)

    plain = tune(X_train, y_train)
    weighted = tune(X_train, y_train, class_weight="balanced")

    cv = pd.DataFrame(plain.cv_results_)
    cv_out = cv[["param_max_depth", "param_min_samples_leaf", "mean_train_score",
                 "mean_test_score", "std_test_score", "rank_test_score"]]
    cv_out = cv_out.rename(columns={"param_max_depth": "max_depth", "param_min_samples_leaf": "min_samples_leaf",
                                    "mean_train_score": "train_auroc", "mean_test_score": "cv_auroc",
                                    "std_test_score": "cv_auroc_std", "rank_test_score": "rank"})
    cv_out.sort_values("rank").to_csv(OUT / "cv_results.csv", index=False)
    leaf_limit_summary(cv, X_train, y_train).round(4).to_csv(OUT / "leaf_limit_summary.csv", index=False)

    metrics = pd.DataFrame([
        test_metrics("tree", plain.best_estimator_, X_test, y_test),
        test_metrics("tree, class_weight=balanced", weighted.best_estimator_, X_test, y_test),
    ])
    metrics.insert(4, "cv_auroc", [plain.best_score_, weighted.best_score_])
    metrics.round(4).to_csv(OUT / "test_metrics.csv", index=False)

    tree = plain.best_estimator_
    features = list(X_train.columns)
    plot_complexity(cv, tree.min_samples_leaf, OUT / "complexity_curve.png")
    plot_top_levels(tree, features, OUT / "tree_top3.png")
    plot_importance(tree, features, OUT / "feature_importance.png")

    print(f"best settings: {plain.best_params_}, CV AUROC {plain.best_score_:.3f}")
    print(metrics.drop(columns=["tn", "fp", "fn", "tp"]).round(3).to_string(index=False))
    print(f"files written to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
