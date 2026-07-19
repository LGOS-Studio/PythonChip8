# LGOS Studio · PythonChip8

> 一款基于 Python 标准库实现的 **CHIP‑8 虚拟机模拟器**，零依赖、单文件、Tkinter 原生 GUI，界面风格致敬 VMware / VirtualBox 虚拟机管理器。

![Python 3.6+](https://img.shields.io/badge/Python-3.6+-green.svg)
![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)
![All Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

---

## ✨ 特性

- 🎮 **完整 CHIP‑8 指令集** — 35 条标准指令全覆盖（绘图 / 音效定时器 / BCD / 按键等待）
- 🪟 **VMware 风格 GUI** — 左侧虚拟机列表 + 右侧屏幕 + 寄存器面板 + 状态栏
- 📦 **零第三方依赖** — 仅使用 `tkinter` / `random` / `time` / `os` 等标准库
- 🔍 **实时调试视图** — PC、SP、I、DT、ST 及 V0–VF 每帧刷新
- ⌨️ **物理键盘映射** — CHIP‑8 十六键 → PC 键盘自然布局
- 📂 **ROM 热加载** — 运行 / 暂停 / 重置，支持任意 `.ch8` 文件

---

## 📸 运行效果（此处为抽象版 :D）

```txt
┌─────────────────────────────────────────────────┐
│  📂 加载 ROM  ▶ 运行  ⏸ 暂停  🔄 重置           │
├──────────┬──────────────────────────────────────┤
│ 虚拟机    │  CHIP-8 屏幕 (64×32, 绿色像素)       │
│ ┌──────┐ │                                      │
│ │CHIP-8│ │                                      │
│ └──────┘ │                                      │
│          │  PC:0x2xx  SP:0x0  I:0xxxx  DT:0x00  │
│          │  V0:00 V1:00 ... VF:00               │
├──────────┴──────────────────────────────────────┤
│ 就绪 - 请加载 ROM 文件 (.ch8)                     │
└─────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/LGOS-Studio/PythonChip8.git
cd PythonChip8
```

### 2. 运行（无需 pip install）

```bash
python chip8_vm.py
```

> 💡 Python 3.6+ 自带 `tkinter`，Windows / macOS 通常开箱即用；Linux 若报错 `No module named _tkinter`，请安装 `sudo apt install python3-tk`（Debian/Ubuntu）或对应发行版包。

> 💡 同时，我们也提供编译好的 Windows 的 exe 程序，可以直接打开[链接](./Releases/latest)下载

### 3. 加载 ROM

点击 **📂 加载 ROM**，选择 `.ch8` 文件即可。

> 🎲 经典 ROM 推荐：Tetris、Space Invaders、Pong、BRIX —— 网上搜索 "[CHIP‑8 ROM pack](https://www.bing.com/search?q=CHIP‑8%20ROM%20pack")" 可下载到大量测试用 ROM。

---

## ⌨️ 键盘映射

CHIP‑8 原生是 4×4 十六进制键盘，映射为 PC 键盘如下：

| CHIP‑8 | 1 | 2 | 3 | C |
|--------|---|---|---|---|
| **PC** | `1` | `2` | `3` | `4` |

| CHIP‑8 | 4 | 5 | 6 | D |
|--------|---|---|---|---|
| **PC** | `Q` | `W` | `E` | `R` |

| CHIP‑8 | 7 | 8 | 9 | E |
|--------|---|---|---|---|
| **PC** | `A` | `S` | `D` | `F` |

| CHIP‑8 | A | 0 | B | F |
|--------|---|---|---|---|
| **PC** | `Z` | `X` | `C` | `V` |

---

## 📁 项目结构

```
PythonChip8/
├── emulator.py          # 单文件主程序（VM 核心 + GUI）
├── README.md            # 你正在看的这份文档
└── roms/                # （可选）自行放置 .ch8 ROM 文件
```

整个模拟器 **仅一个 `.py` 文件**，核心 `Chip8` 类与 `VMApp` GUI 类共存于同一文件，方便学习 & 二次修改。

---

## 🛠 架构简述

```
┌────────────┐
│  Tkinter UI │  ← 画布 64×32 / 寄存器面板 / 控制按钮
├────────────┤
│  Chip8 VM   │  ← 4KB 内存 / 16 寄存器 / 栈 / 定时器
│  (cycle())  │  ← 解码 35 条指令（0x0NNN ~ 0xFNNN）
└────────────┘
      ↑
  KeyEvent (tkinter bind)
```

- **CPU 循环**：`cycle()` 每帧执行 `cycle_rate` 条指令（默认 10），GUI 以 ~60 fps 刷新
- **定时器**：`delay_timer` / `sound_timer` 每帧 −1（CHIP‑8 标准 60 Hz）
- **显示**：`display[32][64]` 位图 → Canvas 放大 `SCALE=10` 渲染为绿色方块

---

## ⚙️ 可调参数（源码内）

```python
SCALE = 10           # 像素放大倍数（改大屏幕更粗犷）
cycle_rate = 10      # 每帧执行指令数（调大 = 跑更快）
```

---

## 📋 TODO / 扩展方向

- [ ] Super‑CHIP (CHIP‑48 / SCHIP) 扩展指令 & 128×64 分辨率
- [ ] 声音输出（`winsound` / `subprocess` beep）
- [ ] 断点 / 单步执行 / 指令反汇编面板
- [ ] 多虚拟机实例（左侧列表真正可切换）
- [ ] 保存 / 加载状态快照

---

## 📜 协议

MIT © 2025–Present **LGOS Studio**

> 欢迎 PR、Issue、Star ⭐ — 让这台小虚拟机再长大一点
