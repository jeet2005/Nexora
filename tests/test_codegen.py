from __future__ import annotations

from nexora import Nexora


def test_report_code_executes_without_nexora_import(regression_csv, monkeypatch):
    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code

    assert "import nexora" not in code
    monkeypatch.chdir(path.parent)
    exec(code, {})


def test_code_for_executes_for_named_model(regression_csv, monkeypatch):
    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_for("Ridge")

    assert "import nexora" not in code
    assert "Ridge" in code
    monkeypatch.chdir(path.parent)
    exec(code, {})


def test_save_code_writes_executable_python(regression_csv, tmp_path, monkeypatch):
    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    saved = report.save_code(tmp_path / "model.py", model="Ridge")
    code = saved.read_text(encoding="utf-8")

    assert saved.exists()
    assert "import nexora" not in code
    monkeypatch.chdir(path.parent)
    exec(code, {})


def test_code_fastapi_generates_valid_code(regression_csv):
    """Test that FastAPI code generator produces syntactically valid Python."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_fastapi()

    assert "import fastapi" in code.lower() or "from fastapi" in code
    assert "import nexora" not in code
    assert "def predict" in code
    assert "def health_check" in code
    assert "BaseModel" in code  # Pydantic models
    assert report.best_model in code  # Model name in code

    # Verify it's syntactically valid Python
    compile(code, "<fastapi_generated>", "exec")


def test_code_fastapi_has_required_endpoints(regression_csv):
    """Test that FastAPI app has all required endpoints."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_fastapi()

    assert '@app.get("/health"' in code or '@app.get("/health")' in code
    assert '@app.post("/predict"' in code or '@app.post("/predict")' in code
    assert "PredictionRequest" in code
    assert "PredictionResponse" in code


def test_code_fastapi_for_specific_model(regression_csv):
    """Test FastAPI code generation for a specific non-best model."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=4)

    # Get second-best model
    completed = [r for r in report.results if r.status == "completed"]
    if len(completed) > 1:
        model_name = completed[1].model_name
        code = report.code_fastapi(model_name=model_name)

        assert model_name in code
        assert "import nexora" not in code
        compile(code, "<fastapi_generated>", "exec")


def test_save_fastapi_writes_to_file(regression_csv, tmp_path):
    """Test that save_fastapi writes valid FastAPI code to file."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    app_path = tmp_path / "app.py"
    saved = report.save_fastapi(app_path)

    assert saved.exists()
    code = saved.read_text(encoding="utf-8")

    assert "@app.post" in code
    assert "@app.get" in code
    compile(code, str(app_path), "exec")


def test_code_streamlit_generates_valid_code(regression_csv):
    """Test that Streamlit code generator produces syntactically valid Python."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_streamlit()

    assert "import streamlit" in code or "st." in code
    assert "import nexora" not in code
    assert "def predict" not in code  # Streamlit doesn't need explicit functions
    assert report.best_model in code  # Model name in code

    # Verify it's syntactically valid Python
    compile(code, "<streamlit_generated>", "exec")


def test_code_streamlit_has_required_components(regression_csv):
    """Test that Streamlit app has UI components."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_streamlit()

    # Check for Streamlit components
    assert "st.title" in code or "st.set_page_config" in code
    assert "st.button" in code or "st.form" in code  # Interactive elements
    assert "st.dataframe" in code  # Data display
    assert "file_uploader" in code or "st.number_input" in code  # Inputs


def test_code_streamlit_for_specific_model(regression_csv):
    """Test Streamlit code generation for a specific non-best model."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=4)

    # Get second-best model
    completed = [r for r in report.results if r.status == "completed"]
    if len(completed) > 1:
        model_name = completed[1].model_name
        code = report.code_streamlit(model_name=model_name)

        assert model_name in code
        assert "import nexora" not in code
        compile(code, "<streamlit_generated>", "exec")


def test_save_streamlit_writes_to_file(regression_csv, tmp_path):
    """Test that save_streamlit writes valid code to file."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    app_path = tmp_path / "dashboard.py"
    saved = report.save_streamlit(app_path)

    assert saved.exists()
    code = saved.read_text(encoding="utf-8")

    assert "streamlit" in code.lower()
    compile(code, str(app_path), "exec")


