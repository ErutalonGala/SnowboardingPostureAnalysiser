# SnowCoach · 单板滑雪姿态分析器

一个可本地运行的 Python / Streamlit 原型：从图片、视频或摄像头画面中提取人体骨架，实时叠加关键点，并根据关节角度、肩髋水平度、重心和手部位置给出可解释的滑行姿态建议。

> **安全提示**：本项目提供的是基于二维画面的训练辅助信息，不能替代持证教练、医疗诊断或雪场安全培训。宽松衣物、遮挡、镜头角度和高速运动都会影响结果。

## 功能

- 图片分析：展示带骨架的结果、指标和改进建议；
- 视频分析：逐帧骨架、稳定性分数和实时建议，可下载分析后视频；
- 摄像头模式：低延迟实时反馈（在本机运行时使用）；
- 可选择 regular / goofy 站姿和初级 / 中级 / 刻滑场景；
- 检测置信度不足时不贸然给出结论；
- 所有处理均在运行应用的机器上完成，不主动上传媒体文件。

## 快速开始

推荐 Python 3.10 或 3.11。

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开终端提示的地址（通常为 <http://localhost:8501>）。上传侧面或略偏正面的全身素材，确保头、双手、双脚均在画面内。

### MediaPipe 兼容性

本项目使用 MediaPipe 的 Solutions Pose API，因此依赖文件固定使用兼容的 0.10.21 版本。部分新版安装包只是
不再从顶层导出 `solutions`，应用会自动尝试兼容导入；如果安装包已彻底移除该 API，则需要在已激活的虚拟环境中强制重装项目依赖：

```bash
python -m pip install --upgrade --force-reinstall -r requirements.txt
```

可用 `python -m pip show mediapipe` 确认实际加载的版本；同时请检查启动 Streamlit 与安装依赖时使用的是同一个 Python 环境。
在 Windows 上建议使用同一个解释器完成安装和启动，例如依次执行
`py -3.11 -m pip install --upgrade --force-reinstall -r requirements.txt` 和
`py -3.11 -m streamlit run app.py`，避免 `pip` 与 `streamlit` 指向不同的虚拟环境。

## 测试

```bash
pytest
```

## 项目结构

```text
app.py                    # Streamlit 界面、图片/视频/摄像头工作流
snowcoach/analyzer.py     # 几何指标、评分和建议引擎
snowcoach/pose_engine.py  # MediaPipe 推理与骨架绘制
tests/                    # 不依赖摄像头的单元测试
```

## 当前限制与后续方向

当前版本是单人、单相机、二维估计。它无法可靠判断刃角、雪板受力或真实速度，也不会保存历史训练记录。生产化可进一步加入相机标定、多视角 3D、动作阶段识别、用户基线校准，以及经专业教练标注的数据集。建议拍摄时将相机固定在腰部高度、避免逆光，并保留人与画面边缘的余量。

## 隐私

上传文件会进入 Streamlit 的临时内存；视频分析会使用系统临时目录生成输出，并在会话流程结束时清理中间文件。若部署到服务器，媒体会由该服务器处理，请在部署前补充访问控制、传输加密与数据保留策略。
