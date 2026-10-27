"""Clean SUPPORT2, split it once, and write ready-to-use model inputs.

    python scripts/prepare_data.py

Input:
    data/raw/support2.csv               (from scripts/download_data.py)
Result, in data/processed/:
    support2_clean.csv                  all 9,105 patients, 29 features, gaps
                                        still visible (for describing the data)
    train.csv, test.csv                 no gaps, categories one-hot encoded;
                                        for decision trees and ensembles
    train_scaled.csv, test_scaled.csv   same, measured numeric columns standardised
                                        (0/1 columns stay 0/1);
                                        for logistic regression, kNN, SVM, MLP
Every model file has the columns id, hospdead (the target) and the features.
Use id only to identify patients, never as a feature.

Medians, most common values, means and standard deviations are computed from
the training patients only and then applied to both files, so the test
patients never influence the preprocessing.
"""
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "support2.csv"
PROCESSED = ROOT / "data" / "processed"

TARGET = "hospdead"
TEST_SIZE = 0.25
SEED = 42

# Known only after study entry, or derived from the outcome: never used as features.
LEAKAGE = [
    "death", "d.time", "slos", "sfdm2",          # outcome and follow-up
    "charges", "totcst", "totmcst",              # costs, known after discharge
    "surv2m", "surv6m", "prg2m", "prg6m",        # SUPPORT model and physician survival estimates
    "dnr", "dnrday",                             # DNR order, mostly given during the stay
    "avtisst",                                   # treatment intensity averaged over days 3-25
]
# Not leakage, but left out: dzclass is a coarser grouping of dzgroup; adls is
# replaced by adlsc (the study's imputed version, no missing values); adlp is
# missing for 62% of patients.
REDUNDANT = ["dzclass", "adls", "adlp"]

# Normal values for missing lab results, as recommended by the dataset author
# (Frank Harrell, see the UCI page): a missing test usually means it was not
# ordered because a normal result was expected.
NORMAL_FILL = {
    "alb": 3.5,
    "pafi": 333.3,
    "bili": 1.01,
    "crea": 1.01,
    "bun": 6.51,
    "wblc": 9.0,
    "urine": 2502.0,
}
INCOME_RANK = {"under $11k": 0, "$11-$25k": 1, "$25-$50k": 2, ">$50k": 3}

NUMERIC = [
    "age", "num.co", "edu", "income", "scoma", "sps", "aps", "hday",
    "diabetes", "dementia", "adlsc",
    "meanbp", "wblc", "hrt", "resp", "temp", "pafi", "alb", "bili", "crea",
    "sod", "ph", "glucose", "bun", "urine",
]
CATEGORICAL = ["sex", "dzgroup", "race", "ca"]
# Yes/no features stored as 0/1 stay 0/1 in the scaled files, like the one-hot columns.
BINARY = ["diabetes", "dementia"]
SCALED = [c for c in NUMERIC if c not in BINARY]


def clean(df):
    """Fixed rules that learn nothing from the data."""
    df = df.drop(columns=LEAKAGE + REDUNDANT)
    df = df.fillna(NORMAL_FILL)
    df["income"] = df["income"].map(INCOME_RANK)  # missing stays missing
    return df


def fill_gaps(train, test):
    """Fill remaining gaps with the training median (numbers) or most common value (categories)."""
    fill = {c: train[c].median() for c in NUMERIC}
    fill |= {c: train[c].mode()[0] for c in CATEGORICAL}
    return train.fillna(fill), test.fillna(fill)


def one_hot(df):
    """One 0/1 column per category; sex becomes a single sex_male column."""
    df = pd.get_dummies(df, columns=["sex"], drop_first=True, dtype=int)
    return pd.get_dummies(df, columns=["dzgroup", "race", "ca"], dtype=int)


def scale(train, test):
    """Standardise measured numeric columns with the training mean and standard deviation."""
    mean, std = train[SCALED].mean(), train[SCALED].std(ddof=0)
    train, test = train.copy(), test.copy()
    train[SCALED] = (train[SCALED] - mean) / std
    test[SCALED] = (test[SCALED] - mean) / std
    return train, test


def main():
    df = clean(pd.read_csv(RAW))
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "support2_clean.csv", index=False)

    train, test = train_test_split(df, test_size=TEST_SIZE, stratify=df[TARGET], random_state=SEED)
    train, test = train.sort_values("id"), test.sort_values("id")
    train, test = fill_gaps(train, test)
    train, test = one_hot(train), one_hot(test)
    test = test.reindex(columns=train.columns, fill_value=0)  # same columns even if a category is absent
    train.to_csv(PROCESSED / "train.csv", index=False)
    test.to_csv(PROCESSED / "test.csv", index=False)

    train_s, test_s = scale(train, test)
    train_s.to_csv(PROCESSED / "train_scaled.csv", index=False)
    test_s.to_csv(PROCESSED / "test_scaled.csv", index=False)

    print(f"support2_clean.csv: {len(df):,} patients, {df.shape[1] - 2} features")
    print(f"model files: {train.shape[1] - 2} feature columns after one-hot encoding")
    for name, part in [("train", train), ("test", test)]:
        print(f"{name}: {len(part):,} patients, {part[TARGET].mean():.1%} died in hospital")


if __name__ == "__main__":
    main()
