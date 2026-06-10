"""Data versioning via DVC."""

import os
import subprocess
import pandas as pd


def init_dvc(repo_path: str = "."):
    """Initialize DVC in the repository if not already initialized."""
    dvc_dir = os.path.join(repo_path, ".dvc")
    if not os.path.exists(dvc_dir):
        try:
            subprocess.run(["dvc", "init"], cwd=repo_path, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to initialize DVC: {e.stderr.decode()}")


def snapshot_data(df: pd.DataFrame, dataset_name: str, version_tag: str, repo_path: str = ".") -> str:
    """Save a DataFrame to disk and track it with DVC.
    
    Args:
        df: DataFrame to save.
        dataset_name: Name of the dataset file (e.g. 'training_data.csv').
        version_tag: Git tag to create for this version.
        repo_path: Path to the repository.
        
    Returns:
        Path to the tracked file.
    """
    init_dvc(repo_path)
    
    data_dir = os.path.join(repo_path, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, dataset_name)
    df.to_csv(file_path, index=False)
    
    try:
        # Add to DVC
        subprocess.run(["dvc", "add", file_path], cwd=repo_path, check=True, capture_output=True)
        
        # Git commit the .dvc file
        dvc_file = f"{file_path}.dvc"
        subprocess.run(["git", "add", dvc_file, os.path.join(repo_path, ".dvc/config")], cwd=repo_path, check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Track data {dataset_name} version {version_tag}"], cwd=repo_path, check=False, capture_output=True)
        
        # Tag it
        subprocess.run(["git", "tag", "-a", version_tag, "-m", f"Data version {version_tag}"], cwd=repo_path, check=False, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to track data with DVC: {e.stderr.decode() if e.stderr else str(e)}")
        
    return file_path
