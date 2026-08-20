from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from snowcoach.pose_engine import PoseEngine


st.set_page_config(page_title="SnowCoach", page_icon="🏂", layout="wide")
st.markdown("""
<style>
.stApp { background: #07111f; color: #eef7ff; }
[data-testid="stMetric"] { background: #101f32; border: 1px solid #203b56; padding: 14px; border-radius: 14px; }
.hero { padding: 1rem 0 1.5rem; }
.eyebrow { color:#58e0c1; font-weight:700; letter-spacing:.12em; font-size:.78rem; }
.hero h1 { font-size:3rem; margin:.25rem 0; }
.hero p { color:#a8bdd0; max-width:760px; }
.tip { background:#102337; border-left:4px solid #58e0c1; padding:.8rem 1rem; border-radius:8px; margin:.5rem 0; }
</style>
<div class="hero"><div class="eyebrow">AI SNOWBOARD COACH</div>
<h1>让每一次滑行，都有数据反馈。</h1>
<p>上传画面或连接摄像头，实时查看人体骨架、稳定性评分与可执行的姿态建议。</p></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("分析设置")
    source = st.radio("画面来源", ("图片", "视频", "摄像头"))
    stance = st.selectbox("站姿", ("Regular · 左脚前", "Goofy · 右脚前"))
    level = st.selectbox("训练场景", ("基础滑行", "中级转弯", "刻滑训练"))
    st.caption(f"当前：{stance} / {level}")
    st.divider()
    st.info("建议使用固定机位，完整拍到头部、双手和雪板。系统仅分析单人。")


def show_result(result):
    if result.status != "ok":
        st.warning(result.suggestions[0])
        return
    cols = st.columns(4)
    cols[0].metric("稳定性评分", f"{result.score} / 100")
    cols[1].metric("识别置信度", f"{result.confidence:.0%}")
    cols[2].metric("屈膝幅度", f"{result.metrics['屈膝幅度']:.1f}°")
    cols[3].metric("重心偏移", f"{result.metrics['重心偏移']:.1f}%")
    st.subheader("教练建议")
    for suggestion in result.suggestions:
        st.markdown(f'<div class="tip">{suggestion}</div>', unsafe_allow_html=True)
    with st.expander("查看完整指标"):
        st.json({key: round(value, 2) for key, value in result.metrics.items()})


if source == "图片":
    upload = st.file_uploader("拖入滑行图片", type=("jpg", "jpeg", "png", "webp"))
    if upload:
        frame = cv2.cvtColor(np.array(Image.open(upload).convert("RGB")), cv2.COLOR_RGB2BGR)
        engine = PoseEngine()
        annotated, result = engine.process(frame, level)
        engine.close()
        left, right = st.columns([1.55, 1])
        with left:
            st.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), caption="骨架识别结果", use_container_width=True)
        with right:
            show_result(result)
    else:
        st.info("上传一张全身滑雪照片开始分析。支持 JPG、PNG、WEBP。")

elif source == "视频":
    upload = st.file_uploader("上传滑行视频", type=("mp4", "mov", "avi", "m4v"))
    if upload and st.button("开始分析", type="primary"):
        progress, preview, status = st.progress(0), st.empty(), st.empty()
        input_path = output_path = None
        try:
            suffix = Path(upload.name).suffix or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as source_file:
                source_file.write(upload.getbuffer())
                input_path = source_file.name
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            output_path = output_file.name
            output_file.close()
            capture = cv2.VideoCapture(input_path)
            fps = capture.get(cv2.CAP_PROP_FPS) or 25
            width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total = max(1, int(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
            writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            engine, index, last_result = PoseEngine(), 0, None
            while capture.isOpened():
                ok, frame = capture.read()
                if not ok:
                    break
                annotated, last_result = engine.process(frame, level)
                writer.write(annotated)
                if index % max(1, int(fps // 3)) == 0:
                    preview.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), use_container_width=True)
                index += 1
                progress.progress(min(index / total, 1.0))
                status.caption(f"已分析 {index} / {total} 帧")
            capture.release(); writer.release(); engine.close()
            if last_result:
                show_result(last_result)
            with open(output_path, "rb") as video_file:
                st.download_button("下载带骨架视频", video_file.read(), "snowcoach-analysis.mp4", "video/mp4")
        finally:
            for path in (input_path, output_path):
                if path:
                    Path(path).unlink(missing_ok=True)
    elif not upload:
        st.info("上传 MP4、MOV 或 AVI 视频；短视频可更快获得反馈。")

else:
    st.warning("摄像头模式会读取运行本应用的计算机摄像头；部署在远程服务器时请改用图片或视频。")
    running = st.toggle("启动实时分析")
    frame_slot = st.empty()
    advice_slot = st.empty()
    if running:
        camera, engine = cv2.VideoCapture(0), PoseEngine()
        if not camera.isOpened():
            st.error("无法打开摄像头，请检查设备权限。")
        else:
            while running:
                ok, frame = camera.read()
                if not ok:
                    break
                annotated, result = engine.process(frame, level)
                frame_slot.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                advice_slot.info(f"评分 {result.score} · {result.suggestions[0]}")
        camera.release(); engine.close()

st.divider()
st.caption("SnowCoach v0.1 · 二维姿态估计仅供训练参考，请始终遵守雪场规则并佩戴护具。")