# ─ Flask Generator Tests ─────────────────────────────────


def test_code_flask_generates_valid_code(regression_csv):
    """Test that Flask code generator produces valid Python."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_flask()

    assert "Flask" in code or "flask" in code
    assert "import nexora" not in code
    assert "@app.route" in code or "@app.get" in code
    compile(code, "<flask_generated>", "exec")


def test_code_flask_has_required_endpoints(regression_csv):
    """Test that Flask app has required endpoints."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_flask()

    assert "@app.route" in code
    assert "/predict" in code
    assert "/health" in code


def test_save_flask_writes_to_file(regression_csv, tmp_path):
    """Test that save_flask writes to file."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    app_path = tmp_path / "app.py"
    saved = report.save_flask(app_path)

    assert saved.exists()
    code = saved.read_text(encoding="utf-8")
    compile(code, str(app_path), "exec")


# ─ Docker Generator Tests ────────────────────────────────


def test_code_docker_returns_dockerfile_and_requirements(regression_csv):
    """Test that Docker generator returns both files."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    dockerfile, requirements = report.code_docker()

    assert "FROM python" in dockerfile
    assert "WORKDIR" in dockerfile
    assert "pandas" in requirements
    assert "scikit-learn" in requirements


def test_save_docker_writes_both_files(regression_csv, tmp_path):
    """Test that save_docker creates both files."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    docker_path = tmp_path / "Dockerfile"
    req_path = tmp_path / "requirements.txt"

    saved_docker, saved_req = report.save_docker(docker_path, req_path)

    assert saved_docker.exists()
    assert saved_req.exists()
    assert "FROM" in saved_docker.read_text()
    assert "pandas" in saved_req.read_text()


# ─ Jupyter Notebook Generator Tests ──────────────────────


def test_code_notebook_generates_valid_json(regression_csv):
    """Test that Jupyter notebook generator produces valid JSON."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    nb_json = report.code_notebook()

    import json

    nb = json.loads(nb_json)
    assert "cells" in nb
    assert "metadata" in nb
    assert len(nb["cells"]) > 0


def test_save_notebook_writes_to_file(regression_csv, tmp_path):
    """Test that save_notebook writes valid .ipynb file."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    nb_path = tmp_path / "notebook.ipynb"
    saved = report.save_notebook(nb_path)

    assert saved.exists()

    import json

    nb = json.loads(saved.read_text(encoding="utf-8"))
    assert nb["nbformat"] == 4


# ─ MLflow Generator Tests ────────────────────────────────


def test_code_mlflow_generates_valid_code(regression_csv):
    """Test that MLflow code generator produces valid Python."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_mlflow()

    assert "mlflow" in code.lower()
    assert "import nexora" not in code
    assert "mlflow.log" in code
    compile(code, "<mlflow_generated>", "exec")


def test_save_mlflow_writes_to_file(regression_csv, tmp_path):
    """Test that save_mlflow writes to file."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    train_path = tmp_path / "train.py"
    saved = report.save_mlflow(train_path)

    assert saved.exists()
    code = saved.read_text(encoding="utf-8")
    compile(code, str(train_path), "exec")


# ─ Pipeline Generator Tests ─────────────────────────────


def test_code_pipeline_generates_valid_code(regression_csv):
    """Test that Pipeline code generator produces valid Python."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_pipeline()

    assert "Pipeline" in code or "pipeline" in code
    assert "import nexora" not in code
    assert "create_pipeline" in code
    compile(code, "<pipeline_generated>", "exec")


def test_code_pipeline_has_preprocessor(regression_csv):
    """Test that Pipeline code includes preprocessing."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    code = report.code_pipeline()

    assert "ColumnTransformer" in code
    assert "StandardScaler" in code or "Imputer" in code


def test_save_pipeline_writes_to_file(regression_csv, tmp_path):
    """Test that save_pipeline writes to file."""

    path, _ = regression_csv
    report = Nexora(path, target="revenue").run(max_models=3)

    pipeline_path = tmp_path / "pipeline.py"
    saved = report.save_pipeline(pipeline_path)

    assert saved.exists()
    code = saved.read_text(encoding="utf-8")
    compile(code, str(pipeline_path), "exec")
