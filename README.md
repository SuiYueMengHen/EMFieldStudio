# EM Field Studio — 衍射仿真软件

基于标量衍射理论的专业光学衍射仿真平台，支持多种传播模型、孔径类型和高精度渲染，提供交互式可视化与定量分析功能。

## 功能特点

### 传播模型

基于严格的标量衍射理论，实现四种经典传播模型：

| 模型 | 方法 | 适用场景 |
|------|------|---------|
| **夫琅和费 (Fraunhofer)** | 远场 FFT | 远场衍射，$N_F \le 0.25$ |
| **菲涅尔角谱法 (ASM)** | 角谱传递函数 | 近场精确传播，含倏逝波截断 |
| **菲涅尔脉冲响应法 (IR)** | 脉冲响应 + FFT 卷积 | 近场传播，$dx^2$ 归一化 |
| **瑞利-索末菲 (RS)** | 严格角谱传递函数 | 精确传播，无近轴近似 |

所有模型均经过科学正确性审查，包括 FFT 归一化、`ifftshift`/`fftshift` 一致性、倏逝波处理等关键细节。

### 孔径类型

支持 8 种孔径几何，均支持平移和旋转：

- **圆形** — 经典圆孔衍射（Airy 斑）
- **矩形** — 单缝/矩形孔衍射，支持宽高比调节
- **三角形** — 等边三角形孔径
- **六边形** — 正六边形（尖顶），几何条件 $|x| + \sqrt{3}|y| \le \sqrt{3}R$
- **圆环** — 环形孔径，内外径比可调
- **星形** — 多角星形，顶点数和内径比可调
- **双缝** — 杨氏双缝干涉，缝宽和间距可调
- **光栅** — 多缝衍射光栅，缝数/缝宽/间距可调

支持**复合孔径**（布尔运算组合）和自定义多边形（射线法判断）。

### 波前像差

基于 **OSA/ANSI 标准 Zernike 多项式**，支持 15 项像差：

- Pistion, Tip, Tilt
- Defocus, Astigmatism (0°/45°)
- Coma (X/Y), Trefoil (X/Y)
- Spherical, Secondary Astigmatism (0°/45°)
- Quadrafoil (X/Y)

孔径外区域自动裁剪（`rho_safe` 机制防止高阶项数值溢出），像差通过相位因子 $\exp(i \cdot 2\pi W / \lambda)$ 施加。

### 彩色衍射模拟

- **Sellmeier 色散公式**：SF11 等光学玻璃的波长折射率计算
- **多波长叠加**：支持自定义波长组合与权重
- **光源预设**：D65 白光、钠灯、汞灯、LED 白光、RGB 激光
- **真彩色渲染**：基于 Dan Bruton 算法的波长→RGB 转换

### 分析工具

| 工具 | 功能 |
|------|------|
| **PSF 分析** | 点扩散函数峰值、总能量、质心定位 |
| **MTF 分析** | 调制传递函数（OTF 的模），径向 MTF 曲线 |
| **Strehl 比** | 有理想参考时计算精确 Strehl 比，无参考时标注 N/A |
| **FWHM 测量** | 基线减除 + 线性插值的半高全宽测量 |
| **围入能量** | 50%/86% 围入能量半径 |
| **径向剖面** | 径向平均强度分布 |
| **曲线拟合** | 高斯拟合、Airy 函数拟合（精确 FWHM 估计 $r \approx 1.61634$）、多峰高斯拟合 |
| **参数扫描** | 批量扫描波长/距离/孔径等参数 |
| **传播动画** | 不同传播距离的衍射图样动画 |
| **接收面分析** | 不同接收面形状的衍射分析 |

### 高精度渲染

| 设置 | 选项 | 说明 |
|------|------|------|
| **FFT 计算精度** | float32 / float64 / longdouble | 控制输入场数据类型，float64 为默认推荐 |
| **图像插值** | 最近邻 / 双线性 / 高精度 (float64) | pyqtgraph 渲染精度，float64 提供更高显示精度 |
| **OpenGL 加速** | 开/关 | 硬件加速渲染，大数据集显著提速 |
| **抗锯齿** | 开/关 | 线条和曲线平滑渲染 |
| **HiDPI** | 开/关 | 高分辨率显示器缩放支持 |
| **精度预设** | 草稿(256) / 标准(512) / 高精度(1024) / 超高精度(2048) / 极限精度(4096) | 网格大小和零填充因子一键切换 |

## 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| **GUI 框架** | PyQt6 | 主窗口、对话框、控件 |
| **科学绘图** | pyqtgraph | 衍射图样实时渲染、截面图、MTF 曲线 |
| **数值计算** | NumPy | FFT、数组运算 |
| **科学计算** | SciPy | Zernike 径向多项式、曲线拟合 (`curve_fit`)、`find_peaks` |
| **JIT 加速** | Numba | 可选的 CPU JIT 编译加速 |
| **GPU 加速** | CuPy | 可选的 CUDA GPU 加速（实验性） |
| **图像处理** | OpenCV, Pillow | 图像导出、格式转换 |
| **数据存储** | h5py, tifffile | HDF5 / TIFF 科学数据导出 |
| **配置管理** | PyYAML, QSettings | YAML 配置文件 + Qt 持久化设置 |
| **数据校验** | Pydantic | 参数模型验证 |
| **打包分发** | PyInstaller | 单文件可执行程序打包 |

