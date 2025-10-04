"""
Test dummy pour vérifier que pytest fonctionne.
"""
import pytest

def test_dummy():
    """Test basique."""
    assert 1 + 1 == 2

def test_imports():
    """Test que les imports fonctionnent."""
    import pandas
    import streamlit
    import plotly
    assert True

@pytest.mark.unit
def test_with_marker():
    """Test avec marker."""
    assert True
