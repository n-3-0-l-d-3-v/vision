import pytest

from vision import launcher


def test_type_maps_to_first_installed_app(monkeypatch):
    monkeypatch.setattr(launcher, "find_app", lambda k: "C:/x/audacity.exe" if k == "audacity" else None)
    assert launcher.resolve("music") == ("audacity", "C:/x/audacity.exe")


def test_no_installed_app_returns_none(monkeypatch):
    monkeypatch.setattr(launcher, "find_app", lambda k: None)
    assert launcher.resolve("video") == (None, None)


def test_unknown_app_rejected():
    with pytest.raises(ValueError):
        launcher.resolve("music", "photoshop")


def test_every_type_app_key_is_known():
    for apps in launcher.TYPE_APPS.values():
        assert all(a in launcher.APPS for a in apps)


def test_open_falls_back_to_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "find_app", lambda k: None)
    opened = []
    monkeypatch.setattr(launcher.os, "startfile", lambda p: opened.append(p), raising=False)
    monkeypatch.setattr(launcher.os, "name", "nt")
    assert "opened the folder" in launcher.open_project(tmp_path, "music")
    assert opened == [str(tmp_path)]