## 项目结构

```
diffraction_lab/
├── src/
│   ├── core/                    # 核心物理引擎
│   │   ├── diffraction.py       # 衍射计算引擎（4种传播模型）
│   │   ├── aperture.py          # 孔径定义（8种几何 + 复合孔径）
│   │   ├── optics.py            # 光学工具函数（OTF/MTF/Fresnel数/远场判据）
│   │   ├── zernike.py           # Zernike 多项式与波前像差
│   │   ├── chromatic.py         # 彩色衍射（Sellmeier色散/多波长叠加）
│   │   └── units.py             # 物理常数与单位
│   ├── analysis/                # 分析工具
│   │   ├── psf_mtf.py           # PSF/MTF/OTF/Strehl 计算
│   │   ├── fitting.py           # 曲线拟合（高斯/Airy/多峰高斯）
│   │   └── measurements.py      # 测量工具（FWHM/径向剖面/围入能量）
│   ├── gui/                     # 图形界面
│   │   ├── main_window.py       # 主窗口
│   │   ├── canvas.py            # 衍射图样画布（OpenGL/抗锯齿/高精度）
│   │   ├── control_panel.py     # 参数控制面板
│   │   ├── profile_plot.py      # 截面分析图
│   │   ├── data_panel.py        # 测量数据面板
│   │   ├── colormaps.py         # 颜色映射
│   │   ├── shape_editor.py      # 孔径形状编辑器
│   │   └── dialogs/             # 对话框
│   │       ├── settings_dialog.py       # 设置（精度/渲染/高级）
│   │       ├── analysis_dialog.py       # MTF/PSF 分析
│   │       ├── fitting_dialog.py        # 曲线拟合
│   │       ├── wavefront_dialog.py      # 波前像差分析
│   │       ├── chromatic_diffraction_dialog.py  # 彩色衍射
│   │       ├── propagation_dialog.py    # 传播动画
│   │       ├── parameter_scan_dialog.py # 参数扫描
│   │       ├── receiver_surface_dialog.py # 接收面分析
│   │       ├── optical_scene_dialog.py  # 光学场景预设
│   │       ├── export_dialog.py         # 数据/图像导出
│   │       └── help_dialog.py           # 帮助文档
│   ├── utils/                   # 工具模块
│   │   ├── preferences.py       # 偏好设置（QSettings 持久化）
│   │   ├── config.py            # YAML 配置管理
│   │   ├── io_handler.py        # 数据导入导出
│   │   └── logger.py            # 日志系统
│   └── main.py                  # 入口（GUI/CLI 双模式）
├── assets/help/                 # 帮助文档
├── config/                      # 默认配置
├── tests/                       # 单元测试
├── requirements.txt
└── setup.py
```

## 安装与运行

### 环境要求

- Python >= 3.10
- Windows / macOS / Linux

### 安装依赖

```bash
cd "EM Field Studio"
pip install -r diffraction_lab/requirements.txt
```

### 启动 GUI

```bash
python -m diffraction_lab.src.main
```

### CLI 模式

```bash
python -m diffraction_lab.src.main --cli --aperture circle --size 50 --wavelength 532 --model fraunhofer --output result.h5
```

### 打包为可执行文件

```bash
pyinstaller diffraction_lab/em_field_studio.spec
```

## 科学正确性保障

本项目经过系统性科学审查，已验证并修复以下关键问题：

- **FFT 归一化**：Fresnel IR 方法使用 $dx^2$ 归一化连续卷积近似，与 ASM 方法保持一致
- **`ifftshift` vs `fftshift`**：居中数据做 FFT 前统一使用 `ifftshift`，避免奇数尺寸偏移
- **OTF 计算**：PSF 先 `ifftshift` 移到原点再做 FFT，确保 DC 分量在 `[0,0]`
- **RS 传递函数**：标准角谱形式 $H = \exp(ikz\sqrt{1-\lambda^2 f_x^2 - \lambda^2 f_y^2})$，无多余前缀
- **远场判据**：`is_far_field` 阈值 $N_F \le 0.25$，与 `far_field_distance` 一致
- **Strehl 比**：无理想参考时返回 N/A（-1.0），有参考时不做 `min` 截断
- **Airy 拟合**：FWHM 对应 $r \approx 1.61634$，半径使用精确零点 `jn_zeros(1,1)[0]`
- **六边形几何**：尖顶六边形条件 $|x| + \sqrt{3}|y| \le \sqrt{3}R$
- **Zernike 溢出防护**：孔径外 `rho` 裁剪为 0，防止高阶项数值溢出

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Return` | 更新计算 |
| `R` | 重置视图 |
| `F` | 适应窗口 |
| `H` | 水平截面 |
| `V` | 垂直截面 |
| `W` | FWHM 测量 |
| `T` | 切换主题 |
| `Ctrl+E` | 导出图像 |
| `Ctrl+D` | 导出数据 |
| `Ctrl+S` | 保存配置 |
| `F1` | 帮助 |

## 许可证

本项目仅供学习和研究使用。

## Project Status

This repository is maintained as part of SuiYueMengHen's open-source project collection. Issues and suggestions are welcome.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
