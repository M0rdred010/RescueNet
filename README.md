# RescueNet 轨迹生成系统

RescueNet 是一个面向应急搜救场景的数据生成项目，包含两部分：

- 卫星轨迹生成（S1）：基于 Starlink TLE 计算卫星 ECEF 轨迹并按时间切片导出。
- 无人机轨迹生成（S2）：基于螺旋搜索路径生成多无人机搜救轨迹并导出。

项目提供 Streamlit 可视化界面，可统一配置参数、启动任务、查看实时日志与输出文件。

## 功能概览

- 一键启动 Web UI（自动安装依赖）
- 卫星/无人机任务可独立或同时运行
- 支持通过环境变量覆盖关键参数
- 输出统一落盘到 `output/` 目录
- 运行日志在页面实时显示

## 项目结构

```text
Soft/
├─ app.py                    # Streamlit 可视化入口
├─ start_ui.bat              # Windows 一键启动脚本
├─ requirements.txt          # Python 依赖
├─ Satellite/
│  ├─ main_s1.py             # S1 卫星轨迹生成主脚本
│  ├─ de421.bsp              # 天体历表文件
│  └─ starlink.tle           # 本地 TLE 缓存文件
├─ Drone/
│  ├─ main_s2.py             # S2 无人机轨迹生成主脚本
│  └─ SAREnv/                # 路径规划相关模块
└─ output/
   ├─ satellite/             # 卫星切片 CSV
   ├─ uav/                   # 无人机切片 CSV
   └─ manifest.json          # 场景索引文件（由 S1 生成）
```

## 环境要求

- Windows（已提供 `start_ui.bat`）
- Python 3.10+（建议使用项目 `.venv`）
- 网络可访问 CelesTrak（用于实时下载 Starlink TLE，可关闭）

## 快速开始（推荐）

在项目根目录双击或命令行执行：

```bat
start_ui.bat
```

脚本行为：

1. 使用 `.venv\Scripts\python.exe`
2. 自动安装或更新 `requirements.txt` 依赖
3. 启动 Streamlit 页面

默认地址：`http://localhost:8501`

## 手动运行

### 1) 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) 启动 Web UI

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### 3) 单独运行 S1 / S2（可选）

```powershell
.\.venv\Scripts\python.exe .\Satellite\main_s1.py
.\.venv\Scripts\python.exe .\Drone\main_s2.py
```

## 参数配置方式

参数支持两种方式：

- 在 Web UI 中填写（推荐）
- 通过环境变量覆盖默认值

### S1 常用环境变量（卫星）

- `S1_T0_UTC`：仿真起始 UTC 时间（ISO 字符串）
- `S1_SIM_DURATION_SEC`：仿真总时长（秒）
- `S1_TIME_STEP_SEC`：时间步长（秒）
- `S1_OBS_LAT` / `S1_OBS_LON` / `S1_OBS_ELE`：观测点坐标
- `S1_MIN_ALT_DEG`：最小仰角（度）
- `S1_MAX_DIST_KM`：最大距离（km）
- `S1_MAX_SAT_COUNT`：输出卫星数上限
- `S1_IP_PREFIX`：卫星 IP 前缀
- `S1_CHUNK_DURATION_SEC`：切片时长（秒）
- `S1_DYNAMIC_FILTER_INTERVAL_SEC`：动态筛选间隔（秒）
- `S1_RESELECT_SAT_COUNT`：每次筛选保留卫星数
- `S1_REFRESH_TLE`：是否实时刷新 TLE（`1` 是 / `0` 否）

### S2 常用环境变量（无人机）

- `S2_ANCHOR_LAT` / `S2_ANCHOR_LON` / `S2_ANCHOR_ALT`：锚点坐标
- `S2_NUM_UAVS`：无人机数量
- `S2_SEARCH_RADIUS_M`：搜索半径（m）
- `S2_ALTITUDE_M`：飞行高度（m）
- `S2_DETECTION_RANGE_M`：检测半径（m）
- `S2_UAV_SPEED_MPS`：巡航速度（m/s）
- `S2_TIME_STEP_MS`：采样周期（ms）
- `S2_TOTAL_DURATION_MS`：仿真时长（ms）
- `S2_VICTIM_COUNT`：受害者数量
- `S2_SPIRAL_FOV_DEG`：螺旋视场角（度）
- `S2_SPIRAL_OVERLAP`：航线重叠率
- `S2_PATH_POINT_SPACING_M`：路径点间距（m）

此外可通过 `OUTPUT_ROOT` 指定输出根目录。

## 输出文件说明

### 卫星输出（`output/satellite/`）

- 文件名格式：`sat_trace_{startMs}_{endMs}.csv`
- 字段示例：
  - `time_ms`, `node_id`, `name`, `type`
  - `ecef_x`, `ecef_y`, `ecef_z`
  - `altitude_km`, `orbit_id`, `ip`
  - `norad_id`, `distance_km`（动态筛选信息）

### 无人机输出（`output/uav/`）

- 文件名格式：`uav_trace_{startMs}_{endMs}.csv`
- 字段示例：
  - `time_ms`, `node_id`, `role`, `type`
  - `ecef_x`, `ecef_y`, `ecef_z`
  - `ip`, `heading_deg`, `battery_pct`

### 清单文件

- `output/manifest.json`：由 S1 生成的场景索引信息。

## 常见问题

### 1) 启动时报 `No module named streamlit`

通常是没有使用项目 `.venv`。
请优先使用：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### 2) 看不到实时日志

已使用无缓冲模式运行子进程；若仍异常，确认：

- 通过 `start_ui.bat` 或 `.venv` Python 启动
- 浏览器无缓存旧页面（可刷新重开）

### 3) TLE 下载失败

- 程序会尝试使用本地 `Satellite/starlink.tle`
- 可设置 `S1_REFRESH_TLE=0` 禁用在线刷新

## 开发建议

- 提交前可先做语法检查：

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py
.\.venv\Scripts\python.exe -m py_compile .\Satellite\main_s1.py
.\.venv\Scripts\python.exe -m py_compile .\Drone\main_s2.py
```

- 建议配合 `.gitignore` 忽略 `.venv/`、`output/`、`__pycache__/`。

## 许可证

当前仓库未声明许可证；如需开源发布，建议补充 `LICENSE` 文件。
