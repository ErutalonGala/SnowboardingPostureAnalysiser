from snowcoach.analyzer import Landmark, PostureAnalyzer, angle


def point(x, y, visibility=1.0):
    return Landmark(x, y, visibility)


def balanced_pose():
    return {
        "left_shoulder": point(.42, .25), "right_shoulder": point(.58, .25),
        "left_hip": point(.44, .50), "right_hip": point(.56, .50),
        "left_knee": point(.42, .68), "right_knee": point(.58, .68),
        "left_ankle": point(.35, .88), "right_ankle": point(.65, .88),
        "left_wrist": point(.35, .45), "right_wrist": point(.65, .45),
    }


def test_angle_for_right_angle():
    assert angle(point(0, 1), point(0, 0), point(1, 0)) == 90


def test_missing_landmarks_returns_insufficient():
    result = PostureAnalyzer().analyze({})
    assert result.status == "insufficient"
    assert result.score == 0


def test_low_visibility_is_not_scored():
    pose = {name: Landmark(p.x, p.y, .2) for name, p in balanced_pose().items()}
    result = PostureAnalyzer().analyze(pose)
    assert result.status == "low_confidence"


def test_balanced_pose_has_metrics_and_feedback():
    result = PostureAnalyzer().analyze(balanced_pose())
    assert result.status == "ok"
    assert 0 <= result.score <= 100
    assert "屈膝幅度" in result.metrics
    assert result.suggestions


def test_uneven_shoulders_trigger_core_feedback():
    pose = balanced_pose()
    pose["left_shoulder"] = point(.42, .10)
    result = PostureAnalyzer().analyze(pose)
    assert any("肩髋线" in suggestion for suggestion in result.suggestions)
