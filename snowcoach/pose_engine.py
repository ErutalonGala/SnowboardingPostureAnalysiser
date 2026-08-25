"""MediaPipe adapter kept separate so geometry tests stay lightweight."""

from __future__ import annotations

import cv2
import mediapipe as mp

from .analyzer import Landmark, PostureAnalyzer


class PoseEngine:
    def __init__(self, detection_confidence: float = 0.55, tracking_confidence: float = 0.55):
        solutions = getattr(mp, "solutions", None)
        if solutions is None:
            version = getattr(mp, "__version__", "unknown")
            raise RuntimeError(
                "This application requires MediaPipe's legacy Solutions API, but "
                f"the installed mediapipe {version} package does not provide it. "
                "Reinstall the compatible dependencies with "
                "`python -m pip install --upgrade --force-reinstall -r requirements.txt`."
            )

        self._pose = solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._draw = solutions.drawing_utils
        self._pose_module = solutions.pose
        self.analyzer = PostureAnalyzer()

    def process(self, bgr_frame, level: str = "基础滑行"):
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        output = self._pose.process(rgb)
        annotated = bgr_frame.copy()
        if not output.pose_landmarks:
            return annotated, self.analyzer.analyze({})
        self._draw.draw_landmarks(
            annotated, output.pose_landmarks, self._pose_module.POSE_CONNECTIONS,
            landmark_drawing_spec=self._draw.DrawingSpec(color=(50, 220, 255), thickness=2, circle_radius=3),
            connection_drawing_spec=self._draw.DrawingSpec(color=(74, 222, 128), thickness=2),
        )
        enum = self._pose_module.PoseLandmark
        names = {
            "left_shoulder": enum.LEFT_SHOULDER, "right_shoulder": enum.RIGHT_SHOULDER,
            "left_hip": enum.LEFT_HIP, "right_hip": enum.RIGHT_HIP,
            "left_knee": enum.LEFT_KNEE, "right_knee": enum.RIGHT_KNEE,
            "left_ankle": enum.LEFT_ANKLE, "right_ankle": enum.RIGHT_ANKLE,
            "left_wrist": enum.LEFT_WRIST, "right_wrist": enum.RIGHT_WRIST,
        }
        points = {name: Landmark(output.pose_landmarks.landmark[item].x,
                                 output.pose_landmarks.landmark[item].y,
                                 output.pose_landmarks.landmark[item].visibility)
                  for name, item in names.items()}
        return annotated, self.analyzer.analyze(points, level)

    def close(self):
        self._pose.close()
