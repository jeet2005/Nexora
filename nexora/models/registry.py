"""Compact MVP model registry."""

from __future__ import annotations

from nexora.types import ModelSpec, TaskType


def get_models_for_task(task_type: TaskType) -> list[ModelSpec]:
    """Return trainable model specs for a task.

    Args:
        task_type: `"classification"` or `"regression"`.

    Returns:
        Ordered model registry for the task.

    Example:
        `get_models_for_task("regression")`
    """

    if task_type == "classification":
        return _classification_specs()
    if task_type == "regression":
        return _regression_specs()
    raise ValueError(f"Unsupported task type: {task_type}")


def get_model(task_type: TaskType, name: str) -> ModelSpec | None:
    """Find a model by id, model name, or class name.

    Args:
        task_type: Task registry to search.
        name: Model identifier.

    Returns:
        Matching ModelSpec or None.

    Example:
        `get_model("regression", "RandomForestRegressor")`
    """

    for spec in get_models_for_task(task_type):
        if spec.matches(name):
            return spec
    return None


def load_custom_model(url_or_repo: str) -> ModelSpec:
    """Dynamically load a custom model spec from a remote source or string.

    This allows community-contributed models to be injected into Nexora.

    Args:
        url_or_repo: URL to a Python file containing a `get_spec()` function.

    Returns:
        The dynamically loaded ModelSpec.
    """
    import importlib.util
    import tempfile
    import urllib.request

    if url_or_repo.startswith("http"):
        # Download the spec
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            urllib.request.urlretrieve(url_or_repo, tmp.name)
            module_name = "custom_nexora_model"
            spec = importlib.util.spec_from_file_location(module_name, tmp.name)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            model_spec = module.get_spec()

            # Note: We should ideally inject this into the registry lists,
            # but for MVP we just return it so the user can pass it to `train_models`
            return model_spec
    else:
        raise ValueError(
            "Only HTTP/HTTPS URLs are supported for community models in the MVP."
        )


def _classification_specs() -> list[ModelSpec]:
    return [
        ModelSpec(
            model_id="logistic_regression",
            model_name="LogisticRegression",
            family="linear",
            task_type="classification",
            import_path="sklearn.linear_model",
            class_name="LogisticRegression",
            params={"max_iter": 1000, "solver": "lbfgs"},
            speed="fast",
        ),
        ModelSpec(
            model_id="random_forest_classifier",
            model_name="RandomForestClassifier",
            family="ensemble",
            task_type="classification",
            import_path="sklearn.ensemble",
            class_name="RandomForestClassifier",
            params={"n_estimators": 80, "random_state": 42, "n_jobs": -1},
            speed="medium",
        ),
        ModelSpec(
            model_id="gradient_boosting_classifier",
            model_name="GradientBoostingClassifier",
            family="boosting",
            task_type="classification",
            import_path="sklearn.ensemble",
            class_name="GradientBoostingClassifier",
            params={"random_state": 42},
            speed="medium",
        ),
        ModelSpec(
            model_id="xgboost_classifier",
            model_name="XGBClassifier",
            family="boosting",
            task_type="classification",
            import_path="xgboost",
            class_name="XGBClassifier",
            params={"random_state": 42, "n_jobs": -1, "eval_metric": "logloss"},
            speed="medium",
        ),
        ModelSpec(
            model_id="lightgbm_classifier",
            model_name="LGBMClassifier",
            family="boosting",
            task_type="classification",
            import_path="lightgbm",
            class_name="LGBMClassifier",
            params={"random_state": 42, "n_jobs": -1, "verbose": -1},
            speed="medium",
        ),
        ModelSpec(
            model_id="catboost_classifier",
            model_name="CatBoostClassifier",
            family="boosting",
            task_type="classification",
            import_path="catboost",
            class_name="CatBoostClassifier",
            params={"random_state": 42, "verbose": False, "allow_writing_files": False},
            speed="medium",
        ),
        ModelSpec(
            model_id="decision_tree_classifier",
            model_name="DecisionTreeClassifier",
            family="tree",
            task_type="classification",
            import_path="sklearn.tree",
            class_name="DecisionTreeClassifier",
            params={"random_state": 42, "max_depth": 8},
            speed="fast",
        ),
        ModelSpec(
            model_id="knn_classifier",
            model_name="KNeighborsClassifier",
            family="neighbors",
            task_type="classification",
            import_path="sklearn.neighbors",
            class_name="KNeighborsClassifier",
            params={"n_neighbors": 5},
            speed="fast",
        ),
        ModelSpec(
            model_id="gaussian_nb",
            model_name="GaussianNB",
            family="bayes",
            task_type="classification",
            import_path="sklearn.naive_bayes",
            class_name="GaussianNB",
            params={},
            speed="fast",
        ),
    ]


def _regression_specs() -> list[ModelSpec]:
    return [
        ModelSpec(
            model_id="linear_regression",
            model_name="LinearRegression",
            family="linear",
            task_type="regression",
            import_path="sklearn.linear_model",
            class_name="LinearRegression",
            params={},
            speed="fast",
        ),
        ModelSpec(
            model_id="ridge",
            model_name="Ridge",
            family="linear",
            task_type="regression",
            import_path="sklearn.linear_model",
            class_name="Ridge",
            params={"alpha": 1.0},
            speed="fast",
        ),
        ModelSpec(
            model_id="random_forest_regressor",
            model_name="RandomForestRegressor",
            family="ensemble",
            task_type="regression",
            import_path="sklearn.ensemble",
            class_name="RandomForestRegressor",
            params={"n_estimators": 80, "random_state": 42, "n_jobs": -1},
            speed="medium",
        ),
        ModelSpec(
            model_id="gradient_boosting_regressor",
            model_name="GradientBoostingRegressor",
            family="boosting",
            task_type="regression",
            import_path="sklearn.ensemble",
            class_name="GradientBoostingRegressor",
            params={"random_state": 42},
            speed="medium",
        ),
        ModelSpec(
            model_id="xgboost_regressor",
            model_name="XGBRegressor",
            family="boosting",
            task_type="regression",
            import_path="xgboost",
            class_name="XGBRegressor",
            params={"random_state": 42, "n_jobs": -1},
            speed="medium",
        ),
        ModelSpec(
            model_id="lightgbm_regressor",
            model_name="LGBMRegressor",
            family="boosting",
            task_type="regression",
            import_path="lightgbm",
            class_name="LGBMRegressor",
            params={"random_state": 42, "n_jobs": -1, "verbose": -1},
            speed="medium",
        ),
        ModelSpec(
            model_id="catboost_regressor",
            model_name="CatBoostRegressor",
            family="boosting",
            task_type="regression",
            import_path="catboost",
            class_name="CatBoostRegressor",
            params={"random_state": 42, "verbose": False, "allow_writing_files": False},
            speed="medium",
        ),
        ModelSpec(
            model_id="decision_tree_regressor",
            model_name="DecisionTreeRegressor",
            family="tree",
            task_type="regression",
            import_path="sklearn.tree",
            class_name="DecisionTreeRegressor",
            params={"random_state": 42, "max_depth": 8},
            speed="fast",
        ),
        ModelSpec(
            model_id="knn_regressor",
            model_name="KNeighborsRegressor",
            family="neighbors",
            task_type="regression",
            import_path="sklearn.neighbors",
            class_name="KNeighborsRegressor",
            params={"n_neighbors": 5},
            speed="fast",
        ),
    ]
