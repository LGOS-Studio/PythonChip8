#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox
import random
import time
import os

# ---------- CHIP-8 核心 ----------
class Chip8:
    def __init__(self):
        self.reset()

    def reset(self):
        # 内存 4KB
        self.memory = [0] * 4096
        # 16 个通用寄存器 V0-VF
        self.V = [0] * 16
        self.I = 0          # 地址寄存器
        self.pc = 0x200     # 程序计数器（从 0x200 开始）
        self.sp = 0         # 栈指针
        self.stack = [0] * 16
        self.delay_timer = 0
        self.sound_timer = 0
        # 显示缓冲区 64x32
        self.display = [[0]*64 for _ in range(32)]
        self.draw_flag = False
        # 键盘状态
        self.keys = [0]*16
        self.waiting_key = -1   # -1 表示未等待按键

        # 加载字体到内存 0x000-0x1FF
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        for i, byte in enumerate(fontset):
            self.memory[i] = byte

    def load_rom(self, filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
        if len(data) > 3584:  # 最大 0xFFF - 0x200 = 3584 bytes
            raise ValueError("ROM too large")
        for i, byte in enumerate(data):
            self.memory[0x200 + i] = byte

    def cycle(self):
        """执行一个指令周期"""
        if self.waiting_key != -1:
            return  # 等待按键

        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc += 2

        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        nn = opcode & 0x00FF
        nnn = opcode & 0x0FFF

        # 解码并执行
        if opcode == 0x00E0:  # CLS
            self.display = [[0]*64 for _ in range(32)]
            self.draw_flag = True
        elif opcode == 0x00EE:  # RET
            self.sp -= 1
            self.pc = self.stack[self.sp]
        elif (opcode & 0xF000) == 0x1000:  # JP addr
            self.pc = nnn
        elif (opcode & 0xF000) == 0x2000:  # CALL addr
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = nnn
        elif (opcode & 0xF000) == 0x3000:  # SE Vx, byte
            if self.V[x] == nn:
                self.pc += 2
        elif (opcode & 0xF000) == 0x4000:  # SNE Vx, byte
            if self.V[x] != nn:
                self.pc += 2
        elif (opcode & 0xF000) == 0x5000 and (opcode & 0x000F) == 0x0000:  # SE Vx, Vy
            if self.V[x] == self.V[y]:
                self.pc += 2
        elif (opcode & 0xF000) == 0x6000:  # LD Vx, byte
            self.V[x] = nn
        elif (opcode & 0xF000) == 0x7000:  # ADD Vx, byte
            self.V[x] = (self.V[x] + nn) & 0xFF
        elif (opcode & 0xF000) == 0x8000:
            if n == 0:      # LD Vx, Vy
                self.V[x] = self.V[y]
            elif n == 1:    # OR
                self.V[x] |= self.V[y]
            elif n == 2:    # AND
                self.V[x] &= self.V[y]
            elif n == 3:    # XOR
                self.V[x] ^= self.V[y]
            elif n == 4:    # ADD Vx, Vy (with carry)
                result = self.V[x] + self.V[y]
                self.V[0xF] = 1 if result > 255 else 0
                self.V[x] = result & 0xFF
            elif n == 5:    # SUB Vx, Vy
                self.V[0xF] = 1 if self.V[x] >= self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif n == 6:    # SHR Vx {, Vy}
                self.V[0xF] = self.V[x] & 1
                self.V[x] >>= 1
            elif n == 7:    # SUBN Vx, Vy
                self.V[0xF] = 1 if self.V[y] >= self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif n == 0xE:  # SHL Vx {, Vy}
                self.V[0xF] = (self.V[x] >> 7) & 1
                self.V[x] = (self.V[x] << 1) & 0xFF
        elif (opcode & 0xF000) == 0x9000 and (opcode & 0x000F) == 0x0000:  # SNE Vx, Vy
            if self.V[x] != self.V[y]:
                self.pc += 2
        elif (opcode & 0xF000) == 0xA000:  # LD I, addr
            self.I = nnn
        elif (opcode & 0xF000) == 0xB000:  # JP V0, addr
            self.pc = nnn + self.V[0]
        elif (opcode & 0xF000) == 0xC000:  # RND Vx, byte
            self.V[x] = random.randint(0, 255) & nn
        elif (opcode & 0xF000) == 0xD000:  # DRW Vx, Vy, nibble
            x_pos = self.V[x] % 64
            y_pos = self.V[y] % 32
            self.V[0xF] = 0
            for row in range(n):
                if y_pos + row >= 32:
                    break
                sprite_byte = self.memory[self.I + row]
                for col in range(8):
                    if x_pos + col >= 64:
                        break
                    pixel = (sprite_byte >> (7 - col)) & 1
                    current = self.display[y_pos + row][x_pos + col]
                    if pixel:
                        if current == 1:
                            self.V[0xF] = 1
                        self.display[y_pos + row][x_pos + col] ^= 1
            self.draw_flag = True
        elif (opcode & 0xF000) == 0xE000:
            if nn == 0x9E:  # SKP Vx
                if self.keys[self.V[x]]:
                    self.pc += 2
            elif nn == 0xA1:  # SKNP Vx
                if not self.keys[self.V[x]]:
                    self.pc += 2
        elif (opcode & 0xF000) == 0xF000:
            if nn == 0x07:  # LD Vx, DT
                self.V[x] = self.delay_timer
            elif nn == 0x0A:  # LD Vx, K
                self.waiting_key = x
            elif nn == 0x15:  # LD DT, Vx
                self.delay_timer = self.V[x]
            elif nn == 0x18:  # LD ST, Vx
                self.sound_timer = self.V[x]
            elif nn == 0x1E:  # ADD I, Vx
                self.I += self.V[x]
                if self.I > 0xFFF:
                    self.I &= 0xFFF
                    self.V[0xF] = 1  # some implementations set VF on overflow
            elif nn == 0x29:  # LD F, Vx (font sprite)
                self.I = self.V[x] * 5
            elif nn == 0x33:  # LD B, Vx (BCD)
                value = self.V[x]
                self.memory[self.I] = value // 100
                self.memory[self.I+1] = (value // 10) % 10
                self.memory[self.I+2] = value % 10
            elif nn == 0x55:  # LD [I], Vx (store registers)
                for i in range(x+1):
                    self.memory[self.I + i] = self.V[i]
            elif nn == 0x65:  # LD Vx, [I] (load registers)
                for i in range(x+1):
                    self.V[i] = self.memory[self.I + i]

    def key_pressed(self, key_index):
        """当有键按下时调用（用于处理等待按键）"""
        if self.waiting_key != -1:
            self.V[self.waiting_key] = key_index
            self.waiting_key = -1

    def tick_timers(self):
        """每秒调用60次（每帧）减少定时器"""
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1


# ---------- GUI ----------
SCALE = 10   # 每个像素放大倍数
CANVAS_W = 64 * SCALE
CANVAS_H = 32 * SCALE

class VMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LGOS Virtual Machine (CHIP-8)")
        self.geometry("900x650")
        self.resizable(False, False)

        self.chip = Chip8()
        self.running = False
        self.rom_loaded = False

        self._build_gui()
        self._bind_keys()

        # 定时器：60Hz 模拟时钟
        self.tick_id = None
        self.cycle_rate = 10  # 每帧执行的指令数（可调）

    def _build_gui(self):
        # 主布局：左列表 + 右内容
        left_frame = tk.Frame(self, width=200, bg="#2b2b2b", relief=tk.RIDGE, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="虚拟机", bg="#2b2b2b", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(pady=10)

        # 虚拟机列表（只有一个）
        vm_listbox = tk.Listbox(left_frame, bg="#3c3f41", fg="white",
                                selectbackground="#0078d4", borderwidth=0,
                                highlightthickness=0, font=("Consolas", 11))
        vm_listbox.insert(tk.END, "Virtual Machine")
        vm_listbox.selection_set(0)
        vm_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 右侧主区域
        right_frame = tk.Frame(self, bg="#1e1e1e")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(right_frame, text="运行状态",
                               bg="#1e1e1e", fg="#cccccc",
                               font=("Segoe UI", 14, "bold"))
        title_label.pack(pady=(10, 5))

        # 画布（屏幕）
        canvas_frame = tk.Frame(right_frame, bg="#111111", bd=2, relief=tk.SUNKEN)
        canvas_frame.pack(pady=5)
        self.canvas = tk.Canvas(canvas_frame, width=CANVAS_W, height=CANVAS_H,
                                bg="black", highlightthickness=0)
        self.canvas.pack()

        # 状态面板
        state_frame = tk.Frame(right_frame, bg="#252526", bd=1, relief=tk.GROOVE)
        state_frame.pack(fill=tk.X, padx=20, pady=5)

        # 寄存器显示
        reg_frame = tk.Frame(state_frame, bg="#252526")
        reg_frame.pack(side=tk.LEFT, padx=10, pady=5)
        self.reg_labels = {}
        for name in ['PC', 'SP', 'I', 'DT', 'ST']:
            lbl = tk.Label(reg_frame, text=f"{name}: 0x000", bg="#252526",
                           fg="#9cdcfe", font=("Consolas", 10))
            lbl.pack(anchor='w')
            self.reg_labels[name] = lbl

        # V寄存器 (V0-VF)
        v_frame = tk.Frame(state_frame, bg="#252526")
        v_frame.pack(side=tk.LEFT, padx=20, pady=5)
        self.v_labels = []
        for i in range(16):
            lbl = tk.Label(v_frame, text=f"V{i:01X}: 0x00", bg="#252526",
                           fg="#ce9178", font=("Consolas", 9))
            lbl.grid(row=i//4, column=i%4, sticky='w', padx=2)
            self.v_labels.append(lbl)

        # 控制按钮
        btn_frame = tk.Frame(right_frame, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        self.load_btn = tk.Button(btn_frame, text="📂 加载 ROM", command=self.load_rom,
                                  bg="#0e639c", fg="white", padx=10, pady=4,
                                  font=("Segoe UI", 10))
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.run_btn = tk.Button(btn_frame, text="▶ 运行", command=self.start_vm,
                                 bg="#1a73e8", fg="white", padx=10, pady=4,
                                 font=("Segoe UI", 10), state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = tk.Button(btn_frame, text="⏸ 暂停", command=self.pause_vm,
                                   bg="#d32f2f", fg="white", padx=10, pady=4,
                                   font=("Segoe UI", 10), state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = tk.Button(btn_frame, text="🔄 重置", command=self.reset_vm,
                                   bg="#555555", fg="white", padx=10, pady=4,
                                   font=("Segoe UI", 10), state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # 底部状态栏
        self.status_bar = tk.Label(right_frame, text="就绪 - 请加载 ROM 文件 (.ch8)",
                                   bg="#007acc", fg="white", anchor='w',
                                   font=("Segoe UI", 9))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _bind_keys(self):
        # 键盘映射（CHIP-8 16键 -> 物理键盘）
        # 典型映射：1 2 3 4 -> Q W E R; A S D F -> A S D F; Z X C V -> Z X C V
        self.key_map = {
            '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
            'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
            'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
            'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
        }
        self.bind('<KeyPress>', self._on_key_down)
        self.bind('<KeyRelease>', self._on_key_up)

    def _on_key_down(self, event):
        char = event.char.lower()
        if char in self.key_map:
            idx = self.key_map[char]
            self.chip.keys[idx] = 1
            self.chip.key_pressed(idx)

    def _on_key_up(self, event):
        char = event.char.lower()
        if char in self.key_map:
            idx = self.key_map[char]
            self.chip.keys[idx] = 0

    def load_rom(self):
        path = filedialog.askopenfilename(
            title="选择 CHIP-8 ROM 文件",
            filetypes=[("CHIP-8 ROM", "*.ch8 *.bin"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            self.chip.reset()
            self.chip.load_rom(path)
            self.rom_loaded = True
            self.status_bar.config(text=f"已加载: {os.path.basename(path)}")
            self.run_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            self.update_display()
            self.update_registers()
        except Exception as e:
            messagebox.showerror("错误", f"无法加载 ROM:\n{str(e)}")

    def start_vm(self):
        if not self.rom_loaded:
            return
        self.running = True
        self.run_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.load_btn.config(state=tk.DISABLED)
        self.status_bar.config(text="运行中...")
        self._vm_loop()

    def pause_vm(self):
        self.running = False
        self.run_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.load_btn.config(state=tk.NORMAL)
        self.status_bar.config(text="已暂停")
        if self.tick_id:
            self.after_cancel(self.tick_id)
            self.tick_id = None

    def reset_vm(self):
        self.pause_vm()
        if self.rom_loaded:
            # 重新加载同一 ROM（需保留路径）
            # 这里简单重置芯片，不清除 ROM（已在 load_rom 中重置）
            # 但我们需要保持 ROM 数据，所以手动重置后重新加载
            # 更好的做法：保存 ROM 路径
            pass
        # 简化：重新初始化并加载上次 ROM
        if hasattr(self, '_last_rom_path'):
            self.chip.reset()
            self.chip.load_rom(self._last_rom_path)
        else:
            self.chip.reset()
        self.update_display()
        self.update_registers()
        self.status_bar.config(text="已重置")

    def _vm_loop(self):
        if not self.running:
            return
        # 执行多个指令（提高速度）
        for _ in range(self.cycle_rate):
            self.chip.cycle()
        self.chip.tick_timers()
        self.update_display()
        self.update_registers()
        # 大约 60 fps
        self.tick_id = self.after(16, self._vm_loop)

    def update_display(self):
        self.canvas.delete("all")
        for y in range(32):
            for x in range(64):
                if self.chip.display[y][x]:
                    x0 = x * SCALE
                    y0 = y * SCALE
                    self.canvas.create_rectangle(
                        x0, y0, x0+SCALE, y0+SCALE,
                        fill="#00ff00", outline=""
                    )

    def update_registers(self):
        c = self.chip
        self.reg_labels['PC'].config(text=f"PC: 0x{c.pc:03X}")
        self.reg_labels['SP'].config(text=f"SP: 0x{c.sp:02X}")
        self.reg_labels['I'].config(text=f"I:  0x{c.I:03X}")
        self.reg_labels['DT'].config(text=f"DT: 0x{c.delay_timer:02X}")
        self.reg_labels['ST'].config(text=f"ST: 0x{c.sound_timer:02X}")
        for i, lbl in enumerate(self.v_labels):
            lbl.config(text=f"V{i:01X}: 0x{c.V[i]:02X}")


if __name__ == "__main__":
    app = VMApp()
    app.mainloop()