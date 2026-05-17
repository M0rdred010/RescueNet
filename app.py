from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, time, datetime
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
SATELLITE_SCRIPT = ROOT_DIR / "Satellite" / "main_s1.py"
DRONE_SCRIPT = ROOT_DIR / "Drone" / "main_s2.py"
OUTPUT_ROOT = ROOT_DIR / "output"


st.set_page_config(page_title="RescueNet 可视化运行台", page_icon="🛰️", layout="wide")

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at top left, rgba(82, 133, 255, 0.18), transparent 30%),
          radial-gradient(circle at top right, rgba(35, 177, 123, 0.12), transparent 28%),
          linear-gradient(180deg, #08111f 0%, #0f172a 38%, #111827 100%);
                color: rgba(248, 250, 252, 0.96);
            }
            .stApp p,
            .stApp li,
            .stApp label,
            .stApp span,
            .stApp div[data-testid="stMarkdownContainer"] {
                color: rgba(248, 250, 252, 0.96);
      }
            section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.04);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
      }
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] span,
            section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {
                color: rgba(255, 255, 255, 0.96) !important;
            }
            section[data-testid="stSidebar"] .stCheckbox,
            section[data-testid="stSidebar"] .stCaption,
            section[data-testid="stSidebar"] .stSubheader {
                color: rgba(255, 255, 255, 0.96) !important;
            }
      .hero {
        padding: 1.2rem 1.4rem;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 1rem;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(14px);
      }
      .subtle {
        color: rgba(229, 238, 251, 0.72);
        font-size: 0.95rem;
      }
      .section-card {
        padding: 1rem 1rem 0.6rem 1rem;
        border-radius: 0.9rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
      }
            div[data-testid="stButton"] > button,
            div[data-testid="stFormSubmitButton"] > button,
            div[data-testid="stDownloadButton"] > button {
                background: linear-gradient(180deg, rgba(30, 41, 59, 0.96), rgba(15, 23, 42, 0.96));
                color: rgba(248, 250, 252, 0.98) !important;
                border: 1px solid rgba(148, 163, 184, 0.55);
                border-radius: 0.75rem;
                box-shadow: 0 8px 20px rgba(2, 6, 23, 0.18);
            }
            div[data-testid="stButton"] > button:hover,
            div[data-testid="stFormSubmitButton"] > button:hover,
            div[data-testid="stDownloadButton"] > button:hover {
                background: linear-gradient(180deg, rgba(51, 65, 85, 0.98), rgba(30, 41, 59, 0.98));
                color: #ffffff !important;
                border-color: rgba(191, 219, 254, 0.85);
            }
            div[data-testid="stButton"] > button:focus,
            div[data-testid="stFormSubmitButton"] > button:focus,
            div[data-testid="stDownloadButton"] > button:focus {
                box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.35);
            }
    </style>
    """,
    unsafe_allow_html=True,
)


def _dt_to_iso(day: date, clock: time) -> str:
    return datetime.combine(day, clock).isoformat(sep=" ", timespec="seconds")


def _run_script(script_path: Path, env_overrides: dict[str, str]) -> tuple[int, str, str]:
    env = os.environ.copy()
    env.update(env_overrides)
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout, completed.stderr


def _run_script_stream(
    script_path: Path, env_overrides: dict[str, str], write_out: callable
) -> tuple[int, str, str]:
    """Run script and stream combined stdout/stderr to the provided write_out callback.

    write_out(current_text: str) should render the full accumulated output into the UI.
    Returns (returncode, full_stdout, full_stderr).
    """
    env = os.environ.copy()
    env.update(env_overrides)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"

    # Merge stderr into stdout for simpler streaming
    proc = subprocess.Popen(
        [sys.executable, "-u", str(script_path)],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    out_accum = ""
    try:
        if proc.stdout is not None:
            for line in iter(proc.stdout.readline, ""):
                out_accum += line
                try:
                    write_out(out_accum)
                except Exception:
                    # UI update may occasionally fail during reruns; ignore to keep streaming
                    pass
    finally:
        proc.wait()

    return proc.returncode, out_accum, ""


def _output_summary(folder: Path) -> list[str]:
    if not folder.exists():
        return []
    return [item.name for item in sorted(folder.iterdir()) if item.is_file()]


def _env_from_widgets(prefix: str, values: dict[str, object]) -> dict[str, str]:
    return {f"{prefix}_{key}": str(value) for key, value in values.items()}


st.markdown(
    """
    <div class="hero">
    <h1 style="margin:0 0 0.35rem 0;">RescueNet 轨迹生成可视化界面</h1>
      <div class="subtle">在页面里调整关键参数，点击开始后自动执行卫星与无人机生成流程，日志与结果都显示在网页中。</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("运行开关")
    run_satellite = st.checkbox("卫星", value=True)
    run_drone = st.checkbox("无人机", value=True)
    st.caption(f"输出目录：{OUTPUT_ROOT}")

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

