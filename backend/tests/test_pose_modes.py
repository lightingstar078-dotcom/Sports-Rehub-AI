from types import SimpleNamespace
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vision import pose_service


def test_single_image_detection_uses_image_running_mode(monkeypatch):
    calls = []
    fake_mp = SimpleNamespace(
        ImageFormat=SimpleNamespace(SRGB="srgb"),
        Image=lambda **kwargs: kwargs,
    )
    monkeypatch.setitem(sys.modules, "mediapipe", fake_mp)
    monkeypatch.setattr(pose_service, "_make", lambda mode: calls.append(mode) or SimpleNamespace(detect=lambda image: image))

    result = pose_service.detect_image_rgb(np.zeros((2, 2, 3), dtype=np.uint8))

    assert calls == ["IMAGE"]
    assert result["image_format"] == "srgb"


def test_video_detection_uses_video_running_mode(monkeypatch):
    calls = []
    fake_mp = SimpleNamespace(
        ImageFormat=SimpleNamespace(SRGB="srgb"),
        Image=lambda **kwargs: kwargs,
    )
    monkeypatch.setitem(sys.modules, "mediapipe", fake_mp)
    monkeypatch.setattr(pose_service, "_make", lambda mode: calls.append(mode) or SimpleNamespace(detect_for_video=lambda image, timestamp: (image, timestamp)))

    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    result = pose_service.detect_video_frame(frame, 123)

    assert calls == ["VIDEO"]
    assert result[1] == 123
