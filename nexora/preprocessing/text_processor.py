"""Local text embeddings using sentence-transformers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class SentenceTransformerEncoder(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible transformer for local text embeddings.
    
    Uses `sentence-transformers` (all-MiniLM-L6-v2 by default) to convert
    text columns into dense vector representations on CPU.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        
    def fit(self, X: pd.DataFrame | np.ndarray, y=None):
        """Fit does nothing for pre-trained embeddings."""
        return self
        
    def transform(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Embed text columns."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError as e:
                raise ImportError("sentence-transformers is required for text columns. Run `pip install sentence-transformers`") from e

        # If X is a DataFrame, process each column and concatenate
        if isinstance(X, pd.DataFrame):
            embeddings = []
            for col in X.columns:
                texts = X[col].astype(str).tolist()
                emb = self._model.encode(texts, show_progress_bar=False)
                embeddings.append(emb)
            return np.hstack(embeddings)
            
        # If X is numpy array, process flat or column-wise
        if X.ndim == 1:
            texts = [str(x) for x in X]
            return self._model.encode(texts, show_progress_bar=False)
        else:
            embeddings = []
            for i in range(X.shape[1]):
                texts = [str(x) for x in X[:, i]]
                emb = self._model.encode(texts, show_progress_bar=False)
                embeddings.append(emb)
            return np.hstack(embeddings)
            
    def get_feature_names_out(self, input_features=None):
        """Return dummy feature names for embeddings."""
        # MiniLM-L6-v2 produces 384-dimensional embeddings
        # We need to know how many columns were in X to return the exact number.
        # This is a simplification.
        if input_features is None:
            return np.array([f"text_emb_{i}" for i in range(384)])
            
        names = []
        for feat in input_features:
            for i in range(384):
                names.append(f"{feat}_emb_{i}")
        return np.array(names)