with st.form("run_form", clear_on_submit=False):
    tab_sat, tab_uav = st.tabs(["卫星参数", "无人机参数"])

    with tab_sat:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**T0 将使用当前 UTC 时间（无需输入）**")
            sim_duration_sec = st.number_input("仿真时长（秒）", min_value=60, max_value=86400, value=600, step=60)
            time_step_sec = st.number_input("时间步长（秒）", min_value=1, max_value=60, value=1, step=1)
            min_alt_deg = st.number_input("最小仰角（度）", value=0.0, step=0.5)
        with c2:
            # T0 日期/时间 已由后台自动使用当前 UTC，不再由用户输入
            st.caption("T0: 使用服务器当前 UTC 时间，若需自定义请在环境变量 S1_T0_UTC 中设置")
            obs_lat = st.number_input("救援中心纬度", value=30.0, format="%.6f")
            obs_lon = st.number_input("救援中心经度", value=104.0, format="%.6f")
            max_dist_km = st.number_input("最大距离（km）", min_value=1.0, value=2000.0, step=10.0)
        with c3:
            obs_ele = st.number_input("救援中心海拔（m）", value=459.0, step=1.0)
            max_sat_count = st.number_input("输出卫星数量", min_value=1, max_value=200, value=25, step=1)
            chunk_duration_sec = st.number_input("切片时长（秒）", min_value=1, max_value=3600, value=60, step=1)
            reselect_sat_count = st.number_input("动态保留卫星数", min_value=1, max_value=200, value=25, step=1)
        ip_prefix = st.text_input("卫星 IP 前缀", value="10.0.3.")
        dynamic_filter_interval_sec = st.number_input("动态筛选间隔（秒）", min_value=1, max_value=3600, value=60, step=1)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_uav:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        with d1:
            anchor_lat = st.number_input("锚点纬度", value=30.0, format="%.6f")
            search_radius_m = st.number_input("搜索半径（m）", min_value=100.0, value=2500.0, step=100.0)
            altitude_m = st.number_input("无人机飞行高度（m）", min_value=1.0, value=50.0, step=1.0)
            detection_range_m = st.number_input("检测半径（m）", min_value=1.0, value=60.0, step=1.0)
        with d2:
            anchor_lon = st.number_input("锚点经度", value=104.0, format="%.6f")
            num_uavs = st.number_input("无人机数量", min_value=1, max_value=20, value=3, step=1)
            uav_speed_mps = st.number_input("巡航速度（m/s）", min_value=1.0, value=15.0, step=1.0)
            time_step_ms = st.number_input("采样周期（ms）", min_value=1, max_value=5000, value=100, step=10)
        with d3:
            anchor_alt = st.number_input("锚点海拔（m）", value=459.0, step=1.0)
            victim_count = st.number_input("受害者数量", min_value=1, max_value=1000, value=50, step=1)
            total_duration_ms = st.number_input("仿真时长（ms）", min_value=1000, value=600000, step=1000)
            path_point_spacing_m = st.number_input("路径点间距（m）", min_value=1.0, value=30.0, step=1.0)
        spiral_fov_deg = st.number_input("螺旋视场角（度）", min_value=1.0, max_value=180.0, value=60.0, step=1.0)
        spiral_overlap = st.number_input("航线重叠率", min_value=0.0, max_value=0.95, value=0.3, step=0.05)
        st.markdown("</div>", unsafe_allow_html=True)

    start = st.form_submit_button("开始运行")

