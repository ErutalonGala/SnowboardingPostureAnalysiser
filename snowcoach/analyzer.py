"""Explainable geometry-based snowboard posture analysis."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, degrees, hypot
from statistics import fmean
from typing import Mapping


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float
    visibility: float = 1.0


@dataclass(frozen=True)
class AnalysisResult:
    score: int
    confidence: float
    metrics: Mapping[str, float]
    suggestions: tuple[str, ...]
    status: str = "ok"


def angle(a: Landmark, b: Landmark, c: Landmark) -> float:
    """Return the smaller ABC angle in degrees."""
    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)
    denom = hypot(*ba) * hypot(*bc)
    if denom == 0:
        return 0.0
    cosine = max(-1.0, min(1.0, (ba[0] * bc[0] + ba[1] * bc[1]) / denom))
    return degrees(acos(cosine))


class PostureAnalyzer:
    """Convert MediaPipe-style named landmarks into coaching feedback."""

    REQUIRED = (
        "left_shoulder", "right_shoulder", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle",
        "left_wrist", "right_wrist",
    )

    def analyze(self, points: Mapping[str, Landmark], level: str = "基础滑行") -> AnalysisResult:
        if any(name not in points for name in self.REQUIRED):
            return AnalysisResult(0, 0.0, {}, ("请让全身进入画面后重试。",), "insufficient")

        confidence = fmean(points[name].visibility for name in self.REQUIRED)
        if confidence < 0.55:
            return AnalysisResult(0, confidence, {}, ("关键关节被遮挡或画面模糊，请调整机位与光线。",), "low_confidence")

        lk = angle(points["left_hip"], points["left_knee"], points["left_ankle"])
        rk = angle(points["right_hip"], points["right_knee"], points["right_ankle"])
        knee_flex = 180.0 - (lk + rk) / 2
        knee_symmetry = abs(lk - rk)
        shoulder_tilt = abs(points["left_shoulder"].y - points["right_shoulder"].y)
        hip_tilt = abs(points["left_hip"].y - points["right_hip"].y)
        torso_center_x = fmean((points["left_shoulder"].x, points["right_shoulder"].x,
                               points["left_hip"].x, points["right_hip"].x))
        base_center_x = fmean((points["left_ankle"].x, points["right_ankle"].x))
        center_offset = abs(torso_center_x - base_center_x)
        shoulder_width = max(0.05, hypot(
            points["left_shoulder"].x - points["right_shoulder"].x,
            points["left_shoulder"].y - points["right_shoulder"].y,
        ))
        hand_spread = abs(points["left_wrist"].x - points["right_wrist"].x) / shoulder_width
        hip_y = fmean((points["left_hip"].y, points["right_hip"].y))
        low_hands = sum(points[w].y > hip_y + 0.12 for w in ("left_wrist", "right_wrist"))

        metrics = {
            "屈膝幅度": knee_flex,
            "双膝差异": knee_symmetry,
            "肩线倾斜": shoulder_tilt * 100,
            "髋线倾斜": hip_tilt * 100,
            "重心偏移": center_offset * 100,
            "手部展开": hand_spread,
        }
        suggestions: list[str] = []
        target_min, target_max = ((18, 45) if level != "刻滑训练" else (25, 55))
        penalties = 0.0

        if knee_flex < target_min:
            suggestions.append("适度屈膝并保持踝、膝、髋联动，避免直腿吸收震动。")
            penalties += min(22, (target_min - knee_flex) * 1.2)
        elif knee_flex > target_max:
            suggestions.append("屈膝偏深；稍抬高重心，避免长期蹲坐导致动作迟缓。")
            penalties += min(14, (knee_flex - target_max) * 0.7)
        if knee_symmetry > 18:
            suggestions.append("双膝弯曲不一致，尝试让两膝随雪板方向协同移动。")
            penalties += min(16, (knee_symmetry - 18) * 0.6)
        if shoulder_tilt > 0.065 or hip_tilt > 0.065:
            suggestions.append("肩髋线倾斜明显；保持核心稳定，避免只用上身补偿平衡。")
            penalties += min(18, max(shoulder_tilt, hip_tilt) * 120)
        if center_offset > 0.09:
            suggestions.append("上身重心偏离支撑中心；将胸口带回双脚之间，视线看向行进方向。")
            penalties += min(20, (center_offset - 0.09) * 100)
        if low_hands:
            suggestions.append("手位偏低；双手自然放在腰部以上、身体前侧，避免向后甩手。")
            penalties += low_hands * 6
        if hand_spread > 3.2:
            suggestions.append("手臂展开过大；放松肩膀和手肘，减少上身多余摆动。")
            penalties += min(10, (hand_spread - 3.2) * 3)
        elif hand_spread < 0.65:
            suggestions.append("双手过于靠拢；略微打开手臂，为转弯保留平衡空间。")
            penalties += 6
        if not suggestions:
            suggestions.append("姿态整体稳定。继续保持柔和屈膝、核心收紧，并用视线引导滑行。")

        score = round(max(0, min(100, 100 - penalties)) * confidence)
        return AnalysisResult(score, confidence, metrics, tuple(suggestions))
