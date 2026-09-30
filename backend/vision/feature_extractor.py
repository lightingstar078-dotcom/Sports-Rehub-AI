import math
import numpy as np
from .pose_service import detect_video_frame

L_HIP, R_HIP, L_KNEE, R_KNEE, L_ANKLE, R_ANKLE = 23,24,25,26,27,28
L_SHOULDER, R_SHOULDER = 11,12

def angle(a, b, c):
    a, b, c = np.array(a, dtype=float), np.array(b, dtype=float), np.array(c, dtype=float)
    ba, bc = a - b, c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0: return 0.0
    x = np.clip(np.dot(ba, bc) / denom, -1, 1)
    return float(np.degrees(np.arccos(x)))

def _pt(lm): return (lm.x, lm.y, lm.z)

def extract_features(path: str, exercise: str):
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError("Video could not be opened")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, frames // 80) if frames else 1
    knees_l, knees_r, hip_l, hip_r, symmetry_vals, sway = [], [], [], [], [], []
    valid = 0
    idx = 0
    prev = None
    while True:
        ok, frame = cap.read()
        if not ok: break
        if idx % step != 0:
            idx += 1; continue
        ts = int(idx / fps * 1000)
        try:
            result = detect_video_frame(frame, ts)
        except FileNotFoundError as exc:
            cap.release(); raise exc
        if not result.pose_landmarks:
            idx += 1; continue
        lm = result.pose_landmarks[0]
        required = [L_HIP,R_HIP,L_KNEE,R_KNEE,L_ANKLE,R_ANKLE,L_SHOULDER,R_SHOULDER]
        if any(i >= len(lm) for i in required):
            idx += 1; continue
        pts = [_pt(x) for x in lm]
        kl, kr = angle(pts[L_HIP], pts[L_KNEE], pts[L_ANKLE]), angle(pts[R_HIP], pts[R_KNEE], pts[R_ANKLE])
        hl, hr = angle(pts[L_SHOULDER], pts[L_HIP], pts[L_KNEE]), angle(pts[R_SHOULDER], pts[R_HIP], pts[R_KNEE])
        knees_l.append(kl); knees_r.append(kr); hip_l.append(hl); hip_r.append(hr)
        leg_left = np.linalg.norm(np.array(pts[L_HIP]) - np.array(pts[L_ANKLE]))
        leg_right = np.linalg.norm(np.array(pts[R_HIP]) - np.array(pts[R_ANKLE]))
        symmetry_vals.append(100 - min(100, abs(leg_left-leg_right) / max(leg_left,leg_right,1e-6) * 100))
        center = (np.array(pts[L_HIP]) + np.array(pts[R_HIP])) / 2
        if prev is not None:
            sway.append(float(np.linalg.norm(center - prev)))
        prev = center
        valid += 1
        idx += 1
    cap.release()
    if valid < 5:
        raise ValueError("Not enough valid human-pose frames for analysis")
    knee_rom = float(max(knees_l+knees_r) - min(knees_l+knees_r))
    hip_rom = float(max(hip_l+hip_r) - min(hip_l+hip_r))
    symmetry = float(np.mean(symmetry_vals))
    stability = max(0, 100 - min(100, (np.mean(sway) if sway else 0.01) * 800))
    consistency = max(0, 100 - min(100, float(np.std(knees_l + knees_r)) * 1.5))
    rom_score = max(0, min(100, knee_rom / 1.6))
    movement_quality = float(np.mean([symmetry, rom_score, consistency]))
    landing = float((stability + consistency) / 2) if exercise == "single_leg_hop" else float(stability)
    return {
        "movement_quality": round(max(0,min(100,movement_quality)), 2),
        "symmetry": round(max(0,min(100,symmetry)), 2),
        "rom": round(max(0,min(100,rom_score)), 2),
        "stability": round(max(0,min(100,stability)), 2),
        "landing_control": round(max(0,min(100,landing)), 2),
        "movement_consistency": round(max(0,min(100,consistency)), 2),
        "knee_angle_mean": round(float(np.mean(knees_l+knees_r)), 2),
        "knee_angle_min": round(float(min(knees_l+knees_r)), 2),
        "knee_angle_max": round(float(max(knees_l+knees_r)), 2),
        "hip_angle_mean": round(float(np.mean(hip_l+hip_r)), 2),
        "frames_analyzed": valid,
    }
