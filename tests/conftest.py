"""
Configuration pytest pour les tests.
"""
import pytest
import os
import sys

# Ajouter src/ au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture pour créer un répertoire temporaire pour les tests."""
    return tmp_path

@pytest.fixture
def sample_config():
    """Fixture pour fournir une configuration de test."""
    return {
        'root_paths': ['/tmp/test'],
        'performance': {
            'num_workers': 4,
            'batch_size': 1000,
            'queue_size': 10000
        }
    }
