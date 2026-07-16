"""Massive predictive model registry — 100+ sklearn / boosting / ensemble variants."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from sklearn.base import BaseEstimator

ProblemKind = Literal["classification", "regression"]
SpeedTier = Literal["fast", "medium", "slow"]


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    family: str
    problem_type: ProblemKind
    speed: SpeedTier
    factory: Callable[[], BaseEstimator]
    min_samples: int = 10
    max_samples: int | None = None
    needs_proba: bool = False


def _try_import(name: str):
    try:
        return __import__(name)
    except ImportError:
        return None


def _classification_specs() -> list[ModelSpec]:
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.discriminant_analysis import (
        LinearDiscriminantAnalysis,
        QuadraticDiscriminantAnalysis,
    )
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import (
        AdaBoostClassifier,
        BaggingClassifier,
        ExtraTreesClassifier,
        GradientBoostingClassifier,
        HistGradientBoostingClassifier,
        RandomForestClassifier,
        VotingClassifier,
    )
    from sklearn.linear_model import (
        LogisticRegression,
        PassiveAggressiveClassifier,
        Perceptron,
        RidgeClassifier,
        SGDClassifier,
    )
    from sklearn.naive_bayes import BernoulliNB, ComplementNB, GaussianNB, MultinomialNB
    from sklearn.neighbors import KNeighborsClassifier, RadiusNeighborsClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC, LinearSVC, NuSVC
    from sklearn.tree import DecisionTreeClassifier, ExtraTreeClassifier

    specs: list[ModelSpec] = []

    def add(
        id_: str,
        name: str,
        family: str,
        factory: Callable[[], BaseEstimator],
        speed: SpeedTier = "medium",
        min_samples: int = 10,
        max_samples: int | None = None,
    ):
        specs.append(
            ModelSpec(
                id=id_,
                name=name,
                family=family,
                problem_type="classification",
                speed=speed,
                factory=factory,
                min_samples=min_samples,
                max_samples=max_samples,
            )
        )

    # --- Linear ---
    for c in (0.001, 0.01, 0.1, 1.0, 10.0, 100.0):
        add(
            f"lr_l2_c{c}",
            f"Logistic Regression (C={c})",
            "linear",
            lambda c=c: LogisticRegression(C=c, max_iter=2000),
            "fast",
        )
    for c in (0.1, 1.0, 10.0):
        add(
            f"lr_l1_c{c}",
            f"Logistic Regression L1 (C={c})",
            "linear",
            lambda c=c: LogisticRegression(
                C=c, penalty="l1", solver="liblinear", max_iter=2000
            ),
            "fast",
        )
    for alpha in (0.0001, 0.001, 0.01, 0.1):
        add(
            f"sgd_hinge_a{alpha}",
            f"SGD Hinge (α={alpha})",
            "linear",
            lambda a=alpha: SGDClassifier(
                loss="hinge", alpha=a, max_iter=1500),
            "fast",
        )
    for alpha in (0.0001, 0.01, 0.1):
        add(
            f"sgd_log_a{alpha}",
            f"SGD Log Loss (α={alpha})",
            "linear",
            lambda a=alpha: SGDClassifier(
                loss="log_loss", alpha=a, max_iter=1500),
            "fast",
        )
    for c in (0.1, 1.0, 10.0):
        add(
            f"ridge_c{c}",
            f"Ridge Classifier (α={c})",
            "linear",
            lambda c=c: RidgeClassifier(alpha=c),
            "fast",
        )
    for c in (0.1, 1.0, 10.0):
        add(
            f"linearsvc_c{c}",
            f"Linear SVC (C={c})",
            "linear",
            lambda c=c: LinearSVC(C=c, max_iter=3000),
            "medium",
        )
    add("perceptron", "Perceptron", "linear",
        lambda: Perceptron(max_iter=1500), "fast")
    for c in (0.01, 0.1, 1.0):
        add(
            f"passive_aggressive_c{c}",
            f"Passive Aggressive (C={c})",
            "linear",
            lambda c=c: PassiveAggressiveClassifier(C=c, max_iter=1500),
            "fast",
        )

    # --- SVM ---
    for kernel in ("linear", "rbf", "poly"):
        for c in (0.1, 1.0, 10.0):
            add(
                f"svc_{kernel}_c{c}",
                f"SVC {kernel} (C={c})",
                "svm",
                lambda k=kernel, c=c: SVC(kernel=k, C=c, probability=True),
                "slow",
                max_samples=50_000,
            )
    for nu in (0.3, 0.5, 0.7):
        add(
            f"nusvc_nu{nu}",
            f"Nu-SVC (ν={nu})",
            "svm",
            lambda n=nu: NuSVC(nu=n, probability=True),
            "slow",
            max_samples=30_000,
        )

    # --- Neighbors ---
    for k in (3, 5, 7, 9, 11, 15, 21):
        add(
            f"knn_k{k}",
            f"KNN (k={k})",
            "neighbors",
            lambda k=k: KNeighborsClassifier(n_neighbors=k),
            "fast",
            max_samples=20_000,
        )
    add(
        "radius_nn",
        "Radius Neighbors",
        "neighbors",
        lambda: RadiusNeighborsClassifier(),
        "medium",
        max_samples=10_000,
    )

    # --- Trees ---
    for depth in (3, 5, 8, 12, 20, None):
        d = depth if depth else "None"
        add(
            f"dt_depth{d}",
            f"Decision Tree (depth={d})",
            "tree",
            lambda dep=depth: DecisionTreeClassifier(max_depth=dep),
            "fast",
        )
    add("extra_tree", "Extra Tree", "tree",
        lambda: ExtraTreeClassifier(), "fast")

    for n in (50, 100, 200, 300):
        for depth in (5, 10, 20):
            add(
                f"rf_{n}_d{depth}",
                f"Random Forest ({n}, d={depth})",
                "ensemble",
                lambda ne=n, dep=depth: RandomForestClassifier(
                    n_estimators=ne, max_depth=dep, n_jobs=-1
                ),
                "medium",
            )
    for n in (50, 100, 200):
        add(
            f"et_{n}",
            f"Extra Trees ({n})",
            "ensemble",
            lambda ne=n: ExtraTreesClassifier(n_estimators=ne, n_jobs=-1),
            "medium",
        )
    for n in (50, 100, 150):
        for lr in (0.05, 0.1):
            add(
                f"gb_{n}_lr{lr}",
                f"Gradient Boosting ({n}, lr={lr})",
                "boosting",
                lambda ne=n, r=lr: GradientBoostingClassifier(
                    n_estimators=ne, learning_rate=r
                ),
                "medium",
            )
    for n in (50, 100, 200):
        add(
            f"hist_gb_{n}",
            f"Hist Gradient Boosting ({n})",
            "boosting",
            lambda ne=n: HistGradientBoostingClassifier(max_iter=ne),
            "medium",
        )
    for n in (50, 100):
        add(
            f"ada_{n}",
            f"AdaBoost ({n})",
            "boosting",
            lambda ne=n: AdaBoostClassifier(n_estimators=ne),
            "medium",
        )
    for n in (20, 50):
        add(
            f"bagging_{n}",
            f"Bagging ({n})",
            "ensemble",
            lambda ne=n: BaggingClassifier(n_estimators=ne, n_jobs=-1),
            "medium",
        )

    # --- Naive Bayes ---
    add("gaussian_nb", "Gaussian Naive Bayes",
        "bayes", lambda: GaussianNB(), "fast")
    add("bernoulli_nb", "Bernoulli Naive Bayes",
        "bayes", lambda: BernoulliNB(), "fast")
    add(
        "multinomial_nb",
        "Multinomial Naive Bayes",
        "bayes",
        lambda: MultinomialNB(),
        "fast",
    )
    add(
        "complement_nb",
        "Complement Naive Bayes",
        "bayes",
        lambda: ComplementNB(),
        "fast",
    )

    # --- Neural ---
    for h in ((32,), (64,), (64, 32), (128, 64), (128, 64, 32)):
        hid = "x".join(map(str, h))
        add(
            f"mlp_{hid}",
            f"MLP ({hid})",
            "neural",
            lambda hidden=h: MLPClassifier(
                hidden_layer_sizes=hidden, max_iter=500),
            "medium",
            max_samples=50_000,
        )

    # --- Discriminant ---
    add(
        "lda",
        "Linear Discriminant Analysis",
        "discriminant",
        lambda: LinearDiscriminantAnalysis(),
        "fast",
    )
    add(
        "qda",
        "Quadratic Discriminant Analysis",
        "discriminant",
        lambda: QuadraticDiscriminantAnalysis(),
        "fast",
    )

    # --- Dummy / calibration ---
    add(
        "dummy_stratified",
        "Dummy (stratified)",
        "baseline",
        lambda: DummyClassifier(strategy="stratified"),
        "fast",
    )
    add(
        "dummy_most_frequent",
        "Dummy (most frequent)",
        "baseline",
        lambda: DummyClassifier(strategy="most_frequent"),
        "fast",
    )
    add(
        "calibrated_lr",
        "Calibrated Logistic",
        "calibration",
        lambda: CalibratedClassifierCV(
            LogisticRegression(max_iter=2000), cv=3),
        "medium",
    )

    # --- Voting ---
    add(
        "voting_soft",
        "Voting (LR+RF+GB)",
        "ensemble",
        lambda: VotingClassifier(
            estimators=[
                ("lr", LogisticRegression(max_iter=2000)),
                ("rf", RandomForestClassifier(n_estimators=100, n_jobs=-1)),
                ("gb", GradientBoostingClassifier(n_estimators=80)),
            ],
            voting="soft",
        ),
        "slow",
    )

    # --- XGBoost ---
    xgb = _try_import("xgboost")
    if xgb:
        XGBC = xgb.XGBClassifier
        for n in (50, 100, 200, 300):
            for depth in (3, 5, 7):
                for lr in (0.05, 0.1):
                    add(
                        f"xgb_{n}_d{depth}_lr{lr}",
                        f"XGBoost ({n}, d={depth}, lr={lr})",
                        "xgboost",
                        lambda ne=n, dep=depth, r=lr: XGBC(
                            n_estimators=ne,
                            max_depth=dep,
                            learning_rate=r,
                            eval_metric="logloss",
                            verbosity=0,
                            n_jobs=-1,
                        ),
                        "medium",
                    )

    # --- LightGBM ---
    lgb = _try_import("lightgbm")
    if lgb:
        LGBC = lgb.LGBMClassifier
        for n in (50, 100, 200):
            for depth in (3, 5, 8):
                for lr in (0.05, 0.1):
                    add(
                        f"lgbm_{n}_d{depth}_lr{lr}",
                        f"LightGBM ({n}, d={depth}, lr={lr})",
                        "lightgbm",
                        lambda ne=n, dep=depth, r=lr: LGBC(
                            n_estimators=ne,
                            max_depth=dep,
                            learning_rate=r,
                            verbose=-1,
                            n_jobs=-1,
                        ),
                        "medium",
                    )

    # --- CatBoost ---
    cb = _try_import("catboost")
    if cb:
        CBC = cb.CatBoostClassifier
        for iters in (100, 200, 300):
            for depth in (4, 6, 8):
                add(
                    f"catboost_{iters}_d{depth}",
                    f"CatBoost ({iters}, d={depth})",
                    "catboost",
                    lambda i=iters, d=depth: CBC(
                        iterations=i, depth=d, verbose=0),
                    "medium",
                )

    return specs


def _regression_specs() -> list[ModelSpec]:
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import (
        AdaBoostRegressor,
        BaggingRegressor,
        ExtraTreesRegressor,
        GradientBoostingRegressor,
        HistGradientBoostingRegressor,
        RandomForestRegressor,
        VotingRegressor,
    )
    from sklearn.linear_model import (
        ElasticNet,
        HuberRegressor,
        Lasso,
        LinearRegression,
        PassiveAggressiveRegressor,
        Ridge,
        SGDRegressor,
    )
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.svm import SVR, LinearSVR, NuSVR
    from sklearn.tree import DecisionTreeRegressor, ExtraTreeRegressor

    specs: list[ModelSpec] = []

    def add(
        id_: str,
        name: str,
        family: str,
        factory: Callable[[], BaseEstimator],
        speed: SpeedTier = "medium",
        min_samples: int = 10,
        max_samples: int | None = None,
    ):
        specs.append(
            ModelSpec(
                id=id_,
                name=name,
                family=family,
                problem_type="regression",
                speed=speed,
                factory=factory,
                min_samples=min_samples,
                max_samples=max_samples,
            )
        )

    add(
        "linear_regression",
        "Linear Regression",
        "linear",
        lambda: LinearRegression(n_jobs=-1),
        "fast",
    )
    for alpha in (0.01, 0.1, 1.0, 10.0):
        add(
            f"ridge_a{alpha}",
            f"Ridge (α={alpha})",
            "linear",
            lambda a=alpha: Ridge(alpha=a),
            "fast",
        )
    for alpha in (0.001, 0.01, 0.1, 1.0):
        add(
            f"lasso_a{alpha}",
            f"Lasso (α={alpha})",
            "linear",
            lambda a=alpha: Lasso(alpha=a, max_iter=3000),
            "fast",
        )
    for alpha in (0.01, 0.1, 1.0):
        add(
            f"elastic_a{alpha}",
            f"ElasticNet (α={alpha})",
            "linear",
            lambda a=alpha: ElasticNet(alpha=a, max_iter=3000),
            "fast",
        )
    for alpha in (0.0001, 0.01, 0.1):
        add(
            f"sgd_reg_a{alpha}",
            f"SGD Regressor (α={alpha})",
            "linear",
            lambda a=alpha: SGDRegressor(alpha=a, max_iter=2000),
            "fast",
        )
    add("huber", "Huber Regressor", "linear",
        lambda: HuberRegressor(), "medium")
    add(
        "passive_aggressive_reg",
        "Passive Aggressive Regressor",
        "linear",
        lambda: PassiveAggressiveRegressor(max_iter=1500),
        "fast",
    )

    for c in (0.1, 1.0, 10.0):
        add(
            f"svr_rbf_c{c}",
            f"SVR RBF (C={c})",
            "svm",
            lambda c=c: SVR(kernel="rbf", C=c),
            "slow",
            max_samples=30_000,
        )
    for c in (0.1, 1.0):
        add(
            f"svr_linear_c{c}",
            f"SVR Linear (C={c})",
            "svm",
            lambda c=c: SVR(kernel="linear", C=c),
            "slow",
            max_samples=30_000,
        )
    add("linearsvr", "Linear SVR", "svm",
        lambda: LinearSVR(max_iter=5000), "medium")
    for nu in (0.3, 0.5):
        add(
            f"nusvr_nu{nu}",
            f"Nu-SVR (ν={nu})",
            "svm",
            lambda n=nu: NuSVR(nu=n),
            "slow",
            max_samples=20_000,
        )

    for k in (3, 5, 7, 9, 11, 15):
        add(
            f"knn_reg_k{k}",
            f"KNN Regressor (k={k})",
            "neighbors",
            lambda k=k: KNeighborsRegressor(n_neighbors=k),
            "fast",
            max_samples=20_000,
        )

    for depth in (3, 5, 8, 12, 20, None):
        d = depth if depth else "None"
        add(
            f"dtr_depth{d}",
            f"Decision Tree Reg (depth={d})",
            "tree",
            lambda dep=depth: DecisionTreeRegressor(max_depth=dep),
            "fast",
        )
    add(
        "extra_tree_reg",
        "Extra Tree Regressor",
        "tree",
        lambda: ExtraTreeRegressor(),
        "fast",
    )

    for n in (50, 100, 200, 300):
        for depth in (5, 10, 20):
            add(
                f"rfr_{n}_d{depth}",
                f"Random Forest Reg ({n}, d={depth})",
                "ensemble",
                lambda ne=n, dep=depth: RandomForestRegressor(
                    n_estimators=ne, max_depth=dep, n_jobs=-1
                ),
                "medium",
            )
    for n in (50, 100, 200):
        add(
            f"etr_{n}",
            f"Extra Trees Reg ({n})",
            "ensemble",
            lambda ne=n: ExtraTreesRegressor(n_estimators=ne, n_jobs=-1),
            "medium",
        )
    for n in (50, 100, 150):
        for lr in (0.05, 0.1):
            add(
                f"gbr_{n}_lr{lr}",
                f"Gradient Boosting Reg ({n}, lr={lr})",
                "boosting",
                lambda ne=n, r=lr: GradientBoostingRegressor(
                    n_estimators=ne, learning_rate=r
                ),
                "medium",
            )
    for n in (50, 100, 200):
        add(
            f"hist_gbr_{n}",
            f"Hist GB Reg ({n})",
            "boosting",
            lambda ne=n: HistGradientBoostingRegressor(max_iter=ne),
            "medium",
        )
    for n in (50, 100):
        add(
            f"ada_reg_{n}",
            f"AdaBoost Reg ({n})",
            "boosting",
            lambda ne=n: AdaBoostRegressor(n_estimators=ne),
            "medium",
        )
    for n in (20, 50):
        add(
            f"bagging_reg_{n}",
            f"Bagging Reg ({n})",
            "ensemble",
            lambda ne=n: BaggingRegressor(n_estimators=ne, n_jobs=-1),
            "medium",
        )

    for h in ((32,), (64,), (64, 32), (128, 64)):
        hid = "x".join(map(str, h))
        add(
            f"mlp_reg_{hid}",
            f"MLP Reg ({hid})",
            "neural",
            lambda hidden=h: MLPRegressor(
                hidden_layer_sizes=hidden, max_iter=500),
            "medium",
            max_samples=50_000,
        )

    add(
        "dummy_mean",
        "Dummy (mean)",
        "baseline",
        lambda: DummyRegressor(strategy="mean"),
        "fast",
    )
    add(
        "dummy_median",
        "Dummy (median)",
        "baseline",
        lambda: DummyRegressor(strategy="median"),
        "fast",
    )

    add(
        "voting_reg",
        "Voting Regressor",
        "ensemble",
        lambda: VotingRegressor(
            estimators=[
                ("ridge", Ridge()),
                ("rf", RandomForestRegressor(n_estimators=80, n_jobs=-1)),
                ("gb", GradientBoostingRegressor(n_estimators=80)),
            ]
        ),
        "slow",
    )

    xgb = _try_import("xgboost")
    if xgb:
        XGBR = xgb.XGBRegressor
        for n in (50, 100, 200):
            for depth in (3, 5, 7):
                for lr in (0.05, 0.1):
                    add(
                        f"xgbr_{n}_d{depth}_lr{lr}",
                        f"XGBoost Reg ({n}, d={depth}, lr={lr})",
                        "xgboost",
                        lambda ne=n, dep=depth, r=lr: XGBR(
                            n_estimators=ne,
                            max_depth=dep,
                            learning_rate=r,
                            verbosity=0,
                            n_jobs=-1,
                        ),
                        "medium",
                    )

    lgb = _try_import("lightgbm")
    if lgb:
        LGBR = lgb.LGBMRegressor
        for n in (50, 100, 200):
            for depth in (3, 5, 8):
                add(
                    f"lgbmr_{n}_d{depth}",
                    f"LightGBM Reg ({n}, d={depth})",
                    "lightgbm",
                    lambda ne=n, dep=depth: LGBR(
                        n_estimators=ne, max_depth=dep, verbose=-1, n_jobs=-1
                    ),
                    "medium",
                )

    cb = _try_import("catboost")
    if cb:
        CBR = cb.CatBoostRegressor
        for iters in (100, 200, 300):
            for depth in (4, 6, 8):
                add(
                    f"catboost_reg_{iters}_d{depth}",
                    f"CatBoost Reg ({iters}, d={depth})",
                    "catboost",
                    lambda i=iters, d=depth: CBR(
                        iterations=i, depth=d, verbose=0),
                    "medium",
                )

    return specs


_REGISTRY: list[ModelSpec] | None = None


def get_all_models() -> list[ModelSpec]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _classification_specs() + _regression_specs()
    return _REGISTRY


def get_models_for_problem(problem_type: str) -> list[ModelSpec]:
    if problem_type == "classification":
        return [m for m in get_all_models() if m.problem_type == "classification"]
    if problem_type == "regression":
        return [m for m in get_all_models() if m.problem_type == "regression"]
    return []


def filter_models(
    models: list[ModelSpec],
    n_samples: int,
    skip_slow: bool = False,
) -> list[ModelSpec]:
    out: list[ModelSpec] = []
    for m in models:
        if n_samples < m.min_samples:
            continue
        if m.max_samples is not None and n_samples > m.max_samples:
            continue
        if skip_slow and m.speed == "slow":
            continue
        out.append(m)
    return out


def registry_stats() -> dict[str, Any]:
    all_m = get_all_models()
    clf = [m for m in all_m if m.problem_type == "classification"]
    reg = [m for m in all_m if m.problem_type == "regression"]
    families = sorted({m.family for m in all_m})
    return {
        "total": len(all_m),
        "classification": len(clf),
        "regression": len(reg),
        "families": families,
        "family_count": len(families),
    }
