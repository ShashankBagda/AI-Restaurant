import tkinter as tk
from tkinter import ttk
import time
import math
import random

try:
    import ctypes
    from ctypes import wintypes
except Exception:
    ctypes = None
    wintypes = None

DEFAULT_WORK_TIME = 15
DEFAULT_WARNING_DURATION = 5
DEFAULT_REST_TIME = 10
DEFAULT_SNOOZE_MIN = 5
DEFAULT_LOW_MOTION = False
DEFAULT_EMBED_IN_TASKBAR = False
DEFAULT_POOL_WIDTH = 480
DEFAULT_POOL_HEIGHT = 100
DEFAULT_TASKBAR_LEFT_OFFSET = 8
DEFAULT_SHARK_SCALE = 1.0
DEFAULT_FURIOUS_DELAY = 8
FURIOUS_BG = "#B71C1C"

MIN_POOL_WIDTH = 240
MIN_POOL_HEIGHT = 70


class WakeySharkApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wakey Shark")
        self.root.resizable(False, False)
        self.bg_color = "#000001"
        self.root.configure(bg=self.bg_color)
        try:
            self.root.wm_attributes("-transparentcolor", self.bg_color)
        except tk.TclError:
            pass
        self.root.overrideredirect(True)

        self.work_time = DEFAULT_WORK_TIME
        self.warning_duration = DEFAULT_WARNING_DURATION
        self.rest_time = DEFAULT_REST_TIME
        self.strict_mode = False
        self.always_on_top = True
        self.snooze_minutes = DEFAULT_SNOOZE_MIN
        self.snooze_until = 0
        self.snooze_started = 0
        self.meeting_mode = False
        self.meeting_started = 0
        self.angry_start_time = 0
        self.is_furious = False
        self.prev_geometry = None
        self.prev_pool = None
        self.swim_y = 0
        self.furious_vx = 10
        self.furious_vy = 7
        self.embed_in_taskbar = DEFAULT_EMBED_IN_TASKBAR
        self.taskbar_left_offset = DEFAULT_TASKBAR_LEFT_OFFSET
        self.taskbar_hwnd = None
        self._original_style = None
        self._original_exstyle = None
        self._running = True
        self._bg_size = None
        self.low_motion = DEFAULT_LOW_MOTION
        self.frame_delay_ms = 100 if self.low_motion else 40
        self.shark_scale = DEFAULT_SHARK_SCALE
        self.furious_delay = DEFAULT_FURIOUS_DELAY

        self.state = "CUTE"
        self.start_time = time.time()
        self.rest_start_time = 0

        self.pool_width = DEFAULT_POOL_WIDTH
        self.pool_height = DEFAULT_POOL_HEIGHT
        self.swim_y = self.pool_height * 0.55

        self.canvas = tk.Canvas(
            self.root,
            width=self.pool_width,
            height=self.pool_height,
            bg=self.bg_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.outfits = [
            "None",
            "Tie",
            "Top Hat",
            "Sunglasses",
            "Mohawk",
            "Beanie",
            "Crown",
            "Headphones",
            "Scarf",
        ]
        self.current_outfit_index = 0

        self.overlay = None
        self.particles = []
        self.tick_count = 0
        self.blink_timer = 0
        self.is_blinking = False

        self.swim_x = self.pool_width * 0.2
        self.swim_dir = 1
        self.swim_speed = 1.2
        self.facing = 1
        self.last_shark_pos = (self.pool_width / 2, self.pool_height / 2)

        self._build_settings_window()
        self._drag_data = {"x": 0, "y": 0, "is_dragging": False}

        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<Button-3>", self.show_settings)
        self.root.bind_all("<Escape>", self.emergency_reset)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

        self.root.deiconify()
        self.root.geometry(f"{self.pool_width}x{self.pool_height}")
        try:
            self.root.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        self.dock_bottom_left()

        self.animate()
        self.root.mainloop()

    def _shutdown(self):
        if not self._running:
            return
        self._running = False
        self.destroy_overlay()
        try:
            if self.settings and self.settings.winfo_exists():
                self.settings.destroy()
        except tk.TclError:
            pass
        try:
            self._release_from_taskbar()
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        app_menu = tk.Menu(menubar, tearoff=0)
        app_menu.add_command(label="Settings", command=self.show_settings)
        app_menu.add_command(label="Snooze Now", command=self.snooze_now)
        app_menu.add_command(label="Meeting Mode", command=self.toggle_meeting)
        app_menu.add_command(label="Reset Timer", command=lambda: self.reset_timer(dock=True))
        app_menu.add_command(label="Force Rest", command=self.trigger_rest)
        app_menu.add_command(label="Minimize", command=self.minimize_window)
        app_menu.add_separator()
        app_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="Wakey Shark", menu=app_menu)
        self.root.config(menu=menubar)

    def _build_settings_window(self):
        self.settings = tk.Toplevel(self.root)
        self.settings.title("Wakey Shark Settings")
        self.settings.resizable(False, False)
        self.settings.protocol("WM_DELETE_WINDOW", self.settings.withdraw)

        self.work_time_var = tk.DoubleVar(value=self.work_time / 60.0)
        self.warning_duration_var = tk.DoubleVar(value=self.warning_duration / 60.0)
        self.rest_time_var = tk.DoubleVar(value=self.rest_time / 60.0)
        self.snooze_minutes_var = tk.DoubleVar(value=self.snooze_minutes)
        self.low_motion_var = tk.BooleanVar(value=self.low_motion)
        self.meeting_mode_var = tk.BooleanVar(value=self.meeting_mode)
        self.shark_scale_var = tk.DoubleVar(value=self.shark_scale)
        self.outfit_var = tk.StringVar(value=self.outfits[self.current_outfit_index])
        self.pool_width_var = tk.IntVar(value=self.pool_width)
        self.pool_height_var = tk.IntVar(value=self.pool_height)
        self.status_var = tk.StringVar(value="State: CUTE")
        self.remaining_var = tk.StringVar(value="Remaining: --")

        pad = {"padx": 8, "pady": 6}

        timers_frame = ttk.LabelFrame(self.settings, text="Timers (minutes)")
        timers_frame.grid(row=0, column=0, sticky="ew", **pad)
        timers_frame.columnconfigure(1, weight=1)

        ttk.Label(timers_frame, text="Work").grid(row=0, column=0, sticky="w")
        tk.Spinbox(
            timers_frame,
            from_=0.1,
            to=240.0,
            textvariable=self.work_time_var,
            increment=0.1,
            format="%.2f",
            width=8,
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(timers_frame, text="Warning").grid(row=1, column=0, sticky="w")
        tk.Spinbox(
            timers_frame,
            from_=0.05,
            to=60.0,
            textvariable=self.warning_duration_var,
            increment=0.05,
            format="%.2f",
            width=8,
        ).grid(row=1, column=1, sticky="w")

        ttk.Label(timers_frame, text="Rest").grid(row=2, column=0, sticky="w")
        tk.Spinbox(
            timers_frame,
            from_=0.1,
            to=120.0,
            textvariable=self.rest_time_var,
            increment=0.1,
            format="%.2f",
            width=8,
        ).grid(row=2, column=1, sticky="w")

        ttk.Label(timers_frame, text="Snooze (minutes)").grid(row=3, column=0, sticky="w")
        tk.Spinbox(
            timers_frame,
            from_=0.1,
            to=240.0,
            textvariable=self.snooze_minutes_var,
            increment=0.1,
            format="%.2f",
            width=8,
        ).grid(row=3, column=1, sticky="w")

        outfit_frame = ttk.LabelFrame(self.settings, text="Outfit")
        outfit_frame.grid(row=1, column=0, sticky="ew", **pad)
        ttk.OptionMenu(
            outfit_frame,
            self.outfit_var,
            self.outfits[self.current_outfit_index],
            *self.outfits,
        ).grid(row=0, column=0, sticky="w")

        behavior_frame = ttk.LabelFrame(self.settings, text="Behavior")
        behavior_frame.grid(row=2, column=0, sticky="ew", **pad)
        ttk.Label(behavior_frame, text="Always on Top: Enabled").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Checkbutton(
            behavior_frame,
            text="Low Motion",
            variable=self.low_motion_var,
        ).grid(row=1, column=0, sticky="w")

        pool_frame = ttk.LabelFrame(self.settings, text="Window")
        pool_frame.grid(row=3, column=0, sticky="ew", **pad)
        ttk.Label(pool_frame, text="Width").grid(row=0, column=0, sticky="w")
        tk.Spinbox(
            pool_frame,
            from_=MIN_POOL_WIDTH,
            to=2000,
            textvariable=self.pool_width_var,
            width=8,
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(pool_frame, text="Height").grid(row=1, column=0, sticky="w")
        tk.Spinbox(
            pool_frame,
            from_=MIN_POOL_HEIGHT,
            to=600,
            textvariable=self.pool_height_var,
            width=8,
        ).grid(row=1, column=1, sticky="w")

        appearance_frame = ttk.LabelFrame(self.settings, text="Appearance")
        appearance_frame.grid(row=4, column=0, sticky="ew", **pad)
        ttk.Label(appearance_frame, text="Shark Size").grid(row=0, column=0, sticky="w")
        ttk.Scale(
            appearance_frame,
            from_=0.2,
            to=2.5,
            variable=self.shark_scale_var,
            orient="horizontal",
            command=self.on_shark_scale_change,
        ).grid(row=0, column=1, sticky="ew")
        appearance_frame.columnconfigure(1, weight=1)

        action_frame = ttk.Frame(self.settings)
        action_frame.grid(row=5, column=0, sticky="ew", **pad)
        ttk.Button(action_frame, text="Apply", command=self.apply_settings).grid(
            row=0, column=0, sticky="ew", padx=2
        )
        ttk.Button(action_frame, text="Snooze Now", command=self.snooze_now).grid(
            row=0, column=1, sticky="ew", padx=2
        )
        ttk.Button(action_frame, text="Meeting Mode", command=self.toggle_meeting).grid(
            row=0, column=2, sticky="ew", padx=2
        )
        ttk.Button(action_frame, text="Reset Timer", command=lambda: self.reset_timer(dock=True)).grid(
            row=0, column=3, sticky="ew", padx=2
        )
        ttk.Button(action_frame, text="Force Rest", command=self.trigger_rest).grid(
            row=0, column=4, sticky="ew", padx=2
        )
        ttk.Button(action_frame, text="Exit", command=self._shutdown).grid(
            row=0, column=5, sticky="ew", padx=2
        )

        status_frame = ttk.LabelFrame(self.settings, text="Status")
        status_frame.grid(row=6, column=0, sticky="ew", **pad)
        ttk.Label(status_frame, textvariable=self.status_var).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(status_frame, textvariable=self.remaining_var).grid(
            row=1, column=0, sticky="w"
        )

    def show_settings(self, event=None):
        if not self._running:
            return
        if self.settings is None or not self.settings.winfo_exists():
            self._build_settings_window()
        self.settings.deiconify()
        self.settings.lift()

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Settings", command=self.show_settings)
        self.context_menu.add_command(label="Snooze Now", command=self.snooze_now)
        self.context_menu.add_command(label="Meeting Mode", command=self.toggle_meeting)
        self.context_menu.add_command(label="Reset Timer", command=lambda: self.reset_timer(dock=True))
        self.context_menu.add_command(label="Force Rest", command=self.trigger_rest)
        self.context_menu.add_command(label="Minimize", command=self.minimize_window)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Quit", command=self.root.quit)

    def show_context_menu(self, event):
        if not self._running:
            return
        if self.context_menu is None:
            self._build_context_menu()
        self.context_menu.post(event.x_root, event.y_root)

    def minimize_window(self):
        if not self._running:
            return
        try:
            self.root.iconify()
        except tk.TclError:
            pass

    def on_shark_scale_change(self, value):
        try:
            self.shark_scale = float(value)
        except ValueError:
            return

    def _clamp_int(self, value, min_val, max_val):
        try:
            value = int(value)
        except Exception:
            value = min_val
        return max(min_val, min(value, max_val))

    def _clamp_float(self, value, min_val, max_val):
        try:
            value = float(value)
        except Exception:
            value = min_val
        return max(min_val, min(value, max_val))

    def apply_settings(self):
        work_min = self._clamp_float(self.work_time_var.get(), 0.1, 240.0)
        warn_min = self._clamp_float(self.warning_duration_var.get(), 0.05, 60.0)
        rest_min = self._clamp_float(self.rest_time_var.get(), 0.1, 120.0)
        self.work_time = work_min * 60.0
        self.warning_duration = warn_min * 60.0
        self.rest_time = rest_min * 60.0
        self.snooze_minutes = self._clamp_float(self.snooze_minutes_var.get(), 0.1, 240.0)
        self.low_motion = bool(self.low_motion_var.get())
        self.shark_scale = float(self.shark_scale_var.get())
        self.set_meeting_mode(bool(self.meeting_mode_var.get()))
        try:
            self.root.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

        outfit_name = self.outfit_var.get()
        if outfit_name in self.outfits:
            self.current_outfit_index = self.outfits.index(outfit_name)

        max_w = self.root.winfo_screenwidth()
        max_h = self.root.winfo_screenheight()
        new_w = self._clamp_int(self.pool_width_var.get(), MIN_POOL_WIDTH, max_w)
        new_h = self._clamp_int(self.pool_height_var.get(), MIN_POOL_HEIGHT, max_h)
        if new_w != self.pool_width or new_h != self.pool_height:
            self.set_pool_size(new_w, new_h)

        self.frame_delay_ms = 100 if self.low_motion else 40
        if self.low_motion:
            self.particles = []
        self.work_time_var.set(self.work_time / 60.0)
        self.warning_duration_var.set(self.warning_duration / 60.0)
        self.rest_time_var.set(self.rest_time / 60.0)
        self.snooze_minutes_var.set(self.snooze_minutes)
        self.pool_width_var.set(self.pool_width)
        self.pool_height_var.set(self.pool_height)
        self.low_motion_var.set(self.low_motion)
        self.meeting_mode_var.set(self.meeting_mode)
        self.shark_scale_var.set(self.shark_scale)

    def set_pool_size(self, width, height):
        if self.embed_in_taskbar and self.taskbar_hwnd:
            rect = self._get_taskbar_rect()
            if rect is not None:
                width = min(width, rect.right - rect.left)
                height = min(height, rect.bottom - rect.top)
        self.pool_width = width
        self.pool_height = height
        self.canvas.config(width=width, height=height)
        self._bg_size = None
        if self.embed_in_taskbar and self.taskbar_hwnd:
            self._set_embedded_geometry(width, height)
        else:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.swim_x = min(max(self.swim_x, width * 0.2), width * 0.8)
        self.last_shark_pos = (self.swim_x, height / 2)

    def _get_work_area(self):
        if ctypes is None or wintypes is None:
            return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        rect = wintypes.RECT()
        SPI_GETWORKAREA = 0x0030
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
        )
        if result:
            return rect.left, rect.top, rect.right, rect.bottom
        return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def _get_taskbar_hwnd(self):
        if ctypes is None or wintypes is None:
            return None
        user32 = ctypes.windll.user32
        user32.FindWindowW.restype = wintypes.HWND
        user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
        hwnd = user32.FindWindowW("Shell_TrayWnd", None)
        return hwnd or None

    def _get_taskbar_rect(self):
        if ctypes is None or wintypes is None:
            return None
        if not self.taskbar_hwnd:
            self.taskbar_hwnd = self._get_taskbar_hwnd()
        if not self.taskbar_hwnd:
            return None
        rect = wintypes.RECT()
        if ctypes.windll.user32.GetWindowRect(
            self.taskbar_hwnd, ctypes.byref(rect)
        ):
            return rect
        return None

    def _set_embedded_geometry(self, width, height):
        rect = self._get_taskbar_rect()
        if rect is None:
            return False

        taskbar_w = rect.right - rect.left
        taskbar_h = rect.bottom - rect.top
        if taskbar_w <= 0 or taskbar_h <= 0:
            return False

        width = min(width, taskbar_w)
        height = min(height, taskbar_h)

        if taskbar_w >= taskbar_h:
            x = max(0, min(self.taskbar_left_offset, taskbar_w - width))
            y = max(0, (taskbar_h - height) // 2)
        else:
            x = max(0, (taskbar_w - width) // 2)
            y = max(0, min(self.taskbar_left_offset, taskbar_h - height))

        hwnd = self.root.winfo_id()
        SWP_NOZORDER = 0x0004
        SWP_NOACTIVATE = 0x0010
        result = ctypes.windll.user32.SetWindowPos(
            hwnd,
            0,
            int(x),
            int(y),
            int(width),
            int(height),
            SWP_NOZORDER | SWP_NOACTIVATE,
        )
        return bool(result)

    def _embed_in_taskbar(self):
        if ctypes is None or wintypes is None:
            return False
        taskbar = self._get_taskbar_hwnd()
        if not taskbar:
            return False

        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        if not hwnd:
            return False
        user32 = ctypes.windll.user32
        GWL_STYLE = -16
        GWL_EXSTYLE = -20
        WS_CHILD = 0x40000000
        WS_POPUP = 0x80000000

        if self._original_style is None:
            self._original_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            self._original_exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        try:
            user32.SetParent(hwnd, taskbar)
            style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            user32.SetWindowLongW(hwnd, GWL_STYLE, (style | WS_CHILD) & ~WS_POPUP)
            self.root.overrideredirect(True)
            self.taskbar_hwnd = taskbar
            if not self._set_embedded_geometry(self.pool_width, self.pool_height):
                raise RuntimeError("SetWindowPos failed")
            return True
        except Exception:
            self._release_from_taskbar()
            return False

    def _release_from_taskbar(self):
        if ctypes is None or wintypes is None:
            return False
        try:
            hwnd = self.root.winfo_id()
        except tk.TclError:
            return False
        user32 = ctypes.windll.user32
        try:
            user32.SetParent(hwnd, 0)
            if self._original_style is not None:
                user32.SetWindowLongW(hwnd, -16, self._original_style)
            if self._original_exstyle is not None:
                user32.SetWindowLongW(hwnd, -20, self._original_exstyle)
            self.root.overrideredirect(False)
        except Exception:
            return False
        self.taskbar_hwnd = None
        return True

    def _apply_taskbar_mode(self):
        if self.embed_in_taskbar:
            if self._embed_in_taskbar():
                return True
            self.embed_in_taskbar = False
            self._release_from_taskbar()
            self._dock_to_taskbar_area()
            return False

        self._release_from_taskbar()
        self._dock_to_taskbar_area()
        return True

    def _dock_to_taskbar_area(self):
        rect = self._get_taskbar_rect()
        if rect is not None:
            taskbar_w = rect.right - rect.left
            taskbar_h = rect.bottom - rect.top
            if taskbar_w > 0 and taskbar_h > 0:
                new_w = min(self.pool_width, taskbar_w)
                new_h = min(self.pool_height, taskbar_h)
                if new_w != self.pool_width or new_h != self.pool_height:
                    self.pool_width = new_w
                    self.pool_height = new_h
                    self.canvas.config(width=new_w, height=new_h)
                    self._bg_size = None
                    if hasattr(self, "pool_width_var"):
                        self.pool_width_var.set(self.pool_width)
                    if hasattr(self, "pool_height_var"):
                        self.pool_height_var.set(self.pool_height)

                if taskbar_w >= taskbar_h:
                    x = rect.left + self.taskbar_left_offset
                    x = max(rect.left, min(x, rect.right - self.pool_width))
                    y = rect.top + (taskbar_h - self.pool_height) // 2
                else:
                    x = rect.left + (taskbar_w - self.pool_width) // 2
                    y = rect.top + self.taskbar_left_offset
                    y = max(rect.top, min(y, rect.bottom - self.pool_height))

                self.root.geometry(
                    f"{self.pool_width}x{self.pool_height}+{x}+{y}"
                )
                return

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        left, top, right, bottom = self._get_work_area()
        taskbar_height = max(0, sh - bottom)

        if self.pool_height <= taskbar_height and taskbar_height > 0:
            y = bottom + (taskbar_height - self.pool_height) // 2
        else:
            y = max(0, bottom - self.pool_height)

        x = left + self.taskbar_left_offset
        x = max(left, min(x, sw - self.pool_width))

        self.root.geometry(f"{self.pool_width}x{self.pool_height}+{x}+{y}")

    def dock_bottom_left(self):
        sw = self.root.winfo_screenwidth()
        left, top, right, bottom = self._get_work_area()
        x = max(0, left)
        y = max(0, bottom - self.pool_height)
        x = max(0, min(x, sw - self.pool_width))
        self.root.geometry(f"{self.pool_width}x{self.pool_height}+{x}+{y}")

    def dock_to_taskbar(self):
        self._apply_taskbar_mode()

    def emergency_reset(self, event=None):
        if self.is_furious:
            self.exit_furious()
            self.trigger_rest(dock=True)
            return
        self.reset_timer(dock=True)
        self.destroy_overlay()

    def reset_timer(self, dock=False):
        self.start_time = time.time()
        self.state = "CUTE"
        self.angry_start_time = 0
        self.exit_furious()
        self.clear_snooze()
        self.destroy_overlay()
        if dock:
            self.dock_bottom_left()

    def trigger_rest(self, dock=False):
        self.state = "RESTING"
        self.rest_start_time = time.time()
        self.angry_start_time = 0
        self.exit_furious()
        self.clear_snooze()
        self.destroy_overlay()
        if dock:
            self.dock_bottom_left()

    def clear_snooze(self):
        self.snooze_until = 0
        self.snooze_started = 0

    def snooze_now(self):
        duration = self.snooze_minutes * 60
        self.start_snooze(duration)

    def start_snooze(self, duration):
        if duration <= 0:
            return
        now = time.time()
        self.snooze_started = now
        self.snooze_until = now + duration
        self.state = "SNOOZE"
        self.destroy_overlay()

    def _shift_timers(self, delta):
        if delta <= 0:
            return
        if self.state == "RESTING":
            self.rest_start_time += delta
        else:
            self.start_time += delta
        if self.snooze_until:
            self.snooze_started += delta
            self.snooze_until += delta

    def set_meeting_mode(self, enabled):
        enabled = bool(enabled)
        if enabled == self.meeting_mode:
            return
        if enabled:
            self.exit_furious()
            self.meeting_mode = True
            self.meeting_started = time.time()
            self.state = "MEETING"
            self.destroy_overlay()
        else:
            paused = 0
            if self.meeting_started:
                paused = time.time() - self.meeting_started
            self.meeting_mode = False
            self.meeting_started = 0
            self._shift_timers(paused)

        if hasattr(self, "meeting_mode_var"):
            self.meeting_mode_var.set(self.meeting_mode)

    def toggle_meeting(self):
        self.set_meeting_mode(not self.meeting_mode)

    def enter_furious(self):
        if self.is_furious:
            return
        self.is_furious = True
        self.state = "FURIOUS"
        self.prev_geometry = self.root.geometry()
        self.prev_pool = (self.pool_width, self.pool_height)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.pool_width = sw
        self.pool_height = sh
        self.canvas.config(width=sw, height=sh)
        self.root.geometry(f"{sw}x{sh}+0+0")
        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        try:
            self.root.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

        self.canvas.configure(bg=FURIOUS_BG)
        self.root.configure(bg=FURIOUS_BG)
        self._bg_size = None
        self.swim_x = sw * 0.2
        self.swim_y = sh * 0.3
        self.furious_vx = 12
        self.furious_vy = 8
        try:
            self.root.grab_set()
            self.root.focus_force()
        except tk.TclError:
            pass

    def exit_furious(self):
        if not self.is_furious:
            return
        self.is_furious = False
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
        try:
            self.root.attributes("-fullscreen", False)
        except tk.TclError:
            pass

        if self.prev_pool:
            self.pool_width, self.pool_height = self.prev_pool
            self.canvas.config(width=self.pool_width, height=self.pool_height)
        if self.prev_geometry:
            self.root.geometry(self.prev_geometry)

        self.canvas.configure(bg=self.bg_color)
        self.root.configure(bg=self.bg_color)
        self._bg_size = None
        try:
            self.root.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

    def destroy_overlay(self):
        if self.overlay is not None:
            try:
                self.overlay.destroy()
            except tk.TclError:
                pass
            self.overlay = None

    def manage_overlay(self):
        if not self._running:
            return
        if self.meeting_mode or self.state == "MEETING" or self.state != "ANGRY":
            self.destroy_overlay()
            return

        if self.overlay is not None:
            return

        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.6 if self.strict_mode else 0.3)
        self.overlay.configure(bg="black" if self.strict_mode else "#2B0B3D")
        self.overlay.attributes("-topmost", True)
        self.overlay.overrideredirect(True)
        self.overlay.bind("<Escape>", self.emergency_reset)

        label = tk.Label(
            self.overlay,
            text="REST YOUR EYES!",
            font=("Arial", 34, "bold"),
            fg="white",
            bg=self.overlay["bg"],
        )
        label.place(relx=0.5, rely=0.85, anchor="center")

        self.root.lift()

    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["is_dragging"] = False

    def on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        if abs(dx) + abs(dy) > 2:
            self._drag_data["is_dragging"] = True
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def on_drag_release(self, event):
        if not self._drag_data["is_dragging"]:
            self.on_click()

    def on_click(self, event=None):
        if self.meeting_mode:
            return
        if self.state in ["WARNING", "ANGRY"]:
            self.trigger_rest()
        elif self.state == "FURIOUS":
            return
        else:
            cx, cy = self.last_shark_pos
            self.spawn_particle(cx, cy - 8, "heart")

    def update_state(self):
        current_time = time.time()
        if self.meeting_mode:
            self.state = "MEETING"
            return
        if self.is_furious:
            self.state = "FURIOUS"
            return
        if self.snooze_until:
            if current_time < self.snooze_until:
                self.state = "SNOOZE"
                return
            paused = max(0, self.snooze_until - self.snooze_started)
            self.start_time += paused
            self.clear_snooze()
        if self.state != "RESTING":
            elapsed = current_time - self.start_time
            if elapsed < self.work_time:
                self.state = "CUTE"
                self.angry_start_time = 0
            elif elapsed < self.work_time + self.warning_duration:
                self.state = "WARNING"
                self.angry_start_time = 0
            else:
                self.state = "ANGRY"
                if not self.angry_start_time:
                    self.angry_start_time = current_time
                if current_time - self.angry_start_time >= self.furious_delay:
                    self.enter_furious()
                    return
        else:
            if current_time - self.rest_start_time > self.rest_time:
                self.reset_timer()

    def get_status_message(self):
        now = time.time()
        if self.state == "MEETING":
            return "Meeting mode", "#90A4AE"
        if self.state == "FURIOUS":
            return "REST NOW!", "#FFCDD2"
        if self.state == "SNOOZE":
            remaining = max(0, int(self.snooze_until - now))
            return f"Snoozed {remaining}s", "#B3E5FC"
        if self.state == "RESTING":
            remaining = max(0, int(self.rest_time - (now - self.rest_start_time)))
            return f"Resting {remaining}s", "#66BB6A"
        if self.state == "CUTE":
            remaining = max(0, int(self.work_time - (now - self.start_time)))
            return f"{remaining}s until break", "#E3F2FD"
        if self.state == "WARNING":
            return "Time to rest", "#FFA000"
        return "Rest now", "#FF5252"

    def get_eye_pos(self, eye_cx, eye_cy, max_radius):
        if self.low_motion:
            return eye_cx, eye_cy
        try:
            mx, my = self.root.winfo_pointerxy()
            wx, wy = self.root.winfo_rootx(), self.root.winfo_rooty()
            mx -= wx
            my -= wy
        except Exception:
            mx, my = eye_cx, eye_cy

        dx = mx - eye_cx
        dy = my - eye_cy
        dist = math.sqrt(dx * dx + dy * dy)

        if dist == 0:
            return eye_cx, eye_cy
        move = min(dist, max_radius)
        angle = math.atan2(dy, dx)
        return eye_cx + math.cos(angle) * move, eye_cy + math.sin(angle) * move

    def spawn_particle(self, x, y, p_type):
        if self.low_motion:
            return
        self.particles.append(
            {
                "x": x,
                "y": y,
                "life": 30,
                "type": p_type,
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(0.6, 1.4),
            }
        )

    def update_swim(self, body_w):
        margin = body_w / 2 + 8
        if self.state == "ANGRY":
            target = self.pool_width / 2
            self.swim_x += (target - self.swim_x) * 0.08
        else:
            speed = self.swim_speed * (0.6 if self.low_motion else 1.0)
            self.swim_x += self.swim_dir * speed
            if self.swim_x > self.pool_width - margin:
                self.swim_x = self.pool_width - margin
                self.swim_dir = -1
            elif self.swim_x < margin:
                self.swim_x = margin
                self.swim_dir = 1

        self.facing = 1 if self.swim_dir >= 0 else -1

    def update_furious_swim(self, body_w, body_h):
        margin_x = body_w / 2 + 8
        margin_y = body_h / 2 + 8
        try:
            mx, my = self.root.winfo_pointerxy()
        except tk.TclError:
            mx, my = self.pool_width / 2, self.pool_height / 2

        mx = max(margin_x, min(mx, self.pool_width - margin_x))
        my = max(margin_y, min(my, self.pool_height - margin_y))

        dx = mx - self.swim_x
        dy = my - self.swim_y
        dist = math.hypot(dx, dy)
        speed = 18
        if dist > 0:
            vx = (dx / dist) * speed
            vy = (dy / dist) * speed
            self.swim_x += vx
            self.swim_y += vy

        self.facing = 1 if dx >= 0 else -1

    def draw_background(self):
        w = self.pool_width
        h = self.pool_height
        self.canvas.create_rectangle(0, 0, w, h, fill="#0B2D4A", outline="", tags="bg")
        self.canvas.create_rectangle(
            0, h * 0.6, w, h, fill="#081F33", outline="", tags="bg"
        )
        wave_y = h * 0.6
        for x in range(0, int(w) + 40, 40):
            self.canvas.create_arc(
                x,
                wave_y - 6,
                x + 40,
                wave_y + 6,
                start=0,
                extent=180,
                style=tk.ARC,
                outline="#1B5E8A",
                tags="bg",
            )

    def draw_outfit(self, cx, cy, bw, bh, facing):
        outfit = self.outfits[self.current_outfit_index]
        if outfit == "None":
            return

        fx = facing
        unit = max(4.0, bh * 0.12)

        if outfit == "Tie":
            tx = cx + fx * (bw * 0.05)
            ty = cy + bh * 0.1
            self.canvas.create_polygon(
                tx,
                ty,
                tx - unit * 0.6,
                ty + unit * 1.4,
                tx,
                ty + unit * 2.0,
                tx + unit * 0.6,
                ty + unit * 1.4,
                fill="#E53935",
                outline="black",
                tags="dynamic",
            )
            self.canvas.create_oval(
                tx - unit * 0.4,
                ty - unit * 0.4,
                tx + unit * 0.4,
                ty + unit * 0.4,
                fill="#E53935",
                outline="black",
                tags="dynamic",
            )
        elif outfit == "Top Hat":
            hx = cx + fx * (bw * 0.2)
            hy = cy - bh * 0.7
            self.canvas.create_rectangle(
                hx - unit * 2.0,
                hy,
                hx + unit * 2.0,
                hy + unit * 0.5,
                fill="#212121",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_rectangle(
                hx - unit * 1.4,
                hy - unit * 2.0,
                hx + unit * 1.4,
                hy,
                fill="#212121",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_rectangle(
                hx - unit * 1.4,
                hy - unit * 0.5,
                hx + unit * 1.4,
                hy,
                fill="#C62828",
                outline="",
                tags="dynamic",
            )
        elif outfit == "Sunglasses":
            ex = cx + fx * (bw * 0.25)
            ey = cy - bh * 0.12
            self.canvas.create_rectangle(
                ex - unit * 1.4,
                ey - unit * 0.6,
                ex + unit * 1.4,
                ey + unit * 0.6,
                fill="black",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_line(
                ex - unit * 1.4,
                ey,
                ex + unit * 1.4,
                ey,
                width=2,
                fill="#444444",
                tags="dynamic",
            )
        elif outfit == "Mohawk":
            hx = cx + fx * (bw * 0.05)
            hy = cy - bh * 0.55
            self.canvas.create_polygon(
                hx - unit * 1.4,
                hy,
                hx,
                hy - unit * 1.6,
                hx + unit * 1.4,
                hy,
                fill="#00C853",
                outline="black",
                tags="dynamic",
            )
        elif outfit == "Beanie":
            hx = cx + fx * (bw * 0.12)
            hy = cy - bh * 0.62
            cap_w = unit * 2.6
            cap_h = unit * 1.8
            self.canvas.create_arc(
                hx - cap_w,
                hy - cap_h,
                hx + cap_w,
                hy + cap_h,
                start=0,
                extent=180,
                fill="#EF5350",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_rectangle(
                hx - cap_w,
                hy,
                hx + cap_w,
                hy + unit * 0.5,
                fill="#C62828",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_oval(
                hx - unit * 0.4,
                hy - cap_h - unit * 0.4,
                hx + unit * 0.4,
                hy - cap_h + unit * 0.4,
                fill="#FFCDD2",
                outline="",
                tags="dynamic",
            )
        elif outfit == "Crown":
            hx = cx + fx * (bw * 0.12)
            hy = cy - bh * 0.7
            crown_w = unit * 2.4
            crown_h = unit * 1.4
            self.canvas.create_polygon(
                hx - crown_w,
                hy + crown_h,
                hx - crown_w * 0.6,
                hy,
                hx,
                hy + crown_h * 0.3,
                hx + crown_w * 0.6,
                hy,
                hx + crown_w,
                hy + crown_h,
                fill="#FDD835",
                outline="black",
                tags="dynamic",
            )
            self.canvas.create_oval(
                hx - unit * 0.3,
                hy - unit * 0.2,
                hx + unit * 0.3,
                hy + unit * 0.4,
                fill="#FF7043",
                outline="",
                tags="dynamic",
            )
        elif outfit == "Headphones":
            hx = cx + fx * (bw * 0.05)
            hy = cy - bh * 0.62
            band_w = unit * 2.6
            band_h = unit * 2.0
            self.canvas.create_arc(
                hx - band_w,
                hy - band_h,
                hx + band_w,
                hy + band_h,
                start=200,
                extent=140,
                style=tk.ARC,
                outline="#37474F",
                width=3,
                tags="dynamic",
            )
            pad_w = unit * 0.8
            pad_h = unit * 1.1
            self.canvas.create_rectangle(
                hx - band_w * 0.95 - pad_w,
                hy + pad_h * 0.2,
                hx - band_w * 0.95 + pad_w,
                hy + pad_h * 1.8,
                fill="#546E7A",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_rectangle(
                hx + band_w * 0.95 - pad_w,
                hy + pad_h * 0.2,
                hx + band_w * 0.95 + pad_w,
                hy + pad_h * 1.8,
                fill="#546E7A",
                outline="",
                tags="dynamic",
            )
        elif outfit == "Scarf":
            sx = cx + fx * (bw * 0.05)
            sy = cy + bh * 0.18
            scarf_w = unit * 2.0
            scarf_h = unit * 0.6
            self.canvas.create_rectangle(
                sx - scarf_w,
                sy - scarf_h,
                sx + scarf_w,
                sy + scarf_h,
                fill="#FFB74D",
                outline="black",
                tags="dynamic",
            )
            tail_dir = -fx
            self.canvas.create_rectangle(
                sx + tail_dir * scarf_w * 0.2,
                sy + scarf_h,
                sx + tail_dir * scarf_w * 0.8,
                sy + scarf_h + unit * 1.6,
                fill="#FFB74D",
                outline="black",
                tags="dynamic",
            )

    def draw_particles(self):
        if self.low_motion:
            self.particles = []
            return
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] -= p["vy"]
            p["life"] -= 1

            if p["type"] == "heart":
                self.canvas.create_text(
                    p["x"],
                    p["y"],
                    text="<3",
                    fill="#FF4F79",
                    font=("Arial", 10, "bold"),
                    tags="particle",
                )
            elif p["type"] == "steam":
                self.canvas.create_oval(
                    p["x"],
                    p["y"],
                    p["x"] + 8,
                    p["y"] + 8,
                    fill="#B0BEC5",
                    outline="",
                    tags="particle",
                )
            elif p["type"] == "bubble":
                self.canvas.create_oval(
                    p["x"],
                    p["y"],
                    p["x"] + 6,
                    p["y"] + 6,
                    outline="#90CAF9",
                    tags="particle",
                )

        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw_shark(self, cx, cy, size, body_w, body_h):
        self.canvas.delete("all")

        smooth_edges = not self.low_motion
        if self.low_motion:
            breath_speed = 0.05
            breath_amp_y = 0.02
            breath_amp_x = 0.015
        else:
            if self.state == "FURIOUS":
                breath_speed = 0.35
                breath_amp_y = 0.05
                breath_amp_x = 0.04
            else:
                breath_speed = 0.08 if self.state != "ANGRY" else 0.25
                breath_amp_y = 0.04
                breath_amp_x = 0.03
        breath = math.sin(self.tick_count * breath_speed)
        scale_y = 1.0 + (breath * breath_amp_y)
        scale_x = 1.0 - (breath * breath_amp_x)
        bw = body_w * scale_x
        bh = body_h * scale_y
        fx = self.facing

        if self.state in ["ANGRY", "FURIOUS"]:
            skin_color = "#5E2B7A"
            belly_color = "#8E44AD"
            eye_bg = "#FFCDD2"
            accent = "#FF7043"
            highlight = "#7B4A9E"
        elif self.state == "WARNING":
            skin_color = "#3498DB"
            belly_color = "#B3E5FC"
            eye_bg = "white"
            accent = "#FFA000"
            highlight = "#81D4FA"
        else:
            skin_color = "#6ED6FF"
            belly_color = "#EAF7FF"
            eye_bg = "white"
            accent = "#64B5F6"
            highlight = "#B3E5FC"

        shadow = "#1E4D6D"

        tail_base_x = cx - fx * (bw / 2)
        tail_tip_x = tail_base_x - fx * (bw * 0.35)
        tail_wag = 0 if self.low_motion else math.sin(self.tick_count * 0.2) * (bh * 0.08)
        self.canvas.create_polygon(
            tail_base_x,
            cy,
            tail_tip_x,
            cy - bh * 0.25 + tail_wag,
            tail_tip_x,
            cy + bh * 0.25 + tail_wag,
            fill=skin_color,
            outline="",
            smooth=smooth_edges,
            tags="dynamic",
        )

        fin_base_x = cx - fx * (bw * 0.05)
        self.canvas.create_polygon(
            fin_base_x,
            cy - bh * 0.35,
            fin_base_x + fx * (bw * 0.12),
            cy - bh * 0.75,
            fin_base_x + fx * (bw * 0.3),
            cy - bh * 0.25,
            fill=skin_color,
            outline="",
            smooth=smooth_edges,
            tags="dynamic",
        )

        self.canvas.create_oval(
            cx - bw / 2,
            cy - bh / 2,
            cx + bw / 2,
            cy + bh / 2,
            fill=skin_color,
            outline="",
            tags="dynamic",
        )

        belly_offset = fx * (bw * 0.12)
        self.canvas.create_oval(
            cx - bw * 0.2 + belly_offset,
            cy,
            cx + bw * 0.35 + belly_offset,
            cy + bh * 0.35,
            fill=belly_color,
            outline="",
            tags="dynamic",
        )

        if not self.low_motion:
            self.canvas.create_oval(
                cx - bw * 0.05 + belly_offset,
                cy - bh * 0.45,
                cx + bw * 0.4 + belly_offset,
                cy - bh * 0.05,
                fill=highlight,
                outline="",
                tags="dynamic",
            )

        fin2_x = cx - fx * (bw * 0.08)
        self.canvas.create_polygon(
            fin2_x,
            cy + bh * 0.05,
            fin2_x + fx * (bw * 0.18),
            cy + bh * 0.2,
            fin2_x + fx * (bw * 0.12),
            cy + bh * 0.35,
            fill=shadow,
            outline="",
            smooth=smooth_edges,
            tags="dynamic",
        )

        if not self.low_motion:
            gill_x = cx + fx * (bw * 0.08)
            for i in range(3):
                y = cy - bh * 0.1 + i * (bh * 0.12)
                self.canvas.create_line(
                    gill_x,
                    y,
                    gill_x + fx * (bw * 0.08),
                    y + bh * 0.02,
                    fill=shadow,
                    width=2,
                    tags="dynamic",
                )

        nose_x = cx + fx * (bw * 0.48)
        nose_y = cy - bh * 0.05
        self.canvas.create_oval(
            nose_x - bw * 0.06,
            nose_y - bh * 0.06,
            nose_x + bw * 0.06,
            nose_y + bh * 0.06,
            fill=skin_color,
            outline="",
            tags="dynamic",
        )

        if self.outfits[self.current_outfit_index] in ["Tie", "Scarf"]:
            self.draw_outfit(cx, cy, bw, bh, fx)

        eye_x = cx + fx * (bw * 0.25)
        eye_y = cy - bh * 0.12
        eye_r = bh * 0.14

        if self.low_motion:
            self.is_blinking = False
            self.blink_timer = 0
        elif self.state != "ANGRY" and random.randint(0, 100) > 98:
            self.is_blinking = True
        if self.is_blinking:
            self.blink_timer += 1
            if self.blink_timer > 6:
                self.is_blinking = False
                self.blink_timer = 0
            self.canvas.create_line(
                eye_x - eye_r,
                eye_y,
                eye_x + eye_r,
                eye_y,
                width=2,
                fill="black",
                tags="dynamic",
            )
        else:
            if self.state == "ANGRY":
                self.canvas.create_polygon(
                    eye_x - eye_r,
                    eye_y - eye_r,
                    eye_x + eye_r,
                    eye_y - eye_r * 0.3,
                    eye_x + eye_r * 0.2,
                    eye_y + eye_r,
                    fill=eye_bg,
                    outline="",
                    tags="dynamic",
                )
            else:
                self.canvas.create_oval(
                    eye_x - eye_r,
                    eye_y - eye_r,
                    eye_x + eye_r,
                    eye_y + eye_r,
                    fill=eye_bg,
                    outline="",
                    tags="dynamic",
                )

            px, py = self.get_eye_pos(eye_x, eye_y, eye_r * 0.4)
            pupil_r = eye_r * 0.45
            self.canvas.create_oval(
                px - pupil_r,
                py - pupil_r,
                px + pupil_r,
                py + pupil_r,
                fill="black",
                outline="",
                tags="dynamic",
            )
            self.canvas.create_oval(
                px - pupil_r * 0.4,
                py - pupil_r * 0.4,
                px - pupil_r * 0.1,
                py - pupil_r * 0.1,
                fill="white",
                outline="",
                tags="dynamic",
            )

        if not self.low_motion:
            if self.state == "ANGRY":
                self.canvas.create_line(
                    eye_x - eye_r * 1.1,
                    eye_y - eye_r * 1.1,
                    eye_x + eye_r * 1.1,
                    eye_y - eye_r * 1.4,
                    width=3,
                    fill=accent,
                    tags="dynamic",
                )
            else:
                cheek_r = eye_r * 0.35
                self.canvas.create_oval(
                    eye_x - eye_r * 1.8,
                    eye_y + eye_r * 0.6,
                    eye_x - eye_r * 1.8 + cheek_r * 2,
                    eye_y + eye_r * 0.6 + cheek_r * 2,
                    fill="#F8BBD0",
                    outline="",
                    tags="dynamic",
                )

        if self.outfits[self.current_outfit_index] in [
            "Top Hat",
            "Sunglasses",
            "Mohawk",
            "Beanie",
            "Crown",
            "Headphones",
        ]:
            self.draw_outfit(cx, cy, bw, bh, fx)

        mouth_x = cx + fx * (bw * 0.38)
        mouth_y = cy + bh * 0.05
        if self.state == "FURIOUS":
            jaw_w = bw * 0.2
            jaw_h = bh * 0.2
            left = mouth_x - jaw_w
            right = mouth_x + jaw_w
            top = mouth_y - jaw_h * 0.4
            bottom = mouth_y + jaw_h * 0.9
            self.canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                fill="#1A1A1A",
                outline="black",
                tags="dynamic",
            )
            tooth_count = 6
            step = (right - left) / tooth_count
            for i in range(tooth_count):
                tx = left + i * step
                self.canvas.create_polygon(
                    tx,
                    top,
                    tx + step * 0.5,
                    top + jaw_h * 0.35,
                    tx + step,
                    top,
                    fill="white",
                    outline="black",
                    tags="dynamic",
                )
                self.canvas.create_polygon(
                    tx,
                    bottom,
                    tx + step * 0.5,
                    bottom - jaw_h * 0.35,
                    tx + step,
                    bottom,
                    fill="white",
                    outline="black",
                    tags="dynamic",
                )
        elif self.state == "ANGRY":
            mw = bw * 0.14
            mh = bh * 0.12
            left = mouth_x - mw
            right = mouth_x + mw
            self.canvas.create_polygon(
                left,
                mouth_y,
                left + mw * 0.25,
                mouth_y + mh,
                left + mw * 0.5,
                mouth_y,
                left + mw * 0.75,
                mouth_y + mh,
                right,
                mouth_y,
                right,
                mouth_y + mh,
                left,
                mouth_y + mh,
                fill="white",
                outline="black",
                tags="dynamic",
            )
        else:
            self.canvas.create_line(
                mouth_x - bw * 0.08,
                mouth_y,
                mouth_x,
                mouth_y + bh * 0.06,
                mouth_x + bw * 0.08,
                mouth_y,
                smooth=True,
                width=2,
                fill="black",
                tags="dynamic",
            )

        if self.state == "ANGRY" and self.tick_count % 12 == 0:
            self.spawn_particle(
                cx + random.randint(-10, 10),
                cy - bh * 0.25,
                "steam",
            )
        elif self.state in ["CUTE", "SNOOZE"] and self.tick_count % 25 == 0:
            self.spawn_particle(
                cx - bw * 0.2,
                cy - bh * 0.1,
                "bubble",
            )

        msg, color = self.get_status_message()
        text_y = max(12, self.pool_height - 12)
        self.canvas.create_text(
            self.pool_width / 2,
            text_y,
            text=msg,
            font=("Verdana", 9, "bold"),
            fill=color,
            tags="dynamic",
        )

        self.draw_particles()
        self.last_shark_pos = (cx, cy)

    def animate(self):
        if not self._running:
            return
        try:
            self.tick_count += 1
            self.update_state()

            if self.meeting_mode:
                self.canvas.delete("all")
                self.root.after(self.frame_delay_ms, self.animate)
                return

            size = min(self.pool_height * 0.9, self.pool_width * 0.28)
            size = max(36, size)
            scale = max(0.2, min(self.shark_scale, 2.5))
            size *= scale
            body_w = size * 1.6
            body_h = size * 0.9

            if self.state == "FURIOUS":
                self.update_furious_swim(body_w, body_h)
                cx = self.swim_x
                cy = self.swim_y
            else:
                self.update_swim(body_w)

                swim_y_base = self.pool_height * 0.55
                if self.low_motion:
                    swim_bob = 0
                else:
                    swim_bob = math.sin(self.tick_count * 0.15) * (
                        self.pool_height * 0.06
                    )
                cx = self.swim_x
                cy = swim_y_base + swim_bob

                if self.state == "ANGRY" and not self.low_motion:
                    cx += random.randint(-2, 2)
                    cy += random.randint(-2, 2)

            self.draw_shark(cx, cy, size, body_w, body_h)

            msg, _ = self.get_status_message()
            self.status_var.set(f"State: {self.state}")
            self.remaining_var.set(msg)

            self.root.after(self.frame_delay_ms, self.animate)
        except tk.TclError:
            self._running = False


if __name__ == "__main__":
    WakeySharkApp()