if start:
    st.session_state.pop("last_sat_stdout", None)
    st.session_state.pop("last_drone_stdout", None)
    st.session_state.pop("last_sat_stderr", None)
    st.session_state.pop("last_drone_stderr", None)

    sat_stdout = ""
    drone_stdout = ""
    sat_stderr = ""
    drone_stderr = ""

    # Create live log placeholders
    col_left_live, col_right_live = st.columns(2)
    with col_left_live:
        st.markdown("### 卫星日志（运行中实时输出）")
        sat_log_box = st.empty()
        sat_log_box.code(st.session_state.get("last_sat_stdout", "") or "(等待输出)", language="text")
    with col_right_live:
        st.markdown("### 无人机日志（运行中实时输出）")
        drone_log_box = st.empty()
        drone_log_box.code(st.session_state.get("last_drone_stdout", "") or "(等待输出)", language="text")

    if run_satellite:
        st.info("正在执行：卫星 生成...")
        # Use current UTC time as T0 unless overridden by environment variable
        current_t0 = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
        sat_env = _env_from_widgets(
            "S1",
            {
                "T0_UTC": current_t0,
                "SIM_DURATION_SEC": sim_duration_sec,
                "TIME_STEP_SEC": time_step_sec,
                "OBS_LAT": obs_lat,
                "OBS_LON": obs_lon,
                "OBS_ELE": obs_ele,
                "MIN_ALT_DEG": min_alt_deg,
                "MAX_DIST_KM": max_dist_km,
                "MAX_SAT_COUNT": max_sat_count,
                "IP_PREFIX": ip_prefix,
                "CHUNK_DURATION_SEC": chunk_duration_sec,
                "DYNAMIC_FILTER_INTERVAL_SEC": dynamic_filter_interval_sec,
                "RESELECT_SAT_COUNT": reselect_sat_count,
            },
        )
        sat_env["OUTPUT_ROOT"] = str(OUTPUT_ROOT)

        def _write_sat(text: str) -> None:
            try:
                sat_log_box.code(text or "(等待输出)", language="text")
            except Exception:
                pass

        sat_code, sat_stdout, sat_stderr = _run_script_stream(SATELLITE_SCRIPT, sat_env, _write_sat)
        if sat_code != 0:
            st.error("卫星 生成失败")
        else:
            st.success("卫星 生成完成")

    if run_drone:
        st.info("正在执行：无人机 生成...")
        drone_env = _env_from_widgets(
            "S2",
            {
                "ANCHOR_LAT": anchor_lat,
                "ANCHOR_LON": anchor_lon,
                "ANCHOR_ALT": anchor_alt,
                "NUM_UAVS": num_uavs,
                "SEARCH_RADIUS_M": search_radius_m,
                "ALTITUDE_M": altitude_m,
                "DETECTION_RANGE_M": detection_range_m,
                "UAV_SPEED_MPS": uav_speed_mps,
                "TIME_STEP_MS": time_step_ms,
                "TOTAL_DURATION_MS": total_duration_ms,
                "VICTIM_COUNT": victim_count,
                "SPIRAL_FOV_DEG": spiral_fov_deg,
                "SPIRAL_OVERLAP": spiral_overlap,
                "PATH_POINT_SPACING_M": path_point_spacing_m,
            },
        )
        drone_env["OUTPUT_ROOT"] = str(OUTPUT_ROOT)

        def _write_drone(text: str) -> None:
            try:
                drone_log_box.code(text or "(等待输出)", language="text")
            except Exception:
                pass

        drone_code, drone_stdout, drone_stderr = _run_script_stream(DRONE_SCRIPT, drone_env, _write_drone)
        if drone_code != 0:
            st.error("无人机 生成失败")
        else:
            st.success("无人机 生成完成")

    st.session_state["last_sat_stdout"] = sat_stdout
    st.session_state["last_sat_stderr"] = sat_stderr
    st.session_state["last_drone_stdout"] = drone_stdout
    st.session_state["last_drone_stderr"] = drone_stderr

st.markdown("## 运行结果")

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("### 卫星日志")
    if not start:
        st.text_area("卫星日志", value=st.session_state.get("last_sat_stdout", ""), height=320, label_visibility="collapsed", key="sat_stdout_area")
    else:
        st.caption("已在上方显示实时日志")
    sat_errors = st.session_state.get("last_sat_stderr", "")
    if sat_errors:
        st.code(sat_errors, language="text")

with col_right:
    st.markdown("### 无人机日志")
    if not start:
        st.text_area("无人机日志", value=st.session_state.get("last_drone_stdout", ""), height=320, label_visibility="collapsed", key="drone_stdout_area")
    else:
        st.caption("已在上方显示实时日志")
    drone_errors = st.session_state.get("last_drone_stderr", "")
    if drone_errors:
        st.code(drone_errors, language="text")

open_col1, open_col2 = st.columns([1, 4])
with open_col1:
    if st.button("打开 output 目录", use_container_width=True):
        try:
            os.startfile(OUTPUT_ROOT)
            st.success(f"已打开：{OUTPUT_ROOT}")
        except Exception as exc:
            st.error(f"打开目录失败：{exc}")

st.markdown("## 输出文件")
out_col1, out_col2 = st.columns(2)
with out_col1:
    st.markdown("**卫星输出**")
    satellite_files = _output_summary(OUTPUT_ROOT / "satellite")
    if satellite_files:
        st.write(satellite_files)
    else:
        st.caption("尚未生成")
with out_col2:
    st.markdown("**无人机输出**")
    drone_files = _output_summary(OUTPUT_ROOT / "uav")
    if drone_files:
        st.write(drone_files)
    else:
        st.caption("尚未生成")
