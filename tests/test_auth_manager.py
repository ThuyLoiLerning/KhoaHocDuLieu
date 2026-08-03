import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.data.auth_manager import AuthManager

def test_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(AuthManager, 'auth_dir', str(tmp_path))
    am = AuthManager()
    state = {"cookies": [{"name": "x", "value": "1"}], "origins": []}
    am.save_storage_state("test_site", state)
    assert am.has_session("test_site")
    loaded = am.get_storage_state("test_site")
    assert loaded["cookies"][0]["value"] == "1"

def test_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(AuthManager, 'auth_dir', str(tmp_path))
    am = AuthManager()
    am.save_storage_state("test_site", {"cookies": [], "origins": []})
    am.delete_session("test_site")
    assert not am.has_session("test_site")
