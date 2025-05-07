from tkinter import Label, ttk, Entry, Frame, StringVar, IntVar, Canvas, PhotoImage, Text, Toplevel, TclError, \
    Button, TclError
from custom_widgets import HelpButton, RoundCornerButton, RoundCornerButtonGR, ImageDescriptionWindow, \
    NoteButton, PowerPointWindow
from win32api import GetMonitorInfo, MonitorFromPoint, PostMessage
from win32con import HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST
from matplots import BasicMatplot, BasicScatter, SpectrumPlot, DynamicScatterPlot
from paned_window import VerticalPanedWindow
from scrolled_text import ScrolledText
from typing import Callable, Optional
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import customtkinter as ctk
from tksheet import Sheet
import tkinter as tk
import ctypes
import psutil
import sys
import os
import gc

VERSION = "v2025-05-07"
GUI_THEME = "itft1"
GREEN = '#68CC64'


class MainGUI(ThemedTk):
    def __init__(self, theme=GUI_THEME):
        super().__init__()
        self['theme'] = theme
        self.title('FAQ Guide - {}'.format(VERSION))
        self.iconphoto(True, PhotoImage(file='images/logo_ico.png'))
        # self.protocol("wm_iconbitmap", 'logo.ico')
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # self.root.call('tk', 'scaling', 3.3)
        self.__bindings()
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        work_area = monitor_info.get("Work")
        self.win_h = work_area[3]  # working area height of the screen
        self.win_w = work_area[2]  # working area width of the screen
        self.geometry("{}x{}+{}+{}".format(self.win_w, self.win_h, -10, 0))
        self.state('zoomed')
        self._on_close_callback = None

        """ Region Frames """
        top_frame_h = 150
        self.tf = _TopFrame(self, height=top_frame_h, width=self.win_w, bg="#b9d1ea")
        self.tf.pack(side="top", fill="x")

        left_frame_h = self.win_h - top_frame_h
        left_frame_w = 300
        self.lf = _LeftFrame(self, height=left_frame_h, width=left_frame_w, bg="#d8e4f4")
        self.lf.pack(side="left", fill="y")

        main_frame_h = self.win_h - top_frame_h
        sash_image_horizon = PhotoImage(
            data="R0lGODlhGAADAPIFAEBAQGBgYICAgLu7u8zMzAAAAAAAAAAAACH5BAEA"
                 "AAUALAAAAAAYAAMAAAMaWBJQym61N2UZJTisb96fpxGD4JBmgZ4lKyQAOw==")
        self.panedwindow = VerticalPanedWindow(self, image=sash_image_horizon)
        self.mf = _MainFrame(self.panedwindow, height=main_frame_h, width=self.win_w - left_frame_w)
        self.cmd_f = _CommandFrame(self.panedwindow)
        self.panedwindow.add(self.mf, stretch="always")
        self.panedwindow.add(self.cmd_f, stretch="always")
        self.panedwindow.pack(fill="both", expand=True)

    def __bindings(self):
        self.bind("<Escape>", lambda x: self.on_close())

    def set_device_type(self, dev_type: str):
        if len(dev_type) > 0:
            self.title('FAQ Guide       Device Type: ' + dev_type + '       ' + VERSION)
        else:
            self.title('FAQ Guide')

    def set_on_close_callback(self, cmd):
        self._on_close_callback = cmd

    def on_close(self):
        if self._on_close_callback is not None:
            self._on_close_callback()
        try:
            self.destroy()
        except TclError:
            self.destroy()
        sys.exit()


class _TopFrame(Frame):
    class OutputSignalFrame(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.output_signal_label = Label(self, text='Output Signal:', bg="#b9d1ea")
            self.output_signal_label.pack(padx=5, side='left')
            self.output_signal_entry = Entry(self, width=30)
            self.output_signal_entry.pack(padx=3, side='left')
            self.output_signal_entry.bind('<Return>', lambda x: self._entry_command())
            self._entry_callback = None
            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.pack(pady=2, side='right')

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='Signal ID Summery', close_command=self._help_button.enable,
                             image_dir_en='images/signal ID table/en', image_dir_cn='images/signal ID table/cn')

        def set_entry_callback(self, cmd):
            self._entry_callback = cmd

        def clear_entry_callback(self):
            self._entry_callback = None

        def _entry_command(self):
            if self._entry_callback:
                self._entry_callback()

        def set_output_signal(self, val: str):
            self.output_signal_entry.delete(0, 'end')
            self.output_signal_entry.insert('end', val)

        def get_output_signal(self):
            return self.output_signal_entry.get()

    class SampleRateLEDFrame(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            first_r_f = Frame(self, bg="#b9d1ea")
            first_r_f.pack(side='top', anchor='w')
            self.sample_rate_label = Label(first_r_f, text='Sample Rate:', bg=first_r_f['bg'])
            self.sample_rate_label.grid(column=0, row=0, sticky='NW')
            self._sample_rate_entry = Entry(first_r_f, width=15)
            self._sample_rate_entry.bind('<Return>', lambda x: self._shz_entry_command())
            self._sample_rate_entry.grid(column=1, row=0, padx=3, sticky='NW')
            second_r_f = Frame(self, bg="#b9d1ea")
            second_r_f.pack(side='top', anchor='w')
            self.led_label = Label(second_r_f, text='LED(%):', bg=second_r_f['bg'])
            self.led_label.grid(column=0, row=1, sticky='NW')
            self._led_entry = Entry(second_r_f, width=15)
            self._led_entry.bind('<Return>', lambda x: self._lai_entry_command())
            self._led_entry.grid(column=1, row=1, padx=30, sticky='NW')
            self._shz_entry_callback = None
            self._lai_entry_callback = None

        def _shz_entry_command(self):
            if self._shz_entry_callback:
                self._shz_entry_callback()

        def _lai_entry_command(self):
            if self._lai_entry_callback:
                self._lai_entry_callback()

        def set_tf_sample_rate(self, val):
            self._sample_rate_entry.delete(0, 'end')
            self._sample_rate_entry.insert('end', val)

        def get_tf_sample_rate(self) -> str:
            return self._sample_rate_entry.get()

        def clear_tf_sample_rate(self):
            self._sample_rate_entry.delete(0, 'end')

        def set_tf_led(self, val):
            self._led_entry.delete(0, 'end')
            self._led_entry.insert('end', val)

        def get_tf_led(self) -> str:
            return self._led_entry.get()

        def clear_tf_led(self):
            self._led_entry.delete(0, 'end')

        def set_shz_entry_callback(self, cmd):
            self._shz_entry_callback = cmd

        def clear_shz_entry_callback(self):
            self._shz_entry_callback = None

        def set_lai_entry_callback(self, cmd):
            self._lai_entry_callback = cmd

        def clear_lai_entry_callback(self):
            self._lai_entry_callback = None

    class ThresholdFrame(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.threshold_label = Label(self, text='Threshold:', bg='#b9d1ea')
            self.threshold_label.pack(side='left')
            self._threshold_entry = Entry(self, width=10)
            self._threshold_entry.bind('<Return>', lambda x: self._entry_command())
            self._threshold_entry.pack(padx=3, side='right')
            self._entry_callback = None

        def set_entry_callback(self, cmd):
            self._entry_callback = cmd

        def clear_entry_callback(self):
            self._entry_callback = None

        def _entry_command(self):
            if self._entry_callback:
                self._entry_callback()

        def set_threshold(self, val):
            self._threshold_entry.delete(0, 'end')
            self._threshold_entry.insert('end', val)

        def get_threshold(self):
            return self._threshold_entry.get()

        def clear_threshold(self):
            self._threshold_entry.delete(0, 'end')

    class ConnTypeFrame(Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._label_f = ttk.LabelFrame(self, text='DLL: Connection Type ')
            self._label_f.grid(column=0, row=0)
            background = Canvas(self._label_f, width=180, height=80)
            background.grid(column=0, row=0, rowspan=2, sticky='nswe')

            img = Image.open('images/sync_async.png')
            self._conn_type_img = ImageTk.PhotoImage(img)
            self._img_size = img.size
            self.help_button = HelpButton(master=self, command=self._help)
            self.help_button.grid(column=0, row=0, sticky='en')

            options = (('Synchronous Mode', 0),
                       ('Asynchronous Mode', 1))
            s = ttk.Style()
            s.configure('Wild.TRadiobutton', background='SystemButtonFace')
            self._selected_option = StringVar()
            for index, option in enumerate(options):
                r = ttk.Radiobutton(self._label_f, text=option[0], value=option[1], variable=self._selected_option,
                                    style='Wild.TRadiobutton', takefocus=False)
                r.grid(column=0, row=index, padx=10, sticky='w')
            self.set_conn_value(0)

        def _help(self):
            self.help_button.disable()
            ImageDescriptionWindow(master=self, image_en=self._conn_type_img, title='Connection Type',
                                   size=[self._img_size[0], self._img_size[1]],
                                   close_command=self.help_button.enable)

        def get_conn_value(self):
            return self._selected_option.get()

        def set_conn_value(self, val):
            self._selected_option.set(val)

    class DevMeasModeFrame(ttk.LabelFrame):
        def __init__(self, *args, **kwargs):
            self._selected_option = IntVar()
            self._selected_buffer = IntVar()
            super().__init__(*args, **kwargs)
            self.CTN = 0
            self.TRG = 1
            self.TRE = 2
            options = (('Continue Mode (CTN)', self.CTN),
                       ('Wait for Trigger (TRG)', self.TRG),
                       ('Trigger Each (TRE)', self.TRE))

            background = Canvas(self, width=200, height=80)
            background.grid(column=0, row=0, rowspan=3, sticky='nswe')

            s = ttk.Style()
            s.configure('Wild.TRadiobutton', background='SystemButtonFace')
            for index, option in enumerate(options):
                r = ttk.Radiobutton(self, text=option[0], value=option[1], variable=self._selected_option,
                                    style='Wild.TRadiobutton', takefocus=False, command=self._sel)
                r.grid(column=0, row=index, padx=10, sticky='w')
            self.set_tf_trig_mode_value(self.CTN)
            self._sel_callback = None

        def set_tf_trig_mode_sel_callback(self, cmd):
            self._sel_callback = cmd

        def clear_tf_trig_mode_sel_callback(self):
            self._sel_callback = None

        def get_tf_trig_mode_value(self):
            return self._selected_option.get()

        def set_tf_trig_mode_value(self, val: int):
            self._selected_option.set(val)
            self._selected_buffer.set(val)

        def _sel(self):
            if self._selected_option.get() != self._selected_buffer.get():
                self._selected_buffer.set(self._selected_option.get())
                if self._sel_callback is not None:
                    self._sel_callback()

    class DevDataFlowSwitchFrame(Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Device: Data Flow Switch')
            self.label_frame.grid(column=0, row=0)
            background = Canvas(self.label_frame, width=180, height=80)
            background.grid(column=0, row=0, rowspan=2, sticky='nswe')

            self._selected_option = IntVar()
            self._selected_buffer = IntVar()
            self.STA = 0
            self.STO = 1
            options = (('Start ($STA)', 0),
                       ('Stop ($STO)', 1))

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=0, row=0, sticky='en')

            s = ttk.Style()
            s.configure('Wild.TRadiobutton', background='SystemButtonFace')
            for index, option in enumerate(options):
                r = ttk.Radiobutton(self.label_frame, text=option[0], value=option[1], variable=self._selected_option,
                                    style='Wild.TRadiobutton', takefocus=False, command=self._sel)
                r.grid(column=0, row=index, padx=10, sticky='w')
            self.set_data_flow_option_value(0)
            self._sel_callback = None

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='Data Stream Control', close_command=self._help_button.enable,
                             image_dir_en='images/data flow switch/en', image_dir_cn='images/data flow switch/cn')

        def set_flow_switch_sel_callback(self, cmd):
            self._sel_callback = cmd

        def _sel(self):
            if self._selected_option.get() != self._selected_buffer.get():
                self._selected_buffer.set(self._selected_option.get())
                if self._sel_callback is not None:
                    self._sel_callback()

        def get_data_flow_option_value(self):
            return self._selected_option.get()

        def set_data_flow_option_value(self, val):
            self._selected_option.set(val)
            self._selected_buffer.set(val)

    class DataAcquisitionFrame(Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Data Acquisition')
            self.label_frame.grid(column=0, row=0)

            self.selected_option = StringVar()
            options = (('GetLastSample', 0),
                       ('GetNextSample', 1),
                       ('ActivateAutoBufferMode', 2))

            background = Canvas(self.label_frame, width=180, height=80)
            background.grid(column=0, row=0, rowspan=3, sticky='nswe')

            self.help_button = HelpButton(master=self, command=self._help)
            self.help_button.grid(column=0, row=0, sticky='en')

            s = ttk.Style()
            s.configure('Wild.TRadiobutton', background='SystemButtonFace')
            for index, option in enumerate(options):
                r = ttk.Radiobutton(self.label_frame, text=option[0], value=option[1], variable=self.selected_option,
                                    style='Wild.TRadiobutton', takefocus=False)
                r.grid(column=0, row=index, padx=10, sticky='w')
            self.set_value(0)

        def _help(self):
            self.help_button.disable()
            PowerPointWindow(master=self, title='Data Acquisition', close_command=self.help_button.enable,
                             image_dir_en='images/data_acquisition/')

        def get_value(self):
            return self.selected_option.get()

        def set_value(self, val):
            self.selected_option.set(val)

    class FocusFrame(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Focus')
            self.label_frame.grid(column=0, row=0)
            self.max_value = 32768

            self.help_button = HelpButton(master=self, command=self._help)
            self.help_button.grid(column=0, row=0, sticky='en')

            background = Canvas(self.label_frame, width=230, height=80)
            background.grid(column=0, row=0, columnspan=3, rowspan=3, sticky='nswe')

            distance_label = Label(self.label_frame, text='Distance 1 (id:256)', bg='SystemButtonFace')
            distance_label.grid(column=0, row=0, columnspan=3, sticky='ns')

            second_r_f = Frame(self.label_frame)
            second_r_f.grid(column=0, row=1, columnspan=2, padx=10)
            self.progress_bar = ttk.Progressbar(second_r_f, orient="horizontal", length=150, mode="indeterminate")
            self.progress_bar.grid(column=0, row=0)
            self.distance_value = StringVar()
            Label(second_r_f, textvariable=self.distance_value, bg='SystemButtonFace', anchor='e').grid(column=1, row=0,
                                                                                                        sticky='w')

            too_close_label = Label(self.label_frame, text='too close', bg='SystemButtonFace')
            too_close_label.grid(column=0, row=2, sticky='w')
            too_far_label = Label(self.label_frame, text='too far', bg='SystemButtonFace')
            too_far_label.grid(column=1, row=2, padx=10, sticky='w')

            self._focus_callback = None
            self.init()

        def _help(self):
            self.help_button.disable()
            PowerPointWindow(master=self, title='About Distance', close_command=self.help_button.enable,
                             image_dir_en='images/focus/en', image_dir_cn='images/focus/cn')

        def init(self):
            self.progress_bar['value'] = 0
            self.progress_bar["maximum"] = self.max_value
            self.set_distance_value('     0')

        def set_max(self, val):
            self.progress_bar["maximum"], self.max_value = val, val

        def set_distance_prog_bar_value(self, val):
            self.progress_bar['value'] = val

        def set_distance_value(self, val):
            self.distance_value.set('{}㎛'.format(val))

        def set_focus_callback(self, cmd):
            self._focus_callback = cmd

        def clear_focus_callback(self):
            self._focus_callback = None

        def update_focus(self):
            if self._focus_callback is not None:
                self._focus_callback()
                self.after(10, self.update_focus)

    class IntensityFrame(Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Intensity')
            self.label_frame.grid(column=0, row=0, columnspan=2)

            btn_f = Frame(self)
            btn_f.grid(column=1, row=0, sticky='en')
            self.help_button = HelpButton(master=btn_f, command=self._help)
            self.help_button.grid(column=0, row=0, sticky='en')

            background = Canvas(self.label_frame, width=220, height=80)
            background.grid(column=0, row=0, columnspan=3, rowspan=3, sticky='nswe')

            self.max_value = 4096
            intensity_label = Label(self.label_frame, text='Intensity 1 MSW (id:16641)', bg='SystemButtonFace')
            intensity_label.grid(column=0, row=0, columnspan=3, sticky='ns')

            self.progress_bar = ttk.Progressbar(self.label_frame, orient="horizontal", length=150, mode="indeterminate")
            self.progress_bar.grid(column=0, row=1, columnspan=2, padx=10)
            self.intensity_value = StringVar()
            Label(self.label_frame, textvariable=self.intensity_value, bg='SystemButtonFace',
                  anchor='e').grid(column=2, row=1, sticky='w')

            too_low_label = Label(self.label_frame, text='too low', bg='SystemButtonFace')
            too_low_label.grid(column=0, row=2, sticky='w')
            too_high_label = Label(self.label_frame, text='too high', bg='SystemButtonFace')
            too_high_label.grid(column=1, row=2, sticky='e')
            self.init()

        def _help(self):
            self.help_button.disable()
            PowerPointWindow(master=self, title='Intensity FAQ', close_command=self.help_button.enable,
                             image_dir_en='images/intensity/en', image_dir_cn='images/intensity/cn')

        def init(self):
            self.progress_bar['value'] = 0
            self.progress_bar["maximum"] = self.max_value
            self.set_intensity_value('0')

        def set_max(self, val):
            self.progress_bar["maximum"], self.max_value = val, val

        def set_intensity_prog_bar_value(self, val):
            self.progress_bar['value'] = val

        def set_intensity_value(self, val: str):
            self.intensity_value.set(val)

    class MonitorFrame(ctk.CTkFrame):
        def __init__(self, master, **kwargs):
            super().__init__(master, fg_color="#b9d1ea", border_width=0, **kwargs)
    
            # 建立一個標籤用以顯示記憶體使用量
            self.memory_label = ctk.CTkLabel(self, font=("Calibri", 10), height=15, text_color="black")
            self.memory_label.pack(side=tk.RIGHT)
    
            # 啟動即時更新記憶體使用量的功能
            self.update_memory_usage()
    
        def update_memory_usage(self):
            # 取得目前應用程式的進程
            process = psutil.Process(os.getpid())
            # 取得記憶體使用量，轉換成 MB
            memory_usage = process.memory_info().rss / (1024 * 1024)
            # 更新標籤上的文字
            self.memory_label.configure(text=f"{memory_usage:.1f} MB")
            # 清理系統資源
            gc.collect()
            # 每1000毫秒(1秒)呼叫一次自身進行更新
            self.after(1000, self.update_memory_usage)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # region Logo Frame
        logo_f = Frame(self, bg="#b9d1ea")
        self.logo_img = PhotoImage(file='images/logo.png')
        Label(logo_f, image=self.logo_img).grid(column=0, row=0, padx=5, pady=5, sticky='nwe')
        logo_f.pack(side='left', fill='both')
        # endregion

        # region Right Frame
        right_f = Frame(self, bg="#b9d1ea", highlightbackground="#8e949a", highlightthickness=2)
        right_f.pack(side='left', fill='both', padx=78, pady=2)

        Label(right_f, text=' Status\nMonitor', relief='sunken', anchor='center', height=10, width=8,
              bg='#daeffd').pack(side='left', fill='x', pady=0, ipady=0)
        # endregion

        # region Top Frame
        top_right_f = Frame(right_f, bg="#b9d1ea")
        top_right_f.pack(side='top', fill='both', padx=0, expand=True)
        self.output_signal_f = self.OutputSignalFrame(top_right_f, bg="#b9d1ea")
        self.output_signal_f.grid(column=1, row=0, padx=0, pady=2, sticky='NW')
        self.sample_rate_led_f = self.SampleRateLEDFrame(top_right_f, bg="#b9d1ea")
        self.sample_rate_led_f.grid(column=2, row=0, padx=100, pady=2, sticky='NW')
        self.threshold_f = self.ThresholdFrame(top_right_f, bg='#b9d1ea')
        self.threshold_f.grid(column=3, row=0, sticky='NW', pady=1)
        # endregion

        # region Bottom Frame
        bottom_right_f = Frame(right_f, bg="#b9d1ea")
        bottom_right_f.pack(side='top', fill='both', padx=0)

        self.dll_conn_type_f = self.ConnTypeFrame(bottom_right_f)
        self.dll_conn_type_f.grid(column=0, row=1, padx=5, pady=5, sticky='W')
        self.device_measurement_mode_f = self.DevMeasModeFrame(bottom_right_f,
                                                               text='Device: Measurement Mode')
        self.device_measurement_mode_f.grid(column=3, row=1, sticky='W', padx=5, pady=5)
        self.device_data_flow_switch_f = self.DevDataFlowSwitchFrame(bottom_right_f)
        self.device_data_flow_switch_f.grid(column=4, row=1, sticky='W', padx=5, pady=5)
        self.dll_data_acq_f = self.DataAcquisitionFrame(bottom_right_f)
        self.dll_data_acq_f.grid(column=5, row=1, sticky='W', padx=5, pady=5)
        self.focus_f = self.FocusFrame(bottom_right_f)
        self.focus_f.grid(column=6, row=1, sticky='W', padx=5, pady=5)
        self.intensity_f = self.IntensityFrame(bottom_right_f)
        self.intensity_f.grid(column=7, row=1, sticky='W', padx=5, pady=5)
        # endregion

        # region Monitor
        monitor_frame = self.MonitorFrame(self)
        monitor_frame.pack(side=tk.RIGHT, padx=(0, 5), anchor=tk.N)
        # endregion


class _LeftFrame(Frame):
    class SensorTypeFrame(Frame):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Sensor Type')
            self.label_frame.grid(column=0, row=0, columnspan=2)
            background = Canvas(self.label_frame, width=220, height=80)
            background.grid(column=0, row=0, rowspan=3, sticky='nswe')

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=1, row=0, sticky='en')

            s = ttk.Style()
            s.configure('bg_color.TRadiobutton', background=background['bg'])
            options = (('CLS/CLS2/CLS2Pro/MPS', 0),
                       ('CHR-2S/IT', 1),
                       ('CHR-C/Mini', 2))
            self.selected_option = StringVar()
            for index, option in enumerate(options):
                r = ttk.Radiobutton(self.label_frame, text=option[0], value=option[1], variable=self.selected_option,
                                    style='bg_color.TRadiobutton', takefocus=False)
                r.grid(column=0, row=index, padx=10, sticky='w')
            self.set_sensor_type(0)

        def get_sensor_type(self):
            return self.selected_option.get()

        def set_sensor_type(self, val):
            self.selected_option.set(val)

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='Connecting Sensor with API', close_command=self._help_button.enable,
                             image_dir_en='images\\sensor_type\\en', image_dir_cn='images\\sensor_type\\cn')

    class ConnectionFrame(Frame):
        class ConnectWindow(Toplevel):
            class ConnWinErrorBox(Toplevel):
                def __init__(self, close_command=None, hide_command=None, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.close_command = close_command
                    self.hide_command = hide_command

                    (width, height) = (360, 100)
                    frm_width = self.winfo_rootx() - self.winfo_x()
                    win_width = width + 2 * frm_width
                    titlebar_height = self.winfo_rooty() - self.winfo_y()
                    win_height = height + titlebar_height + frm_width
                    x = self.winfo_screenwidth() // 2 - win_width // 2 - 250
                    y = self.winfo_screenheight() // 2 - win_height // 2 - 10
                    self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                    self.deiconify()
                    self.resizable(False, False)
                    self.attributes('-topmost', True)
                    self.title('Error')
                    self.protocol("WM_DELETE_WINDOW", self._conn_win_on_close)

                    main_frame = Frame(self, bg=self['bg'])
                    main_frame.pack(fill='both', expand=True, pady=10, ipady=20)
                    txt = 'Error in Connecting to the Device! '
                    resized_image = Image.open('images/xbox.png').resize((48, 48))
                    self.img = ImageTk.PhotoImage(resized_image)
                    Label(main_frame, bg=main_frame['bg'], image=self.img, text=txt, font='calibri 9', anchor='w',
                          compound='left', justify='left', padx=10).pack(side='top')
                    RoundCornerButton(master=main_frame, text='Close', size='xs', width=70, height=25,
                                      command=self._conn_win_on_close, bg=main_frame['bg']).pack(side='right', padx=5,
                                                                                                 anchor='e')
                    RoundCornerButton(master=main_frame, text='Trouble Shooting', size='xs', width=120, height=25,
                                      command=self._trouble_shooting, bg=main_frame['bg']).pack(side='right',
                                                                                                anchor='e')
                    img = Image.open('images/connection_trouble_shooting_CHR-C.png')
                    self.chrc_img_size = img.size
                    self.chrc_img = ImageTk.PhotoImage(img)

                def _trouble_shooting(self):
                    PowerPointWindow(master=self, title='Connection', close_command=self._conn_win_on_close,
                                     image_dir_en='images/connection')
                    self.withdraw()
                    if self.hide_command is not None:
                        self.hide_command()

                def _conn_win_on_close(self):
                    self.destroy()
                    if self.hide_command is not None:
                        self.close_command()

            def __init__(self, close_command=None, ip='', port='', *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.close_command = close_command

                (width, height) = (670, 90)
                frm_width = self.winfo_rootx() - self.winfo_x()
                win_width = width + 2 * frm_width
                titlebar_height = self.winfo_rooty() - self.winfo_y()
                win_height = height + titlebar_height + frm_width
                x = self.winfo_screenwidth() // 2 - win_width // 2
                y = self.winfo_screenheight() // 2 - win_height // 2
                self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                self.deiconify()
                self.resizable(False, False)
                self.attributes('-topmost', True)
                self.title('Connecting to CHR Device...')
                self.protocol("WM_DELETE_WINDOW", self.conn_win_on_close)

                frame = Frame(self, bg=self['bg'])
                frame.pack(fill='both', expand=True, pady=10, ipady=20)
                txt = 'Trying to connect to IP {} Open connecting for to device'.format(ip)
                Label(frame, bg=frame['bg'], text=txt, font='calibri 9', anchor='w', padx=40).pack(side='top', fill='x')
                self.progress_bar = ttk.Progressbar(frame, orient="horizontal", length=100, mode="indeterminate")
                self.progress_bar.pack(side='top', fill='x', padx=40)
                self.progress_bar.start(10)
                RoundCornerButton(master=frame, text='Cancel', size='xs', width=70, height=25,
                                  command=self.conn_win_on_close, bg=frame['bg']).pack(side='top')

            def conn_win_on_close(self):
                self.destroy()
                self.close_command()

            def _on_hide(self):
                self.withdraw()

            def error_window(self):
                try:
                    self.ConnWinErrorBox(master=self, close_command=self.conn_win_on_close, hide_command=self._on_hide)
                except TclError:
                    pass

        class AutoSearchWindow(Toplevel):
            class AutoSearchErrorBox(Toplevel):
                def __init__(self, close_command=None, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.close_command = close_command
                    (width, height) = (400, 100)
                    frm_width = self.winfo_rootx() - self.winfo_x()
                    win_width = width + 2 * frm_width
                    titlebar_height = self.winfo_rooty() - self.winfo_y()
                    win_height = height + titlebar_height + frm_width
                    x = self.winfo_screenwidth() // 2 - win_width // 2 - 250
                    y = self.winfo_screenheight() // 2 - win_height // 2 - 10
                    self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                    self.deiconify()
                    self.resizable(False, False)
                    self.attributes('-topmost', True)
                    self.title('Error')
                    self.protocol("WM_DELETE_WINDOW", self._on_close)

                    main_frame = Frame(self, bg=self['bg'])
                    main_frame.pack(fill='both', expand=True, pady=10, ipady=20)
                    txt = 'No device is available. Please check device connection.'
                    resized_image = Image.open('images/xbox.png').resize((48, 48))
                    self.img = ImageTk.PhotoImage(resized_image)
                    Label(main_frame, bg=main_frame['bg'], image=self.img, text=txt, font='calibri 9', anchor='w',
                          compound='left', justify='left', padx=10).pack(side='top')
                    RoundCornerButton(master=main_frame, text='Close', size='xs', width=70, height=25,
                                      command=self._on_close, bg=main_frame['bg']).pack(side='right', padx=5,
                                                                                        anchor='e')

                def _on_close(self):
                    self.destroy()
                    if self.close_command is not None:
                        self.close_command()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                (width, height) = (600, 250)
                frm_width = self.winfo_rootx() - self.winfo_x()
                win_width = width + 2 * frm_width
                titlebar_height = self.winfo_rooty() - self.winfo_y()
                win_height = height + titlebar_height + frm_width
                x = self.winfo_screenwidth() // 2 - win_width // 2
                y = self.winfo_screenheight() // 2 - win_height // 2
                self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                self.deiconify()
                self.resizable(False, False)
                self.attributes('-topmost', True)
                self.title('Finding Sensor...')
                self.protocol("WM_DELETE_WINDOW", self._auto_win_on_close)

                self.auto_main_f = Frame(self, bg=self['bg'])
                self.auto_main_f.pack(fill='both', expand=True, pady=10, ipady=20)
                self.radio_button_f = None
                self.radio_button_sub_f = None
                txt = 'Finding CHR Devices'
                Label(self.auto_main_f, bg=self.auto_main_f['bg'], text=txt, font='calibri 9', anchor='w',
                      padx=40).pack(side='top', fill='x')
                self._max_options = 5
                self._options = [['', 0]]
                self.selected_option = IntVar()
                self.config_radio_button(count=0, options=self._options)
                self.selected_option.set(0)
                self._progress_bar = ttk.Progressbar(self.auto_main_f, orient="horizontal", length=100,
                                                     mode="indeterminate")
                self._progress_bar.pack(side='top', fill='x', padx=40)
                self._progress_bar.start(10)
                self._btn_f = Frame(self.auto_main_f)
                self._btn_f.pack(side='top')
                RoundCornerButton(master=self._btn_f, text='Cancel', size='xs', width=80, height=25,
                                  command=self._auto_win_on_close, bg=self.auto_main_f['bg']).pack(side='left')
                self._conn_btn = RoundCornerButton(master=self._btn_f, text='Connect', size='xs', width=80, height=25,
                                                   command=self._conn, bg=self.auto_main_f['bg'])
                self._conn_btn.pack(side='left', padx=10)
                self.disable_conn_btn()
                self.auto_search_device_callback = None
                self.conn_callback = None
                self.cancel_callback = None
                self._after_id = None

            def config_radio_button(self, count: int, options):
                count = self._max_options if count > self._max_options else count
                [options.append(('', i)) for i in range(self._max_options - count)]
                if self.radio_button_sub_f is not None:
                    self.radio_button_sub_f.pack_forget()
                if self.radio_button_sub_f is None:
                    s = ttk.Style()
                    s.configure('Wild2.TRadiobutton', background='white')
                    self.radio_button_f = Frame(self.auto_main_f, bg='white')
                    self.radio_button_f.pack(side='top', padx=40, pady=5, anchor='w')
                self.radio_button_sub_f = Frame(self.radio_button_f, bg='white', borderwidth=3, highlightthickness=0,
                                                relief='sunken')
                self.radio_button_sub_f.pack(side='top')
                Canvas(self.radio_button_sub_f, width=550, height=120, bg='white').grid(column=0, row=0,
                                                                                        rowspan=self._max_options)
                for index, option in enumerate(options):
                    if len(option[0]) > 0:
                        r = ttk.Radiobutton(self.radio_button_sub_f, text=option[0], value=option[1],
                                            style='Wild2.TRadiobutton', variable=self.selected_option, takefocus=False)
                        r.grid(column=0, row=index, sticky='w')
                self._options = options

            def disable_conn_btn(self):
                self._conn_btn['state'] = 'disable'

            def enable_conn_btn(self):
                self._conn_btn['state'] = 'normal'

            def get_selected_option(self):
                return self.selected_option.get()

            def error_window(self):
                try:
                    self.AutoSearchErrorBox(master=self, close_command=self._auto_win_on_close)
                except TclError:
                    pass

            def check_search_results(self):
                if self.auto_search_device_callback is not None:
                    results = self.auto_search_device_callback()
                    if results is False:
                        self._after_id = self.after(200, self.check_search_results)
                    else:
                        self.after_cancel(self._after_id)
                        count = len(results)
                        if count > 0:
                            options = [(v, i) for (i, v) in enumerate(results)]
                            self.config_radio_button(count=count, options=options)
                            self.enable_conn_btn()
                        else:
                            self.AutoSearchErrorBox(master=self, close_command=self._auto_win_on_close)

            def _auto_win_on_close(self):
                self.destroy()
                if self.cancel_callback is not None:
                    self.cancel_callback()

            def _conn(self):
                if self.conn_callback is not None:
                    self.conn_callback()
                    self._auto_win_on_close()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.label_f = ttk.LabelFrame(self, text='Connection')
            self.label_f.grid(column=0, row=0, columnspan=2)
            background = Canvas(self.label_f, width=220, height=60)
            background.grid(column=0, row=0, rowspan=5, sticky='nswe')

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=1, row=0, sticky='en')

            self._ip_entry = Entry(self.label_f)
            self._ip_entry.grid(column=0, row=0, padx=25, pady=3, sticky='we')

            self.connect_txt = 'Connect'
            self.disconnect_txt = 'Disconnect'

            self.conn_btn = RoundCornerButtonGR(master=self.label_f, size='m', width=150, height=25, bg=self['bg'],
                                                normal='1_2', green='1_2', red='1_2', text='Connect',
                                                command=self.conn)
            self.conn_btn.grid(column=0, row=1, padx=10, ipadx=20)
            self._auto_search_btn = ttk.Button(self.label_f, text='         Auto Search', takefocus=False,
                                               command=self.auto_search)
            self._auto_search_btn.grid(column=0, row=2, padx=10, ipadx=14)

            self._conn_btn_callback = None
            self._disconn_btn_callback = None
            self._auto_search_callback = None
            self.conn_win = None
            self.auto_search_win = None

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='Connection', close_command=self._help_button.enable,
                             image_dir_en='images/connection_trouble shooting/en',
                             image_dir_cn='images/connection_trouble shooting/cn')

        def conn(self):
            self.disable_conn_button()
            self.conn_win = self.ConnectWindow(master=self, close_command=self.enable_conn_button, ip=self.get_ip())
            if self._conn_btn_callback is not None:
                self._conn_btn_callback()

        def disconn(self):
            self.disable_conn_button()
            if self._disconn_btn_callback is not None:
                self._disconn_btn_callback()
            self.enable_conn_button()
            self.set_btn_disconnected()

        def auto_search(self):
            self.auto_search_win = self.AutoSearchWindow(master=self)
            if self._auto_search_callback is not None:
                self._auto_search_callback()
                self.auto_search_win.check_search_results()

        def close_conn_win(self):
            self.conn_win.conn_win_on_close()

        def disable_conn_button(self):
            self.conn_btn.disable()

        def enable_conn_button(self):
            self.conn_btn.enable()

        def disable_auto_button(self):
            self._auto_search_btn['state'] = 'disabled'

        def enable_auto_button(self):
            self._auto_search_btn['state'] = 'normal'

        def set_btn_connected(self):
            self.conn_btn.cmd(self.disconn)
            self.conn_btn.text(self.disconnect_txt)
            self.conn_btn.set_button_color('g')

        def set_btn_disconnected(self):
            self.conn_btn.cmd(self.conn)
            self.conn_btn.text(self.connect_txt)
            self.conn_btn.set_button_color('n')

        def disable_ip_entry(self):
            self._ip_entry['state'] = 'disabled'

        def enable_ip_entry(self):
            self._ip_entry['state'] = 'normal'

        def set_ip(self, value: str):
            state_changed = False
            if self._ip_entry['state'] == 'disabled':
                self._ip_entry['state'] = 'normal'
            self._ip_entry.delete(0, 'end')
            self._ip_entry.insert(0, value)
            if state_changed:
                self._ip_entry['state'] = 'disabled'

        def get_ip(self) -> Optional[str]:
            try:
                _ip = self._ip_entry.get()
            except TclError:
                _ip = None
            return _ip

        def set_conn_callback(self, cmd):
            self._conn_btn_callback = cmd

        def set_disconn_btn_callback(self, cmd):
            self._disconn_btn_callback = cmd

        def set_auto_search_callback(self, cmd):
            self._auto_search_callback = cmd

        def set_auto_search_device_callback(self, cmd):
            if self.auto_search_win is not None:
                self.auto_search_win.auto_search_device_callback = cmd

        def set_auto_conn_callback(self, cmd):
            if self.auto_search_win is not None:
                self.auto_search_win.conn_callback = cmd

        def set_cancel_callback(self, cmd):
            if self.auto_search_win is not None:
                self.auto_search_win.cancel_callback = cmd

    class DarkReferenceFrame(Frame):
        class InfoBox(Toplevel):
            def __init__(self, dark_type: int, freq: str, close_command=None, *args, **kwargs):
                """
                :param dark_type: 0: Dark reference; 1: Fast Dark reference
                """
                super().__init__(*args, **kwargs)
                self.close_command = close_command
                (width, height) = (400, 120)
                frm_width = self.winfo_rootx() - self.winfo_x()
                win_width = width + 2 * frm_width
                titlebar_height = self.winfo_rooty() - self.winfo_y()
                win_height = height + titlebar_height + frm_width
                x = self.winfo_screenwidth() // 2 - win_width // 2
                y = self.winfo_screenheight() // 2 - win_height // 2
                self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
                self.deiconify()
                self.resizable(False, False)
                self.attributes('-topmost', True)
                self.title('Information')
                self.protocol("WM_DELETE_WINDOW", self._info_on_close)

                main_frame = Frame(self, bg='white')
                main_frame.pack(side='top', fill='both', expand=True)
                dark_type_str = 'Dark' if dark_type == 0 else 'Fast Dark'
                txt = '{} Reference has been completed! Device response:\n $DRK {}Hz ready.'.format(dark_type_str, freq)
                resized_image = Image.open('images/info.png').resize((40, 40))
                self.img = ImageTk.PhotoImage(resized_image)
                Label(main_frame, bg=main_frame['bg'], image=self.img, text=txt, font='calibri 9', anchor='w',
                      compound='left', justify='left', padx=10, pady=5).pack(side='top')
                RoundCornerButton(master=self, text='OK', size='xs', width=70, height=25,
                                  command=self._info_on_close, bg=self['bg']).pack(side='top', padx=5, pady=10,
                                                                                   anchor='e')

            def _info_on_close(self):
                self.destroy()
                if self.close_command is not None:
                    self.close_command()

        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Dark Reference')
            self.label_frame.grid(column=0, row=0, columnspan=2)
            background = Canvas(self.label_frame, width=220, height=70)
            background.grid(column=0, row=0, rowspan=2, sticky='nswe')

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=1, row=0, sticky='en')

            self.perform_dark_button = ttk.Button(self.label_frame, text='       Perform Dark', takefocus=False,
                                                  command=self._perform_dark)
            self.perform_dark_button.grid(column=0, row=0, padx=10, ipadx=14)
            self.fast_dark_button = ttk.Button(self.label_frame, text='           Fast Dark', takefocus=False,
                                               command=self._fast_dark)
            self.fast_dark_button.grid(column=0, row=1, padx=10, ipadx=20)
            self._dark_callback = None
            self._fast_dark_callback = None

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='About Dark Reference', close_command=self._help_button.enable,
                             image_dir_en='images\\perform_dark_reference\\en',
                             image_dir_cn='images\\perform_dark_reference\\cn')

        def _perform_dark(self):
            if self._dark_callback is not None:
                self._dark_callback()

        def _fast_dark(self):
            if self._fast_dark_callback is not None:
                self._fast_dark_callback()

        def info_window(self, dark_type: int, freq: str, on_close_cmd: Callable):
            """
            dark_type: 0: Dark reference; 1: Fast Dark reference
            """
            try:
                self.InfoBox(master=self, dark_type=dark_type, freq=freq, close_command=on_close_cmd)
            except TclError:
                pass

        def disable_dark_button(self):
            self.perform_dark_button['state'] = 'disable'

        def enable_dark_button(self):
            self.perform_dark_button['state'] = 'normal'

        def disable_fast_dark_button(self):
            self.fast_dark_button['state'] = 'disable'

        def enable_fast_dark_button(self):
            self.fast_dark_button['state'] = 'normal'

        def set_dark_callback(self, cmd):
            self._dark_callback = cmd

        def set_fast_dark_callback(self, cmd):
            self._fast_dark_callback = cmd

    class ProbeSelection(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Probe Selection')
            self.label_frame.grid(column=0, row=0, columnspan=2)
            background = Canvas(self.label_frame, width=220, height=60)
            background.grid(column=0, row=0, rowspan=2, sticky='nswe')

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=1, row=0, sticky='en')

            self._selected_probe = StringVar()
            s = ttk.Style()
            s.configure("TCombobox", fieldbackground="white", background="white",
                        selectbackground=None, selectforeground=None)
            self.probe_select_combobox = ttk.Combobox(self.label_frame, textvariable=self._selected_probe, width=25,
                                                      state='readonly', takefocus=False)
            self.probe_select_combobox.grid(column=0, row=0, columnspan=2, padx=15, pady=10, sticky='wn')
            self.probe_select_combobox.bind("<<ComboboxSelected>>", self.probe_select_command)

            self.full_scale_string = StringVar()
            self.set_full_scale('')
            self.full_scale_label = Label(self.label_frame, textvariable=self.full_scale_string, bg='#ffffe1')
            self.full_scale_label.grid(column=0, row=1, padx=20, sticky='w')

            self._probe_select_callback = None

        def probe_select_command(self, e):
            if self._probe_select_callback is not None:
                self._probe_select_callback()

        def set_probe_select_callback(self, cmd):
            self._probe_select_callback = cmd

        def clear_probe_select_callback(self):
            self._probe_select_callback = None

        def set_probe_list(self, probe_list):
            self.probe_select_combobox['value'] = probe_list

        def clear_probe_list(self):
            self.probe_select_combobox['value'] = []

        def set_probe(self, index):
            try:
                self._selected_probe.set(self.probe_select_combobox['value'][index])
            except IndexError:
                pass

        def clear_probe(self):
            self._selected_probe.set('')

        def get_selected_probe(self):
            return self._selected_probe.get()

        def set_full_scale(self, value):
            self.full_scale_string.set(f'Full Scale: {value} ㎛')

        def clear_full_scale_string(self):
            self.full_scale_string.set('Full Scale:')

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='Probe Selection', close_command=self._help_button.enable,
                             image_dir_en='images\\probe_selection\\en', image_dir_cn='images\\probe_selection\\cn')

    class MultilayerSettingFrame(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Multi-layer Setting')
            self.label_frame.grid(column=0, row=0)
            background = Canvas(self.label_frame, width=220, height=60)
            background.grid(column=0, row=0, rowspan=2, columnspan=3, sticky='nswe')

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=0, row=0, sticky='en')

            self.number_of_peak_label = Label(self.label_frame, text='Number of Peak:', bg=background['bg'])
            self.number_of_peak_label.grid(column=0, row=0, padx=15, sticky='w')
            self.number_of_peak_entry = Entry(self.label_frame, width=9)
            self.number_of_peak_entry.grid(column=1, row=0, sticky='w')
            self.number_of_peak_entry.bind('<Return>', self._entry_command)
            s = ttk.Style()
            s.configure('TCheckbutton', background=background['bg'])
            self.checkbox_var = StringVar()
            self.detection_window_checkbutton = ttk.Checkbutton(self.label_frame, text='Detection Window Active',
                                                                command=self.dwd_checked, variable=self.checkbox_var,
                                                                onvalue=1, offvalue=0, takefocus=False)
            self.detection_window_checkbutton.grid(column=0, row=1, columnspan=2, padx=15, sticky='w')
            self._number_of_peak_callback = None

        def _entry_command(self, e):
            if self._number_of_peak_callback is not None:
                self._number_of_peak_callback()

        def set_number_of_peak_callback(self, cmd):
            self._number_of_peak_callback = cmd

        def set_lf_number_of_peak(self, val):
            self.number_of_peak_entry.delete(0, 'end')
            self.number_of_peak_entry.insert('end', val)

        def get_lf_number_of_peak(self) -> str:
            return self.number_of_peak_entry.get()

        def dwd_checked(self):
            pass

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='Multi-layer Setting',
                             close_command=self._help_button.enable,
                             image_dir_en='images\\multi-layer setting\\en',
                             image_dir_cn='images\\multi-layer setting\\cn')

    class AverageFrame(Frame):
        def __init__(self, *args, **kwargs):
            self.selected_option = StringVar()
            super().__init__(*args, **kwargs)
            self.label_frame = ttk.LabelFrame(self, text='Average')
            self.label_frame.grid(column=0, row=0)
            background = Canvas(self.label_frame, width=220, height=60)
            background.grid(column=0, row=0, rowspan=2, columnspan=3, sticky='nswe')

            self._help_button = HelpButton(master=self, command=self._help)
            self._help_button.grid(column=0, row=0, sticky='en')

            self.data_sample_label = Label(self.label_frame, text='Data Sample Average:', bg=background['bg'])
            self.data_sample_label.grid(column=0, row=0, padx=15, sticky='w')
            self._data_sample_entry = Entry(self.label_frame, width=6)
            self._data_sample_entry.grid(column=1, row=0, sticky='w')
            self._data_sample_entry.bind('<Return>', self._data_sample_entry_command)
            self.spectrum_average_label = Label(self.label_frame, text='Spectrum Average:', bg=background['bg'])
            self.spectrum_average_label.grid(column=0, row=1, padx=15, sticky='w')
            self._spectrum_average_entry = Entry(self.label_frame, width=6)
            self._spectrum_average_entry.grid(column=1, row=1, sticky='w')
            self._spectrum_average_entry.bind('<Return>', self._spectrum_average_entry_command)

            self._data_sample_callback = None
            self._spectrum_average_callback = None

        def _help(self):
            self._help_button.disable()
            PowerPointWindow(master=self, title='About Average', close_command=self._help_button.enable,
                             image_dir_en='images\\average\\en', image_dir_cn='images\\average\\cn')

        def set_data_sample_callback(self, cmd):
            self._data_sample_callback = cmd

        def set_spectrum_average_callback(self, cmd):
            self._spectrum_average_callback = cmd

        def _data_sample_entry_command(self, e):
            if self._data_sample_callback is not None:
                self._data_sample_callback()

        def _spectrum_average_entry_command(self, e):
            if self._spectrum_average_callback is not None:
                self._spectrum_average_callback()

        def set_data_sample(self, val):
            self._data_sample_entry.delete(0, 'end')
            self._data_sample_entry.insert('end', val)

        def get_data_sample(self):
            return self._data_sample_entry.get()

        def clear_data_sample(self):
            self._data_sample_entry.delete(0, 'end')

        def set_spectrum_average(self, val):
            self._spectrum_average_entry.delete(0, 'end')
            self._spectrum_average_entry.insert('end', val)

        def get_spectrum_average(self):
            return self._spectrum_average_entry.get()

        def clear_spectrum_average(self):
            self._spectrum_average_entry.delete(0, 'end')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Label(self, text='Operation Check List', relief='sunken', anchor='center').pack(side='top', fill='x',
                                                                                            pady=3, ipady=5)
        self.sensor_type_f = self.SensorTypeFrame(self)
        self.sensor_type_f.pack(side='top', fill='x', pady=3)
        self.conn_f = self.ConnectionFrame(self)
        self.conn_f.pack(side='top', fill='x', pady=3)
        self.dark_ref_f = self.DarkReferenceFrame(self)
        self.dark_ref_f.pack(side='top', fill='x', pady=3)
        self.probe_sel_f = self.ProbeSelection(self)
        self.probe_sel_f.pack(side='top', fill='x', pady=3)
        self.multilayer_stn_f = self.MultilayerSettingFrame(self)
        self.multilayer_stn_f.pack(side='top', fill='x', pady=3)
        self.average_f = self.AverageFrame(self)
        self.average_f.pack(side='top', fill='x', pady=3)


class _MainFrame(Frame):
    class IntroductionPage(Frame):
        class Col0Frame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                img_size = [850, 565]
                self.configure()
                self.config(width=img_size[0], height=img_size[1])

                img = Image.open('images/introduction_background_manual.png').resize((img_size[0], img_size[1]))
                self.img = ImageTk.PhotoImage(img)
                Label(self, image=self.img, bg=self['bg'], anchor='n').place(x=0, y=0, width=850, height=675)

                left_space = 300
                col1_x = left_space + 100
                col2_x = left_space + 253
                col3_x = left_space + 409

                top_space = 75
                row1_y = top_space  # CLS
                row2_y = top_space + 49  # CLS2
                row3_y = top_space + 90  # CLS2 Pro
                row4_y = top_space + 133  # CVC
                row5_y = top_space + 175  # Mini
                row6_y = top_space + 212  # C
                row7_y = top_space + 255  # 2S
                row8_y = top_space + 300  # Overall
                row9_y = top_space + 342  # IT
                row10_y = top_space + 383  # DPS
                row11_y = top_space + 423  # FSS40/80
                row12_y = top_space + 459  # FSS310

                button_list = [
                    {'text': 'CLS', 'width': 104, 'height': 30, 'size': 's', 'x': col1_x, 'y': row1_y,
                     'command': lambda doc='datasheet', sensor='CLS': self._open_manual(doc, sensor)},
                    {'text': 'CLS', 'width': 104, 'height': 30, 'size': 's', 'x': col2_x, 'y': row1_y,
                     'command': lambda doc='user manual', sensor='CLS': self._open_manual(doc, sensor)},
                    {'text': 'CLS', 'width': 115, 'height': 45, 'size': 's', 'x': col3_x, 'y': row1_y,
                     'command': lambda doc='command manual', sensor='CLS': self._open_manual(doc, sensor)},
                    {'text': 'CLS 2', 'width': 104, 'height': 26, 'size': 's', 'x': col1_x, 'y': row2_y,
                     'command': lambda doc='datasheet', sensor='CLS2': self._open_manual(doc, sensor)},
                    {'text': 'CLS 2', 'width': 104, 'height': 26, 'size': 's', 'x': col2_x, 'y': row2_y,
                     'command': lambda doc='user manual', sensor='CLS2': self._open_manual(doc, sensor)},
                    {'text': 'CLS 2Pro', 'width': 104, 'height': 26, 'size': 's', 'x': col1_x, 'y': row3_y,
                     'command': lambda doc='datasheet', sensor='CLS 2Pro': self._open_manual(doc, sensor)},
                    {'text': 'CLS 2Pro', 'width': 104, 'height': 26, 'size': 's', 'x': col2_x, 'y': row3_y,
                     'command': lambda doc='user manual', sensor='CLS 2Pro': self._open_manual(doc, sensor)},
                    {'text': 'CVC', 'width': 104, 'height': 26, 'size': 's', 'x': col1_x, 'y': row4_y,
                     'command': lambda doc='datasheet', sensor='CVC': self._open_manual(doc, sensor)},
                    {'text': 'CVC', 'width': 104, 'height': 26, 'size': 's', 'x': col2_x, 'y': row4_y,
                     'command': lambda doc='user manual', sensor='CVC': self._open_manual(doc, sensor)},
                    {'text': 'CVC SDK', 'width': 115, 'height': 26, 'size': 's', 'x': col3_x, 'y': row4_y,
                     'command': lambda doc='command manual', sensor='CVC': self._open_manual(doc, sensor)},
                    {'text': 'Mini', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row5_y,
                     'command': lambda doc='datasheet', sensor='Mini': self._open_manual(doc, sensor)},
                    {'text': 'Mini', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row5_y,
                     'command': lambda doc='user manual', sensor='Mini': self._open_manual(doc, sensor)},
                    {'text': 'Mini/C', 'width': 115, 'height': 23, 'size': 's', 'x': col3_x, 'y': row5_y,
                     'command': lambda doc='command manual', sensor='Mini': self._open_manual(doc, sensor)},
                    {'text': 'C', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row6_y,
                     'command': lambda doc='datasheet', sensor='C': self._open_manual(doc, sensor)},
                    {'text': 'C', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row6_y,
                     'command': lambda doc='user manual', sensor='C': self._open_manual(doc, sensor)},
                    # {'text': 'C', 'width': 115, 'height': 23, 'size': 's', 'x': col3_x, 'y': row5_y,
                    #  'command': lambda doc='command manual', sensor='C': self._open_manual(doc, sensor)},
                    {'text': '2S', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row7_y,
                     'command': lambda doc='datasheet', sensor='2S': self._open_manual(doc, sensor)},
                    {'text': '2S', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row7_y,
                     'command': lambda doc='user manual', sensor='2S': self._open_manual(doc, sensor)},
                    {'text': '2S', 'width': 115, 'height': 23, 'size': 's', 'x': col3_x, 'y': row7_y,
                     'command': lambda doc='command manual', sensor='2S': self._open_manual(doc, sensor)},
                    {'text': 'Confocal', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row8_y,
                     'command': lambda doc='datasheet', sensor='2S': self._open_manual(doc, sensor)},
                    {'text': 'IT', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row9_y,
                     'command': lambda doc='datasheet', sensor='IT': self._open_manual(doc, sensor)},
                    {'text': 'IT', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row9_y,
                     'command': lambda doc='user manual', sensor='IT': self._open_manual(doc, sensor)},
                    {'text': 'IT', 'width': 115, 'height': 23, 'size': 's', 'x': col3_x, 'y': row9_y,
                     'command': lambda doc='command manual', sensor='IT': self._open_manual(doc, sensor)},
                    {'text': 'DPS', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row10_y,
                     'command': lambda doc='datasheet', sensor='DPS': self._open_manual(doc, sensor)},
                    {'text': 'DPS', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row10_y,
                     'command': lambda doc='user manual', sensor='DPS': self._open_manual(doc, sensor)},
                    {'text': 'DPS', 'width': 115, 'height': 23, 'size': 's', 'x': col3_x, 'y': row10_y,
                     'command': lambda doc='command manual', sensor='DPS': self._open_manual(doc, sensor)},
                    {'text': 'FSS40/80', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row11_y,
                     'command': lambda doc='datasheet', sensor='FSS80': self._open_manual(doc, sensor)},
                    {'text': 'FSS40/80', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row11_y,
                     'command': lambda doc='user manual', sensor='FSS80': self._open_manual(doc, sensor)},
                    {'text': 'FSS', 'width': 115, 'height': 40, 'size': 's', 'x': col3_x, 'y': row11_y,
                     'command': lambda doc='command manual', sensor='FSS': self._open_manual(doc, sensor)},
                    {'text': 'FSS310', 'width': 104, 'height': 23, 'size': 's', 'x': col1_x, 'y': row12_y,
                     'command': lambda doc='datasheet', sensor='FSS310': self._open_manual(doc, sensor)},
                    {'text': 'FSS310', 'width': 104, 'height': 23, 'size': 's', 'x': col2_x, 'y': row12_y,
                     'command': lambda doc='user manual', sensor='FSS310': self._open_manual(doc, sensor)},
                ]
                for cfg in button_list:
                    RoundCornerButton(master=self, text=cfg['text'], width=cfg['width'], height=cfg['height'],
                                      bg=self['bg'], size=cfg['size'], command=cfg['command']).place(x=cfg['x'],
                                                                                                     y=cfg['y'])

                self.open_manual_callback = None

            def _open_manual(self, manual_type, sensor):
                if self.open_manual_callback is not None:
                    self.open_manual_callback(manual_type, sensor)

        class Col1Frame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                img = Image.open('images/introduction_background_sample_code.png').resize((134, 486))
                self.bg_img = ImageTk.PhotoImage(img)
                Label(self, width=1, height=1, bg='red', borderwidth=1, relief="solid").grid(column=0, row=0,
                                                                                             sticky='nw')
                Label(self, image=self.bg_img, bg=self['bg']).grid(column=0, row=0, rowspan=6, sticky='nsew')
                btn_size = (20, 20)
                self.search_f = Frame(self, bg=self['bg'])
                self.search_f.bind("<Enter>", self._search_f_on_enter)
                self.search_f.bind("<Leave>", self._search_f_on_leave)
                self.search_f.bind("<FocusOut>", self._search_f_on_leave)
                image = Image.open('images/excel.png')
                resize_img = image.resize(btn_size)
                self.excel_img = ImageTk.PhotoImage(resize_img)
                self._excel_btn = Button(self.search_f, image=self.excel_img, bg='#4472C4', relief='groove',
                                         activebackground=self['bg'], command=self._sample_code_table)
                image = Image.open('images/search.png')
                resize_img = image.resize(btn_size)
                self.search_img = ImageTk.PhotoImage(resize_img)
                self._search_btn = Button(self.search_f, image=self.search_img, bg='#4472C4', relief='groove',
                                          activebackground=self['bg'], command=self._search_sample_code)
                self.search_entry = Entry(self.search_f, width=5)
                self.search_entry.bind("<Return>", lambda event: self._search_sample_code())
                self._excel_btn.pack(side='left')
                self._search_btn.pack(side='left')

                btn_size = (60, 60)
                image = Image.open('images/c++_logo.png')
                resize_image = image.resize(btn_size)
                self.c_plus_plus_img = ImageTk.PhotoImage(resize_image)
                image = Image.open('images/c#_logo.png')
                resize_image = image.resize(btn_size)
                self.c_sharp_img = ImageTk.PhotoImage(resize_image)
                image = Image.open('images/python_logo.png')
                resize_image = image.resize(btn_size)
                self.python_img = ImageTk.PhotoImage(resize_image)
                self.c_plus_plus_btn = Button(self, image=self.c_plus_plus_img, bg=self['bg'], relief='groove',
                                              command=lambda x='C++': self._open_sample_code(x))
                self.c_sharp_btn = Button(self, image=self.c_sharp_img, bg=self['bg'], relief='groove',
                                          command=lambda x='C#': self._open_sample_code(x))
                self.python_btn = Button(self, image=self.python_img, bg=self['bg'], relief='groove',
                                         command=lambda x='Python': self._open_sample_code(x))
                self.search_f.grid(column=0, row=1, padx=10, pady=5, sticky='w')
                self.c_plus_plus_btn.grid(column=0, row=2, pady=26, sticky='n')
                self.c_sharp_btn.grid(column=0, row=3, pady=39, sticky='n')
                self.python_btn.grid(column=0, row=4, pady=20, sticky='n')
                self.open_sample_code_callback = None
                self.sample_code_table_callback = None
                self.search_sample_code_callback = None

            def _open_sample_code(self, program_type):
                if self.open_sample_code_callback is not None:
                    self.open_sample_code_callback(program_type)

            def _sample_code_table(self):
                if self.sample_code_table_callback is not None:
                    self.sample_code_table_callback()

            def _search_sample_code(self):
                if self.search_sample_code_callback is not None:
                    self.search_sample_code_callback()

            def _search_f_on_enter(self, event):
                self.search_entry.pack(side='left', padx=3)

            def _search_f_on_leave(self, event):
                if len(self.search_entry.get()) == 0:
                    self.search_entry.pack_forget()

        class Col2Frame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                img = Image.open('images/introduction_background_api.png').resize((134, 330))
                self.bg_img = ImageTk.PhotoImage(img)
                Label(self, width=1, height=1, bg='red', borderwidth=1, relief="solid").grid(column=0, row=0, pady=15,
                                                                                             sticky='nw')
                Label(self, image=self.bg_img, bg=self['bg']).grid(column=0, row=0, rowspan=3, sticky='nsew')

                btn_size = (72, 72)
                self._api_img = ImageTk.PhotoImage(Image.open('images/API.png').resize(btn_size))
                self._api_btn = Button(self, image=self._api_img, bg=self['bg'], relief='groove',
                                       command=self._open_api)
                self._api_btn.grid(column=0, row=1, pady=12, sticky='n')
                self._api_manual_img = ImageTk.PhotoImage(Image.open('images/api_manual.png').resize(btn_size))
                self._api_manual_btn = Button(self, image=self._api_manual_img, bg=self['bg'], relief='groove',
                                              command=lambda x='api manual', y=None: self._open_api_manual(x, y))
                self._api_manual_btn.grid(column=0, row=2, pady=0, sticky='n')
                self.open_api_callback = None
                self.open_api_manual_callback = None

            def _open_api(self):
                if self.open_api_callback is not None:
                    self.open_api_callback()

            def _open_api_manual(self, manual_type, sensor):
                if self.open_api_manual_callback is not None:
                    self.open_api_manual_callback(manual_type, sensor)

        class Col3Frame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                img = Image.open('images/introduction_background_tool.png').resize((141, 200))
                self.bg_img = ImageTk.PhotoImage(img)
                Label(self, width=1, height=1, bg='red', borderwidth=1, relief="solid").grid(column=0, row=0, pady=20,
                                                                                             sticky='nw')
                Label(self, image=self.bg_img, bg=self['bg']).grid(column=0, row=0, rowspan=2, sticky='nsew')

                btn_size = (72, 72)
                self._chr_explorer_img = ImageTk.PhotoImage(Image.open('images/CHRExplorerIcon.png').resize(btn_size))
                self.btn = Button(self, image=self._chr_explorer_img, bg=self['bg'], relief='groove',
                                  command=self._open_chr_explorer_callback)
                self.btn.grid(column=0, row=1, pady=12, sticky='n')
                self.open_chr_explorer_callback = None

            def _open_chr_explorer_callback(self):
                if self.open_chr_explorer_callback is not None:
                    self.open_chr_explorer_callback()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_frame = Frame(self, bg=self['bg'])
            main_frame.pack(side='top', fill='x', padx=30, pady=5)
            self.col_0_f = self.Col0Frame(main_frame, bg=self['bg'])
            self.col_0_f.grid(column=0, row=0, sticky='n')
            self.col_1_f = self.Col1Frame(main_frame, bg=self['bg'])
            self.col_1_f.grid(column=1, row=0, padx=5, sticky='n')
            self.col_2_f = self.Col2Frame(main_frame, bg=self['bg'])
            self.col_2_f.grid(column=2, row=0, sticky='n')
            self.col_3_f = self.Col3Frame(main_frame, bg=self['bg'])
            self.col_3_f.grid(column=3, row=0, padx=5, sticky='n')
            # tmp_f = Frame(self, bg='yellow')
            # tmp_f.pack(side='top', pady=5)
            # Button(tmp_f, text='1 up', command=self.col_1_up).grid(column=0, row=0)
            # Button(tmp_f, text='1 down', command=self.col_1_down).grid(column=0, row=1)
            # Button(tmp_f, text='2 up', command=self.col_2_up).grid(column=1, row=0)
            # Button(tmp_f, text='2 down', command=self.col_2_down).grid(column=1, row=1)
            # Button(tmp_f, text='3 up', command=self.col_3_up).grid(column=2, row=0)
            # Button(tmp_f, text='3 down', command=self.col_3_down).grid(column=2, row=1)
            # Button(tmp_f, text='4 up', command=self.col_4_up).grid(column=3, row=0)
            # Button(tmp_f, text='4 down', command=self.col_4_down).grid(column=3, row=1)
            # self.c_1 = 0
            # self.c_2 = 0
            # self.c_3 = 0
            # self.c_4 = 0

        # def col_1_up(self):
        #     self.c_1 += 1
        #     self.col_1_f.search_f.grid_forget()
        #     self.col_1_f.search_f.grid(column=0, row=1, pady=self.c_1, sticky='w')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_1_down(self):
        #     self.c_1 -= 1
        #     self.col_1_f.search_f.grid_forget()
        #     self.col_1_f.search_f.grid(column=0, row=1, pady=self.c_1, sticky='w')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_2_up(self):
        #     self.c_2 += 1
        #     self.col_1_f.c_plus_plus_btn.grid_forget()
        #     self.col_1_f.c_plus_plus_btn.grid(column=0, row=2, pady=self.c_2, sticky='n')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_2_down(self):
        #     self.c_2 -= 1
        #     self.col_1_f.c_plus_plus_btn.grid_forget()
        #     self.col_1_f.c_plus_plus_btn.grid(column=0, row=2, pady=self.c_2, sticky='n')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_3_up(self):
        #     self.c_3 += 1
        #     self.col_1_f.c_sharp_btn.grid_forget()
        #     self.col_1_f.c_sharp_btn.grid(column=0, row=3, pady=self.c_3, sticky='n')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_3_down(self):
        #     self.c_3 -= 1
        #     self.col_1_f.c_sharp_btn.grid_forget()
        #     self.col_1_f.c_sharp_btn.grid(column=0, row=3, pady=self.c_3, sticky='n')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_4_up(self):
        #     self.c_4 += 1
        #     self.col_1_f.python_btn.grid_forget()
        #     self.col_1_f.python_btn.grid(column=0, row=4, pady=self.c_4, sticky='n')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)
        #
        # def col_4_down(self):
        #     self.c_4 -= 1
        #     self.col_1_f.python_btn.grid_forget()
        #     self.col_1_f.python_btn.grid(column=0, row=4, pady=self.c_4, sticky='n')
        #     print(self.c_1, self.c_2, self.c_3, self.c_4)

        def get_search_entry(self):
            return self.col_1_f.search_entry.get()

        def set_open_manual_callback(self, cmd):
            self.col_0_f.open_manual_callback = cmd
            self.col_2_f.open_api_manual_callback = cmd

        def set_open_sample_code_callback(self, cmd):
            self.col_1_f.open_sample_code_callback = cmd

        def set_sample_code_table_callback(self, cmd):
            self.col_1_f.sample_code_table_callback = cmd

        def set_search_sample_code_callback(self, cmd):
            self.col_1_f.search_sample_code_callback = cmd

        def set_open_chr_explorer_callback(self, cmd):
            self.col_3_f.open_chr_explorer_callback = cmd

        def set_open_api_callback(self, cmd):
            self.col_2_f.open_api_callback = cmd

    class ConnectionPage(Frame):
        class TopLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.conn_test_button = RoundCornerButtonGR(master=self, size='m', width=250, height=20, bg=self['bg'],
                                                            text='[Connection Test] by Distance 1',
                                                            command=self._button_clicked)
                self.conn_test_button.pack(side='top', anchor='w')
                self._sample_counter_plot = BasicScatter(master=self, fig_size=(8, 3.7), tool_bar=False,
                                                         title='Sample Counter', x_label='Time(sec)',
                                                         y_label='Sample Count')
                self._sample_counter_plot.setup_plot()
                self._sample_counter_plot.pack(side='top')

                self._button_callback = None

            def set_btn_red(self):
                self.conn_test_button.set_button_color('r')

            def set_btn_greed(self):
                self.conn_test_button.set_button_color('g')

            def set_btn_normal(self):
                self.conn_test_button.set_button_color('n')

            def get_btn_color(self):
                return self.conn_test_button.get_button_color()

            def _button_clicked(self):
                if self._button_callback is not None:
                    self._button_callback()

            def set_btn_callback(self, cmd):
                self._button_callback = cmd

            def clear_btn_callback(self):
                self._button_callback = None

            def set_time_interval(self, val: int) -> None:
                self._sample_counter_plot.set_x_lim(left_val=0, right_val=val)

            def get_time_interval(self) -> int:
                return self._sample_counter_plot.get_x_lim()[1]

            def set_samples_y_limit(self, bottom_val: int, top_val: int) -> None:
                self._sample_counter_plot.set_y_lim(bottom_val, top_val)

            def get_samples_y_lim(self):
                return self._sample_counter_plot.get_y_lim()

            def set_samples_scatter(self, offsets):
                self._sample_counter_plot.set_scatter(offsets)

        class BottomLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._distance_plot = BasicScatter(master=self, fig_size=(8, 3.7), tool_bar=False, dot_size=1,
                                                   title='First Peak Signal', x_label='Time(sec)',
                                                   y_label='Distance 1 (um)')
                self._distance_plot.setup_plot()
                self._distance_plot.pack(side='top')

            def set_time_interval(self, val: int) -> None:
                self._distance_plot.set_x_lim(left_val=0, right_val=val)

            def get_time_interval(self) -> int:
                return self._distance_plot.get_x_lim()[1]

            def set_samples_y_limit(self, bottom_val: int, top_val: int) -> None:
                self._distance_plot.set_y_lim(bottom_val, top_val)

            def get_samples_y_lim(self) -> list:
                return self._distance_plot.get_y_lim()

            def set_samples_scatter(self, offsets):
                self._distance_plot.set_scatter(offsets)

        class TopRightFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.label_frame = Frame(self, bg=self['bg'])
                self.label_frame.pack(side='top', anchor='w', padx=4)
                Label(self.label_frame, text='How to modify the IP address?', bg='#ffffe1', anchor='w',
                      width=25).pack(side='left', fill='y')
                self.help_button = HelpButton(master=self.label_frame, command=self._help, bg='#ffffe1')
                self.help_button.pack(side='left', fill='y')
                img = Image.open('images/modify_ip_address.png')
                self._modify_ip_img = ImageTk.PhotoImage(img)
                self._img_size = img.size
                self.ip_entry = Entry(self, width=30)
                self.ip_entry.pack(side='top', anchor='w', padx=4, pady=5)
                self.ip_entry.insert('end', '192.168.170.2')
                # self.ip_mask_entry = Entry(self, width=30)
                # self.ip_mask_entry.pack(side='top', anchor='w', padx=4)
                # self.ip_mask_entry.insert('end', '255.255.255.0')
                self.modify_ip_button = RoundCornerButton(master=self, size='m', text='Modify IP address', width=220,
                                                          height=20, bg=self['bg'], command=self._modify_ip)
                self.modify_ip_button.pack(side='top', anchor='w')
                self.modify_ip_callback = None

            def _help(self):
                self.help_button.disable()
                ImageDescriptionWindow(master=self, image_en=self._modify_ip_img, title='Modify IP Address',
                                       size=[self._img_size[0], self._img_size[1]],
                                       close_command=self.help_button.enable)

            def _modify_ip(self):
                if self.modify_ip_callback is not None:
                    self.modify_ip_callback()

        class BottomRightFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.first_row_frame = Frame(self, bg=self['bg'])
                self.first_row_frame.pack(side='top', anchor='w')
                self.samples_entry = Entry(self.first_row_frame, width=10)
                self.samples_entry.pack(side='left', anchor='w', padx=5)
                self.samples_entry.insert('end', '2000')
                label_txt = 'Samples'
                Label(self.first_row_frame, text=label_txt, bg=self.first_row_frame['bg'],
                      width=len(label_txt)).pack(side='right', anchor='w')
                self.second_row_frame = Frame(self, bg='#daeffd')
                self.save_peak_bcrf_button = RoundCornerButton(master=self, width=140, height=50,
                                                               text='Save Peak Data\n(*.Bcrf)', bg=self['bg'])
                self.save_peak_bcrf_button.pack(side='left', anchor='w')
                self.save_peak_csv_button = RoundCornerButton(master=self, width=140, height=50,
                                                              text='Save Peak Data\n(*.csv)', bg=self['bg'])
                self.save_peak_csv_button.pack(side='right', anchor='w')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_frame = Frame(self, bg=self['bg'])
            main_frame.pack(side='top', fill='x', padx=30, pady=5)
            self.top_left_f = self.TopLeftFrame(main_frame, bg=self['bg'])
            self.top_left_f.grid(column=0, row=0)
            self.bottom_left_f = self.BottomLeftFrame(main_frame, bg=self['bg'])
            self.bottom_left_f.grid(column=0, row=1, pady=5)
            self.top_right_f = self.TopRightFrame(main_frame, bg=self['bg'])
            self.top_right_f.grid(column=1, row=0, padx=40, pady=5, sticky='nw')
            self.button_right_f = self.BottomRightFrame(main_frame, bg=self['bg'])
            self.button_right_f.grid(column=1, row=1, padx=40, pady=20, sticky='nw')

        def set_conn_page_ip(self, ip: str):
            self.top_right_f.ip_entry.delete(0, 'end')
            self.top_right_f.ip_entry.insert('end', ip)

        def get_conn_page_ip(self) -> str:
            return self.top_right_f.ip_entry.get()

        def set_conn_modify_ip_callback(self, cmd):
            self.top_right_f.modify_ip_callback = cmd

    class InitialPage(Frame):
        class TopLeftFrame(Frame):
            class FlashLabel(Label):
                def __init__(self, flash_bg, flash_fg, bg, fg, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self._after_id = None
                    self.color_index = 0
                    self.flash_bg, self.flash_fg = flash_bg, flash_fg
                    self.bg, self.fg = bg, fg

                    self.config(bg=self.flash_bg[0], fg=self.flash_fg[0])
                    self.bind("<Button-1>", lambda event: self.stop_flash(event))

                def start_flash(self):
                    self._flash_loop()

                def stop_flash(self, event):
                    if self._after_id:
                        self.after_cancel(self._after_id)
                        self._after_id = None
                        self.config(bg=self.bg, fg=self.fg)

                def _flash_loop(self):
                    self.color_index = 1 - self.color_index
                    self.config(bg=self.flash_bg[self.color_index], fg=self.flash_fg[self.color_index])
                    self._after_id = self.after(250, self._flash_loop)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self['bg'] = 'white'
                self.label = Label(self, text='Dark Reference', bg='#fffce1', anchor='w', width=49)
                self.label.grid(column=0, row=0, sticky='new')
                self._help_button = HelpButton(master=self, command=self._help)
                self._help_button.grid(column=0, row=0, sticky='ne', pady=1)
                self.sheet = Sheet(self, show_y_scrollbar=False, show_x_scrollbar=False, show_header=False,
                                   show_row_index=False, width=350, height=130, table_bg='white', frame_bg='white',
                                   top_left_bg='white')
                self.sheet.set_sheet_data(data=[['SEN', '?'], ['SHZ', '?'], ['LAI', '?'], ['Dark Type', '?']])
                self.sheet.readonly_rows([0, 1, 2, 3])
                self.sheet.enable_bindings(("single_select", "row_select", "column_width_resize", "arrowkeys",
                                            "right_click_popup_menu", "rc_select", "rc_insert_row", "copy", "cut",
                                            "paste", "delete", "undo", "edit_cell"))
                self.sheet.grid(column=0, row=1, sticky='ne')
                self.alarm_label_1 = self.FlashLabel(master=self, flash_bg=['red', 'green'],
                                                     flash_fg=['black', 'white'], bg=self['bg'], fg='black',
                                                     text='Alarm: Not clear in the measuring range')
                self.alarm_label_1.grid(column=0, row=2, sticky='nw', padx=15, pady=3)
                self.alarm_label_1.start_flash()
                self.alarm_label_2 = self.FlashLabel(master=self, flash_bg=['red', 'green'],
                                                     flash_fg=['black', 'white'], bg=self['bg'], fg='black',
                                                     text='Alarm: parameters not match (FDK)')
                self.alarm_label_2.grid(column=0, row=3, sticky='nw', padx=15, pady=3)
                self.alarm_label_2.start_flash()

            def set_sen(self, val):
                self.sheet.set_cell_data(r=0, c=1, value=val, redraw=True)
                self.sheet.MT.update()

            def get_sen(self):
                return self.sheet.get_cell_data(r=0, c=1)

            def clear_sen(self):
                self.sheet.set_cell_data(r=0, c=1, value='', redraw=True)
                self.sheet.MT.update()

            def set_shz(self, val):
                self.sheet.set_cell_data(r=1, c=1, value=val, redraw=True)

            def get_shz(self):
                return self.sheet.get_cell_data(r=1, c=1)

            def clear_shz(self):
                self.sheet.set_cell_data(r=1, c=1, value='', redraw=True)
                self.sheet.MT.update()

            def set_lai(self, val):
                self.sheet.set_cell_data(r=2, c=1, value=val, redraw=True)

            def get_lai(self):
                self.sheet.get_cell_data(r=2, c=1)

            def clear_lai(self):
                self.sheet.set_cell_data(r=2, c=1, value='', redraw=True)
                self.sheet.MT.update()

            def set_dark_type(self, val):
                self.sheet.set_cell_data(r=3, c=1, value=val, redraw=True)
                self.sheet.MT.update()

            def get_dark_type(self):
                return self.sheet.get_cell_data(r=3, c=1)

            def clear_dark_type(self):
                self.sheet.set_cell_data(r=3, c=1, value='', redraw=True)
                self.sheet.MT.update()

            def _help(self):
                self._help_button.disable()
                PowerPointWindow(master=self, title='About Dark Reference', close_command=self._help_button.enable,
                                 image_dir_en='images\\perform_dark_reference\\en',
                                 image_dir_cn='images\\perform_dark_reference\\cn')

        class BottomLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self['bg'] = 'white'
                self.label = Label(self, text='Probe Selection', bg='#fffce1', anchor='w', width=49)
                self.label.grid(column=0, row=0, sticky='new')

                self._help_button = HelpButton(master=self, command=self._help)
                self._help_button.grid(column=0, row=0, sticky='ne', pady=1)
                self.get_probes_info_button = RoundCornerButton(master=self, text='Get all probes information',
                                                                width=220, height=20, bg=self['bg'], size='m',
                                                                command=self._get_all_probes_info)
                self.get_probes_info_button.grid(column=0, row=1, sticky='nw', padx=5)
                self.info_textbox = Text(self, width=35, height=5, borderwidth=2, font='calibri 10')
                self.info_textbox.grid(column=0, row=2, sticky='nw', padx=5, pady=5)
                self.info_textbox.insert('end', 'All information about probes.\n')
                self.get_all_probes_info_callback = None

            def _get_all_probes_info(self):
                if self.get_all_probes_info_callback is not None:
                    self.get_all_probes_info_callback()

            def _help(self):
                self._help_button.disable()
                PowerPointWindow(master=self, title='Probe Selection', close_command=self._help_button.enable,
                                 image_dir_en='images\\probe_selection\\en', image_dir_cn='images\\probe_selection\\cn')

        class TopRightFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self['bg'] = 'white'
                self.label = Label(self, text='Measuring Mode', bg='#fffce1', anchor='w', width=49)
                self.label.grid(column=0, row=0, columnspan=2, sticky='new')

                self._help_button = HelpButton(master=self, command=self._help)
                self._help_button.grid(column=1, row=0, sticky='ne', pady=1)

                self.command_entry = Entry(self, width=10, borderwidth=2, disabledbackground='white',
                                           disabledforeground='black')
                self.command_entry.insert('end', '$MMD')
                self.command_entry.grid(column=0, row=1, sticky='nw', padx=10, pady=15)
                self.command_entry['state'] = 'disabled'
                self.chromatic_mode_button = RoundCornerButton(master=self, text='Chromatic Mode', width=180,
                                                               height=20, bg=self['bg'], size='m')
                self.chromatic_mode_button.grid(column=1, row=1, sticky='w', padx=10, pady=5)
                self.interferometric_mode_button = RoundCornerButton(master=self, text='Interferometric Mode',
                                                                     width=180, height=20, bg=self['bg'], size='m')
                self.interferometric_mode_button.grid(column=1, row=2, sticky='nw', padx=10)

            def _help(self):
                self._help_button.disable()
                PowerPointWindow(master=self, title='Measuring Mode', close_command=self._help_button.enable,
                                 image_dir_en='images\\measuring_mode\\en', image_dir_cn='images\\measuring_mode\\cn')

        class BottomRightFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self['bg'] = 'white'
                self.label = Label(self, text='Average', bg='#fffce1', anchor='w', width=49)
                self.label.grid(column=0, row=0, columnspan=2, sticky='new')

                self._help_button = HelpButton(master=self, command=self._help)
                self._help_button.grid(column=1, row=0, sticky='ne', pady=1)
                self.sheet = Sheet(self, show_y_scrollbar=False, show_x_scrollbar=False, show_header=False,
                                   show_row_index=False, width=280, height=75, table_bg='white', frame_bg='white',
                                   top_left_bg='white')
                self.sheet.set_sheet_data(data=[['AVD', '?'], ['AVS', '?']])
                self.sheet.readonly_columns([0])
                self.sheet.enable_bindings(("single_select", "row_select", "column_width_resize", "arrowkeys",
                                            "right_click_popup_menu", "rc_select", "rc_insert_row", "copy", "cut",
                                            "paste", "delete", "undo", "edit_cell"))
                self.sheet.grid(column=0, row=1, sticky='nw')
                self.set_button = RoundCornerButton(master=self, text='Set', width=70, height=20, bg=self['bg'],
                                                    size='s')
                self.set_button.grid(column=1, row=1, sticky='w', padx=10)
                Label(self, text='Set both to 1 in the beginning.', bg='white', anchor='w').grid(column=0, row=2,
                                                                                                 padx=20, sticky='nw')

            def set_avd(self, val):
                self.sheet.set_cell_data(r=0, c=1, value=val, redraw=True)
                self.sheet.MT.update()

            def get_avd(self):
                return self.sheet.get_cell_data(r=0, c=1)

            def clear_avd(self):
                self.sheet.set_cell_data(r=0, c=1, value='', redraw=True)
                self.sheet.MT.update()

            def set_avs(self, val):
                self.sheet.set_cell_data(r=1, c=1, value=val, redraw=True)
                self.sheet.MT.update()

            def get_avs(self):
                return self.sheet.get_cell_data(r=1, c=1)

            def clear_avs(self):
                self.sheet.set_cell_data(r=1, c=1, value='', redraw=True)
                self.sheet.MT.update()

            def _help(self):
                self._help_button.disable()
                PowerPointWindow(master=self, title='About Average', close_command=self._help_button.enable,
                                 image_dir_en='images\\average\\en', image_dir_cn='images\\average\\cn')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_f = Frame(self, bg=self['bg'])
            main_f.pack(side='top', fill='x', padx=30, pady=15)
            self.top_left_f = self.TopLeftFrame(main_f)
            self.top_left_f.grid(column=0, row=0, sticky='nw')
            self.bottom_left_f = self.BottomLeftFrame(main_f)
            self.bottom_left_f.grid(column=0, row=1, pady=20, sticky='nw')
            self.top_right_f = self.TopRightFrame(main_f)
            self.top_right_f.grid(column=1, row=0, padx=20, sticky='nw')
            self.bottom_right_f = self.BottomRightFrame(main_f)
            self.bottom_right_f.grid(column=1, row=1, padx=20, pady=20, sticky='nw')

        def set_initial_probe_info_textbox(self, val):
            self.bottom_left_f.info_textbox.delete('1.0', 'end')
            self.bottom_left_f.info_textbox.insert('end', val)

        def init_probe_info_textbox(self):
            self.bottom_left_f.info_textbox.delete('1.0', 'end')
            self.bottom_left_f.info_textbox.insert('end', 'All information about probes.\n')

        def set_get_all_probes_info_callback(self, cmd):
            self.bottom_left_f.get_all_probes_info_callback = cmd

    class FocusPage(Frame):
        class TopLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.label_frame = Frame(self, bg=self['bg'])
                self.label_frame.pack(side='top', anchor='w')
                Label(self.label_frame, text='<Focus>', bg='#ffffe1', anchor='w', width=47).pack(side='left', fill='y')
                self.help_button = HelpButton(master=self.label_frame, command=self._help, bg='#ffffe1')
                self.help_button.pack(side='left', fill='y')
                img = Image.open('images/how_to_focus.png')
                self._how_to_focus_img = ImageTk.PhotoImage(img)
                self._img_size = img.size

                second_row_f = Frame(self, bg=self['bg'])
                Label(second_row_f, text='Frequency ($SHZ)', justify='left',
                      bg=second_row_f['bg']).grid(column=0, row=0, sticky='nw')
                Label(second_row_f, text='LED ($LAI)', justify='left',
                      bg=second_row_f['bg']).grid(column=0, row=1, sticky='nw')
                self.focus_freq_entry = Entry(second_row_f, width=10, takefocus=False)
                self.focus_freq_entry.grid(column=1, row=0, sticky='nw', padx=10, pady=2)
                self.focus_freq_entry.insert('end', '2000')
                self.focus_led_entry = Entry(second_row_f, width=10, takefocus=False)
                self.focus_led_entry.grid(column=1, row=1, sticky='nw', padx=10, pady=2)
                self.focus_led_entry.insert('end', '100')
                RoundCornerButton(master=second_row_f, text='Set', width=60, height=40, takefocus=False,
                                  bg=self['bg'], command=self._set).grid(column=2, row=0, rowspan=2, sticky='nw')
                self.focus_set_callback = None
                second_row_f.pack(side='top', fill='x', pady=15)

                third_row_f = Frame(self, bg=self['bg'])
                Label(third_row_f, text='<Moving suggestion>', justify='left',
                      bg=third_row_f['bg']).pack(side='left', fill='y')
                self.move_str_var = StringVar()
                self.move_str_var.set('Go far away/close by ??um   ')
                self.focus_move_str_label = Label(third_row_f, textvariable=self.move_str_var, justify='left',
                                                  bg='white')
                self.focus_move_str_label.pack(side='left', fill='y', padx=10)
                third_row_f.pack(side='top', fill='x', pady=5)

                forth_row_f = Frame(self, bg='white')
                label_2_txt = 'Until sample is measured.\n' \
                              'Considering step height inside sample and warpage + tilt,\n' \
                              'place the sample at center of measuring range.'
                Label(forth_row_f, text=label_2_txt, justify='left', bg='white').pack(side='top', ipadx=5, anchor='w')
                forth_row_f.pack(side='top', fill='x', pady=15, ipady=10)

            def _help(self):
                self.help_button.disable()
                ImageDescriptionWindow(master=self, image_en=self._how_to_focus_img, title='How to focus?',
                                       size=[self._img_size[0], self._img_size[1]],
                                       close_command=self.help_button.enable)

            def _set(self):
                if self.focus_set_callback is not None:
                    self.focus_set_callback()

        class BottomLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                resized_img = Image.open('images/focus_fig.png').resize((400, 200))
                self.label_img = ImageTk.PhotoImage(resized_img)
                Label(self, image=self.label_img, bg=self['bg']).pack(side='top', anchor='w')

        class SpectrumFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                _frame_1 = Frame(self, bg=self['bg'])
                _frame_1.pack(side='top', anchor='w')
                self.spectrum_button = RoundCornerButtonGR(master=_frame_1, text='Start Spectrum',
                                                           green='G2', width=165, height=20, bg=self['bg'],
                                                           command=self._spectrum_switch)
                self.spectrum_button.pack(side='left')
                Label(_frame_1, bg=self['bg'], text='Channel:').pack(side='left')
                self.channel_entry = Entry(_frame_1, width=10)
                self.channel_entry.pack(side='left')
                self.channel_entry.bind('<Return>', self._entry_command)

                self.spectrum_plot = SpectrumPlot(master=self, fig_size=(7, 6), tool_bar=False,
                                                  title='Spectrum View')
                self.spectrum_plot.pack(side='top')
                self.spectrum_button_callback = None
                self.update_spectrum_callback = None
                self.focus_p_channel_entry_callback = None
                self._after_id = None

            def _spectrum_switch(self):
                if self.spectrum_button_callback is not None:
                    self.spectrum_button_callback()

            def _entry_command(self, e):
                if self.focus_p_channel_entry_callback is not None:
                    self.focus_p_channel_entry_callback()

            def update_focus_p_spectrum(self):
                if self.update_spectrum_callback is not None:
                    self.update_spectrum_callback()
                    self._after_id = self.after(200, self.update_focus_p_spectrum)

            def stop_focus_p_spectrum(self):
                if self._after_id:
                    self.after_cancel(self._after_id)
                    self._after_id = None

        class MultiChannelProfileView(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                _btn_frame = Frame(self, bg=self['bg'])
                _btn_frame.pack(side='top', anchor='w')
                self.prof_view_button = RoundCornerButtonGR(master=_btn_frame, text='Start Live',
                                                            green='G2', width=165, height=20, bg=self['bg'],
                                                            command=self._multichannel_profile_view_switch)
                self.prof_view_button.pack(side='left', anchor='w')
                self.multi_profile_view_option_ids_var = ctk.StringVar()
                self.id_option_menu = ctk.CTkOptionMenu(_btn_frame, command=self._id_option, values=[],
                                                        variable=self.multi_profile_view_option_ids_var)
                self.id_option_menu.configure(width=120, height=20)
                self.id_option_menu.configure(fg_color='white',
                                         button_color='#1594df',
                                         button_hover_color='#b9d1ea',
                                         text_color='black',
                                         text_color_disabled='light grey',
                                         dropdown_fg_color='white',
                                         dropdown_hover_color='#1594df',
                                         dropdown_text_color='black')
                self.id_option_menu.pack(side='left', anchor='w', padx=5)

                self.multi_prof_view = DynamicScatterPlot(self)
                self.multi_prof_view.pack(side='top')
                self.multi_prof_view_distance_y_lim = [0, 0]
                self.prof_view_button_callback = None
                self.update_prof_view_callback = None
                self._after_id = None

            def _id_option(self, id_str):
                self.multi_prof_view.update_label(id_str)
                self.update_y_lim_to_chart()

            def update_y_lim_to_chart(self):
                self.multi_prof_view.update_y_lim(self.multi_prof_view_distance_y_lim)

            def _multichannel_profile_view_switch(self):
                if self.prof_view_button_callback is not None:
                    self.prof_view_button_callback()

            def update_prof_view(self):
                if self.update_prof_view_callback is not None:
                    self.update_prof_view_callback()
                    self._after_id = self.after(200, self.update_prof_view)

            def stop_prof_view(self):
                if self._after_id:
                    self.after_cancel(self._after_id)
                    self._after_id = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_f = Frame(self, bg=self['bg'])
            main_f.pack(side='top', fill='x', padx=30, pady=15)
            self.focus_top_left_f = self.TopLeftFrame(main_f, bg=self['bg'])
            self.focus_top_left_f.grid(column=0, row=0, sticky='nw')
            self.focus_bottom_left_f = self.BottomLeftFrame(main_f, bg=self['bg'])
            self.focus_bottom_left_f.grid(column=0, row=1, sticky='nw')
            self.focus_spectrum_f = self.SpectrumFrame(main_f, bg=self['bg'])
            self.focus_spectrum_f.grid(column=1, row=0, rowspan=2, sticky='nw', padx=20)
            self.multi_prof_view_f = self.MultiChannelProfileView(main_f, bg=self['bg'])
            self.multi_prof_view_f.grid(column=2, row=0, rowspan=2, sticky='nw')

        def set_focus_move_str(self, direction: int, distance: int = 0) -> None:
            """
            :param direction: 0: Position is good
                              1: Go far away by distance
                             -1: Get closer by distance
                             -2: Go far away/close by ??um
            :param distance: Integer distance to be display
            """
            move_str = ''
            if direction == 1 or direction == -1 or direction == -2:
                if self.focus_top_left_f.focus_move_str_label['bg'] == GREEN:
                    self.focus_top_left_f.focus_move_str_label['bg'] = 'white'
                if direction == 1:
                    move_str = 'Go far away by {}um   '.format(distance)
                elif direction == -1:
                    move_str = 'Get closer by {}um   '.format(distance)
                else:
                    move_str = 'Go far away/close by ??um   '
            elif direction == 0:
                if self.focus_top_left_f.focus_move_str_label['bg'] == 'white':
                    self.focus_top_left_f.focus_move_str_label['bg'] = GREEN
                move_str = 'Position is good'
            self.focus_top_left_f.move_str_var.set(move_str)

        def set_focus_freq(self, value):
            self.focus_top_left_f.focus_freq_entry.delete(0, 'end')
            self.focus_top_left_f.focus_freq_entry.insert('end', value)

        def get_focus_freq(self):
            return self.focus_top_left_f.focus_freq_entry.get()

        def set_focus_led(self, val):
            self.focus_top_left_f.focus_led_entry.delete(0, 'end')
            self.focus_top_left_f.focus_led_entry.insert('end', val)

        def get_focus_led(self):
            return self.focus_top_left_f.focus_led_entry.get()

        def update_focus_spectrum(self, data):
            self.focus_spectrum_f.spectrum_plot.plot(data)

        def set_focus_spectrum_btn_green(self):
            self.focus_spectrum_f.spectrum_button.set_button_color('g')
            self.focus_spectrum_f.spectrum_button['text'] = 'Stop Spectrum'

        def set_focus_spectrum_btn_normal(self):
            self.focus_spectrum_f.spectrum_button.set_button_color('n')
            self.focus_spectrum_f.spectrum_button['text'] = 'Start Spectrum'

        def get_focus_spectrum_btn_color(self):
            return self.focus_spectrum_f.spectrum_button.get_button_color()

        def set_focus_set_callback(self, cmd):
            self.focus_top_left_f.focus_set_callback = cmd

        def set_focus_p_spectrum_button_callback(self, cmd):
            self.focus_spectrum_f.spectrum_button_callback = cmd

        def set_focus_p_channel_entry_callback(self, cmd):
            self.focus_spectrum_f.focus_p_channel_entry_callback = cmd

        def set_focus_spectrum_channel(self, val):
            self.focus_spectrum_f.channel_entry.delete(0, 'end')
            self.focus_spectrum_f.channel_entry.insert('end', val)

        def get_focus_spectrum_channel(self):
            return self.focus_spectrum_f.channel_entry.get()

        def set_update_spectrum_callback(self, cmd):
            self.focus_spectrum_f.update_spectrum_callback = cmd

        def set_multichannel_profile_view_btn_green(self):
            self.multi_prof_view_f.prof_view_button.set_button_color('g')
            self.multi_prof_view_f.prof_view_button['text'] = 'Stop Live'

        def set_multichannel_profile_view_btn_normal(self):
            self.multi_prof_view_f.prof_view_button.set_button_color('n')
            self.multi_prof_view_f.prof_view_button['text'] = 'Start Live'

        def get_multichannel_profile_view_btn_color(self):
            return self.multi_prof_view_f.prof_view_button.get_button_color()

        def set_multichannel_profile_view_id_list(self, id_list: list):
            self.multi_prof_view_f.id_option_menu.configure(values=id_list)

        def get_multichannel_profile_view_id_list(self) -> list:
            return self.multi_prof_view_f.id_option_menu.cget('values')

        def set_multichannel_profile_view_id(self, id_str: str):
            self.multi_prof_view_f.multi_profile_view_option_ids_var.set(id_str)

        def get_multichannel_profile_view_id(self) -> str:
            return self.multi_prof_view_f.multi_profile_view_option_ids_var.get()

        def set_multichannel_profile_view_btn_callback(self, cmd):
            self.multi_prof_view_f.prof_view_button_callback = cmd

        def set_update_multichannel_profile_view_callback(self, cmd):
            self.multi_prof_view_f.update_prof_view_callback = cmd

        def update_multichannel_profile_view(self, data, autoscale_y=False):
            self.multi_prof_view_f.multi_prof_view.update_plot(data, autoscale_y)

        def update_multichannel_profile_view_distance_y_lim(self, min_int, max_int):
            self.multi_prof_view_f.multi_prof_view_distance_y_lim = [min_int, max_int]

    class TriggerTestPage(Frame):
        class TopRowFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.QUICK = 'quick start'
                self.TIMING = 'timing diagram'
                self.COMMAND = 'command list'
                self.DISABLE = 'disable'
                self.NORMAL = 'normal'
                self.quick_start_button = RoundCornerButton(master=self, text='Quick Start', width=100, height=20,
                                                            bg=self['bg'], size='m', command=self._quick_start)
                self.quick_start_button.pack(side='left', padx=5)
                self.timing_diagram_button = RoundCornerButton(master=self, text='Encoder Timing Diagram', width=170,
                                                               height=20, bg=self['bg'], size='m',
                                                               command=self._timing_diagram)
                self.timing_diagram_button.pack(side='left', padx=5)

                self.command_list_button = RoundCornerButton(master=self, text='Command List', width=130, height=20,
                                                             bg=self['bg'], size='m', command=self._command_list)
                self.command_list_button.pack(side='left', padx=5)

                img = Image.open('images/encoder_timing_diagram.png').resize((1083, 782))
                self.timing_diagram_img_size = img.size
                self.timing_diagram_img = ImageTk.PhotoImage(img)
                img = Image.open('images/encoder_command_list.png').resize((1074, 512))
                self.command_list_img_size = img.size
                self.command_list_img = ImageTk.PhotoImage(img)

            def button_state(self, btn, state):
                if btn == self.QUICK:
                    self.quick_start_button['state'] = state
                elif btn == self.TIMING:
                    self.timing_diagram_button['state'] = state
                elif btn == self.COMMAND:
                    self.command_list_button['state'] = state

            def _quick_start(self):
                self.button_state(btn=self.QUICK, state=self.DISABLE)
                PowerPointWindow(master=self, title='Quick Start',
                                 close_command=lambda: self.button_state(btn=self.QUICK, state=self.NORMAL),
                                 image_dir_en='images/quick_start/en', image_dir_cn='images/quick_start/cn')

            def _timing_diagram(self):
                self.button_state(btn=self.TIMING, state=self.DISABLE)
                ImageDescriptionWindow(master=self, image_en=self.timing_diagram_img, title='Timing Diagram',
                                       size=[self.timing_diagram_img_size[0], self.timing_diagram_img_size[1]],
                                       close_command=lambda x=self.TIMING, y=self.NORMAL: self.button_state(x, y))

            def _command_list(self):
                self.button_state(btn=self.COMMAND, state=self.DISABLE)
                ImageDescriptionWindow(master=self, image_en=self.command_list_img, title='Command List',
                                       size=[self.command_list_img_size[0], self.command_list_img_size[1]],
                                       close_command=lambda x=self.COMMAND, y=self.NORMAL: self.button_state(x, y))

        class TopLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                Label(self, text='Encoder Trigger Counter', bg='#ffffe1', anchor='w', width=56).pack(side='top',
                                                                                                     anchor='w',
                                                                                                     fill='x')

                second_row_frame = Frame(self, bg=self['bg'])
                second_row_frame.pack(side='top', anchor='w')
                Label(second_row_frame, text='Encoder X', anchor='w', width=20, bg=self['bg']).grid(column=0, row=0,
                                                                                                    padx=3, sticky='nw')
                Label(second_row_frame, text='Encoder Y', anchor='w', width=20, bg=self['bg']).grid(column=0, row=1,
                                                                                                    padx=3, sticky='nw')
                Label(second_row_frame, text='Encoder Z', anchor='w', width=20, bg=self['bg']).grid(column=0, row=2,
                                                                                                    padx=3, sticky='nw')
                Label(second_row_frame, text='Sample Counter', anchor='w', width=20,
                      bg=self['bg']).grid(column=0, row=3, padx=3, sticky='nw')
                self.encoder_x_entry = Entry(second_row_frame, width=15, readonlybackground='white', state='readonly')
                self.encoder_x_entry.grid(column=1, row=0)
                self.encoder_y_entry = Entry(second_row_frame, width=15, readonlybackground='white', state='readonly')
                self.encoder_y_entry.grid(column=1, row=1)
                self.encoder_z_entry = Entry(second_row_frame, width=15, readonlybackground='white', state='readonly')
                self.encoder_z_entry.grid(column=1, row=2)
                self.sample_counter_entry = Entry(second_row_frame, width=15, readonlybackground='white',
                                                  state='readonly')
                self.sample_counter_entry.grid(column=1, row=3)
                btn_frame = Frame(second_row_frame, bg=self['bg'])
                btn_frame.grid(column=2, row=0, sticky='nw', ipadx=37)
                self.order_encoder_button = RoundCornerButton(master=btn_frame, text='Read Encoder', width=130,
                                                              height=20, bg=self['bg'], size='m',
                                                              command=self._order_encoder)
                self.order_encoder_button.pack(side='top', anchor='e')
                self._order_encoder_callback = None

            def _order_encoder(self):
                if self._order_encoder_callback is not None:
                    self._order_encoder_callback()

        class BottomLeftFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                first_row_f = Frame(self, bg=self['bg'])
                first_row_f.pack(side='top', anchor='w', fill='x')
                Label(first_row_f, text='Trigger Lost Tracker', bg='#ffffe1', anchor='w',
                      width=66).grid(column=0, row=0, sticky='new')
                btn_f = Frame(first_row_f, bg=self['bg'])
                btn_f.grid(column=0, row=0, sticky='ne')
                self.note_button = NoteButton(master=btn_f, command=self._ppt)
                self.note_button.grid(column=0, row=0, sticky='ne', pady=1)

                second_row_f = Frame(self, bg=self['bg'])
                second_row_f.pack(side='top', anchor='w')
                Label(second_row_f, text='Trigger count should be', anchor='w', width=20,
                      bg=self['bg']).grid(column=0, row=0, padx=3, sticky='nw')
                Label(second_row_f, text='Trigger happened', anchor='w', width=20,
                      bg=self['bg']).grid(column=0, row=1, padx=3, sticky='nw')
                self.trigger_count_entry = Entry(second_row_f, width=15, readonlybackground='white',
                                                 state='readonly')
                self.trigger_count_entry.grid(column=1, row=0)
                self.trigger_happened_entry = Entry(second_row_f, width=15, readonlybackground='white',
                                                    state='readonly')
                self.trigger_happened_entry.grid(column=1, row=1)
                btn_frame = Frame(second_row_f, bg=self['bg'])
                btn_frame.grid(column=2, row=0, sticky='nw', ipadx=20)
                self.check_trigger_button = RoundCornerButtonGR(master=btn_frame, text='Start Check Trigger',
                                                                green='G2', width=165, height=20, bg=self['bg'],
                                                                command=self._check_trigger)
                self.check_trigger_button.pack(side='top', anchor='e')

                third_row_frame = Frame(self, bg=self['bg'])
                third_row_frame.pack(side='top', anchor='w')
                Label(third_row_frame, text='Trigger lost information', anchor='nw', width=20,
                      bg=self['bg']).grid(column=0, row=0, padx=3, sticky='nw')
                self.info_textbox = Text(third_row_frame, width=42, height=5, borderwidth=2, font='calibri 10',
                                         state='disabled')
                self.info_textbox.tag_config('warning', foreground='red')
                self.info_textbox.grid(column=1, row=0, sticky='nwe', pady=5)
                self.check_trigger_callback = None

            def _ppt(self):
                self.note_button.disable()
                PowerPointWindow(master=self, title='Trigger Lost Note', close_command=self.note_button.enable,
                                 image_dir_en='images/trigger_lost_note/en',
                                 image_dir_cn='images/trigger_lost_note/cn')

            def _check_trigger(self):
                if self.check_trigger_callback is not None:
                    self.check_trigger_callback()

        class RightFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.CTN = 0
                self.TRG = 1
                self.TRE = 2
                Label(self, text='Encoder Trigger Setting', bg='#ffffe1', anchor='w',
                      width=56).pack(side='top', anchor='w', fill='x')

                _second_row_frame = Frame(self, bg=self['bg'])
                _second_row_frame.pack(side='top', anchor='w', ipadx=40)
                _left_f = Frame(_second_row_frame, bg=self['bg'])
                _left_f.pack(side='left', anchor='n', padx=5, pady=5)
                _options = (('Set to free run mode', self.CTN),
                            ('Enter wait for trigger', self.TRG),
                            ('Set to trigger each mode', self.TRE))
                self._selected_option = IntVar()
                self._selection_buffer = IntVar()
                for index, option in enumerate(_options):
                    r = ttk.Radiobutton(_left_f, text=option[0], value=option[1], variable=self._selected_option,
                                        takefocus=False, command=self._trigger_mode_sel)
                    r.grid(column=0, row=index, padx=10, sticky='w')

                self._software_trigger_button = RoundCornerButton(master=_second_row_frame, text='Software Trigger',
                                                                  size='m', width=140, height=20, bg=self['bg'],
                                                                  command=self._software_trig)
                self._software_trigger_button.pack(side='top', anchor='e')

                # region Middle Frame
                self._middle_frame = Frame(self, bg=self['bg'])
                self._middle_frame.pack(side='top', anchor='w', pady=5)
                s = ttk.Style()
                s.configure('blue.TCheckbutton', background=self['bg'])
                self._use_encoder_trigger_checkbox_var = IntVar()
                self._use_encoder_trigger_checkbutton = ttk.Checkbutton(self._middle_frame, style='blue.TCheckbutton',
                                                                        text='Use Encoder Trigger', takefocus=False,
                                                                        variable=self._use_encoder_trigger_checkbox_var,
                                                                        command=self._use_encoder_trigger_on_click,
                                                                        onvalue=1, offvalue=0)
                self._use_encoder_trigger_checkbutton.grid(column=0, row=0, columnspan=2, sticky='nw', padx=25)
                self._endless_trigger_checkbox_var = IntVar()
                self._endless_trigger_checkbutton = ttk.Checkbutton(self._middle_frame, text='Endless Trigger',
                                                                    variable=self._endless_trigger_checkbox_var,
                                                                    takefocus=False, style='blue.TCheckbutton',
                                                                    command=self._endless_trigger_on_click,
                                                                    onvalue=1, offvalue=0)
                self._endless_trigger_checkbutton.grid(column=0, row=1, columnspan=2, sticky='nw', padx=35, pady=10)
                self._trigger_on_return_checkbox_var = IntVar()
                self._trigger_on_return_checkbutton = ttk.Checkbutton(self._middle_frame, text='Trigger on Return Move',
                                                                      variable=self._trigger_on_return_checkbox_var,
                                                                      takefocus=False, style='blue.TCheckbutton',
                                                                      command=self._trigger_on_return_on_click,
                                                                      onvalue=1, offvalue=0)
                self._trigger_on_return_checkbutton.grid(column=1, row=1, columnspan=2, sticky='nw', padx=28, pady=10)
                Label(self._middle_frame, text='Axis:', anchor='w', width=10,
                      bg=self['bg']).grid(column=0, row=2, padx=33, sticky='nw')
                Label(self._middle_frame, text='Start Pos:', anchor='w', width=10,
                      bg=self['bg']).grid(column=0, row=3, padx=33, sticky='nw')
                Label(self._middle_frame, text='Interval:', anchor='w', width=10,
                      bg=self['bg']).grid(column=0, row=4, padx=33, sticky='nw')
                Label(self._middle_frame, text='Stop Pos:', anchor='w', width=10,
                      bg=self['bg']).grid(column=0, row=5, padx=33, sticky='nw')
                self._selected_axis = StringVar()
                s.configure("TCombobox", fieldbackground="white", background="white")
                self._axis_combobox = ttk.Combobox(self._middle_frame, textvariable=self._selected_axis, width=13,
                                                   height=20, state='readonly', values=['x', 'y', 'z', 'u', 'v'])
                self._axis_combobox.bind("<<ComboboxSelected>>", self._axis_sel)
                self._selected_axis.set(self._axis_combobox['values'][0])
                self._axis_combobox.grid(column=1, row=2, sticky='nw', padx=30)
                self._start_pos_entry = Entry(self._middle_frame, width=15)
                self._start_pos_entry.bind('<Return>', self._start_pos_enter)
                self._start_pos_entry.insert('end', '0')
                self._start_pos_entry.grid(column=1, row=3, sticky='nw', padx=30)
                self._interval_entry = Entry(self._middle_frame, width=15)
                self._interval_entry.bind('<Return>', self._interval_enter)
                self._interval_entry.grid(column=1, row=4, sticky='nw', padx=30)
                self._interval_entry.insert('end', '10')
                self._stop_pos_entry = Entry(self._middle_frame, width=15)
                self._stop_pos_entry.bind('<Return>', self._stop_pos_enter)
                self._stop_pos_entry.grid(column=1, row=5, sticky='nw', padx=30)
                self._stop_pos_entry.insert('end', '1000')
                # endregion

                # region Bottom Frame
                self._bottom_frame = Frame(self, bg=self['bg'])
                self._bottom_frame.pack(side='top', anchor='w', padx=25, pady=5)
                self._set_trig_pos_button = RoundCornerButton(master=self._bottom_frame, width=200, height=20,
                                                              text='Set Trigger Axis Encoder Position:', size='m',
                                                              bg=self['bg'], command=self._set_trig_pos)
                self._set_trig_pos_button.pack(side='left', anchor='n', padx=5)
                self._encoder_position_entry = Entry(self._bottom_frame, width=15)
                self._encoder_position_entry.insert('end', '-20')
                self._encoder_position_entry.pack(side='right', anchor='n', pady=2)
                # endregion

                self.set_tt_trig_mode_value(self.CTN)

                self._trig_mode_sel_callback = None
                self._software_trig_callback = None
                self._use_encoder_trigger_callback = None
                self._endless_trigger_callback = None
                self._trigger_on_return_callback = None
                self._axis_sel_callback = None
                self._start_pos_callback = None
                self._interval_callback = None
                self._stop_pos_callback = None
                self._set_trig_pos_callback = None

            def set_tt_trig_mode_value(self, val: int):
                self._selected_option.set(val)
                self._selection_buffer.set(val)
                self.tt_check_trigger_each_widgets_state()

            def get_tt_trig_mode_value(self) -> int:
                return self._selected_option.get()

            def set_use_encoder_trig(self, val: int):
                self._use_encoder_trigger_checkbox_var.set(val)

            def get_use_encoder_trig(self) -> int:
                return self._use_encoder_trigger_checkbox_var.get()

            def set_endless_trig(self, val: int):
                self._endless_trigger_checkbox_var.set(val)

            def get_endless_trig(self) -> int:
                return self._endless_trigger_checkbox_var.get()

            def set_tt_trig_on_return(self, val: int):
                self._trigger_on_return_checkbox_var.set(val)

            def get_tt_trig_on_return(self) -> int:
                return self._trigger_on_return_checkbox_var.get()

            def set_tt_axis(self, val: str):
                self._selected_axis.set(val)

            def get_tt_axis(self) -> str:
                return self._selected_axis.get()

            def set_start_pos(self, val: str):
                if self._start_pos_entry['state'] == 'disabled':
                    self._start_pos_entry['state'] = 'normal'
                    self._start_pos_entry.delete(0, 'end')
                    self._start_pos_entry.insert('end', val)
                    self._start_pos_entry['state'] = 'disabled'
                else:
                    self._start_pos_entry.delete(0, 'end')
                    self._start_pos_entry.insert('end', val)

            def get_start_pos(self) -> str:
                return self._start_pos_entry.get()

            def set_interval(self, val: str):
                if self._interval_entry['state'] == 'disabled':
                    self._interval_entry['state'] = 'normal'
                    self._interval_entry.delete(0, 'end')
                    self._interval_entry.insert('end', val)
                    self._interval_entry['state'] = 'disabled'
                else:
                    self._interval_entry.delete(0, 'end')
                    self._interval_entry.insert('end', val)

            def get_interval(self) -> str:
                return self._interval_entry.get()

            def set_stop_pos(self, val: str):
                if self._stop_pos_entry['state'] == 'disabled':
                    self._stop_pos_entry['state'] = 'normal'
                    self._stop_pos_entry.delete(0, 'end')
                    self._stop_pos_entry.insert('end', val)
                    self._stop_pos_entry['state'] = 'disabled'
                else:
                    self._stop_pos_entry.delete(0, 'end')
                    self._stop_pos_entry.insert('end', val)

            def get_stop_pos(self) -> str:
                return self._stop_pos_entry.get()

            def get_trig_axis_encoder_pos(self):
                return self._encoder_position_entry.get()

            def tt_check_trigger_each_widgets_state(self):
                trig_mode = self.get_tt_trig_mode_value()
                use_encoder_trig = self._use_encoder_trigger_checkbox_var.get()
                if trig_mode == self.TRE:
                    # print('use_encoder_trig = ', use_encoder_trig)
                    if use_encoder_trig == 1:
                        for child in self._middle_frame.children.values():
                            child['state'] = 'normal'
                        for child in self._bottom_frame.children.values():
                            child['state'] = 'normal'
                        self._axis_combobox['state'] = 'readonly'
                    else:
                        for child in self._middle_frame.children.values():
                            child['state'] = 'disable'
                        for child in self._bottom_frame.children.values():
                            child['state'] = 'disable'
                    self._use_encoder_trigger_checkbutton['state'] = 'normal'
                elif trig_mode == self.CTN or trig_mode == self.TRG:
                    for child in self._middle_frame.children.values():
                        child['state'] = 'disable'
                    for child in self._bottom_frame.children.values():
                        child['state'] = 'disable'

            def _trigger_mode_sel(self):
                if self._selection_buffer.get() != self._selected_option.get():
                    self.tt_check_trigger_each_widgets_state()
                    self._selection_buffer.set(self._selected_option.get())
                    if self._trig_mode_sel_callback is not None:
                        self._trig_mode_sel_callback()

            def _software_trig(self):
                if self._software_trig_callback is not None:
                    self._software_trig_callback()

            def _use_encoder_trigger_on_click(self):
                self.tt_check_trigger_each_widgets_state()
                if self._use_encoder_trigger_callback is not None:
                    self._use_encoder_trigger_callback()

            def _endless_trigger_on_click(self):
                if self._endless_trigger_callback is not None:
                    self._endless_trigger_callback()

            def _trigger_on_return_on_click(self):
                if self._trigger_on_return_callback is not None:
                    self._trigger_on_return_callback()

            def _axis_sel(self, e):
                if self._axis_sel_callback is not None:
                    self._axis_sel_callback()

            def _start_pos_enter(self, e):
                if self._start_pos_callback is not None:
                    self._start_pos_callback()

            def _interval_enter(self, e):
                if self._interval_callback is not None:
                    self._interval_callback()

            def _stop_pos_enter(self, e):
                if self._stop_pos_callback is not None:
                    self._stop_pos_callback()

            def _set_trig_pos(self):
                if self._set_trig_pos_callback is not None:
                    self._set_trig_pos_callback()

            def set_tt_trig_mode_sel_callback(self, cmd):
                self._trig_mode_sel_callback = cmd

            def clear_tt_trig_mode_sel_callback(self):
                self._trig_mode_sel_callback = None

            def set_software_trig_callback(self, cmd):
                self._software_trig_callback = cmd

            def clear_software_trig_callback(self):
                self._software_trig_callback = None

            def set_use_encoder_trig_callback(self, cmd):
                self._use_encoder_trigger_callback = cmd

            def clear_use_encoder_trig_callback(self):
                self._use_encoder_trigger_callback = None

            def set_endless_trig_callback(self, cmd):
                self._endless_trigger_callback = cmd

            def clear_endless_trig_callback(self):
                self._endless_trigger_callback = None

            def set_tt_trig_on_return_callback(self, cmd):
                self._trigger_on_return_callback = cmd

            def clear_tt_trig_on_return_callback(self):
                self._trigger_on_return_callback = None

            def set_axis_sel_callback(self, cmd):
                self._axis_sel_callback = cmd

            def clear_axis_sel_callback(self):
                self._axis_sel_callback = None

            def set_start_pos_callback(self, cmd):
                self._start_pos_callback = cmd

            def clear_start_pos_callback(self):
                self._start_pos_callback = None

            def set_interval_callback(self, cmd):
                self._interval_callback = cmd

            def clear_interval_callback(self):
                self._interval_callback = None

            def set_stop_pos_callback(self, cmd):
                self._stop_pos_callback = cmd

            def clear_stop_pos_callback(self):
                self._stop_pos_callback = None

            def set_set_trig_pos_callback(self, cmd):
                self._set_trig_pos_callback = cmd

            def clear_set_trig_pos_callback(self):
                self._set_trig_pos_callback = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_frame = Frame(self, bg=self['bg'])
            main_frame.pack(side='top', fill='x', padx=30, pady=15)
            self.top_row_f = self.TopRowFrame(main_frame, bg=self['bg'])
            self.top_row_f.grid(column=0, row=0, columnspan=2, sticky='nw')
            self.top_left_f = self.TopLeftFrame(main_frame, bg=self['bg'])
            self.top_left_f.grid(column=0, row=1, sticky='nw', pady=15)
            self.bottom_left_f = self.BottomLeftFrame(main_frame, bg=self['bg'])
            self.bottom_left_f.grid(column=0, row=2, sticky='nw', pady=15)
            self.right_f = self.RightFrame(main_frame, bg=self['bg'])
            self.right_f.grid(column=1, row=1, rowspan=2, sticky='nw', padx=15, pady=15)
            self._update_callback = None
            self._after_id = None

        """ Trigger Test - Top left Frame """

        # region
        def set_encoder_x_value(self, val: str):
            self.top_left_f.encoder_x_entry['state'] = 'normal'
            self.top_left_f.encoder_x_entry.delete(0, 'end')
            self.top_left_f.encoder_x_entry.insert('end', val)
            self.top_left_f.encoder_x_entry['state'] = 'readonly'

        def clear_encoder_x_value(self):
            self.top_left_f.encoder_x_entry['state'] = 'normal'
            self.top_left_f.encoder_x_entry.delete(0, 'end')
            self.top_left_f.encoder_x_entry['state'] = 'readonly'

        def set_encoder_y_value(self, val: str):
            self.top_left_f.encoder_y_entry['state'] = 'normal'
            self.top_left_f.encoder_y_entry.delete(0, 'end')
            self.top_left_f.encoder_y_entry.insert('end', val)
            self.top_left_f.encoder_y_entry['state'] = 'readonly'

        def clear_encoder_y_value(self):
            self.top_left_f.encoder_y_entry['state'] = 'normal'
            self.top_left_f.encoder_y_entry.delete(0, 'end')
            self.top_left_f.encoder_y_entry['state'] = 'readonly'

        def set_encoder_z_value(self, val: str):
            self.top_left_f.encoder_z_entry['state'] = 'normal'
            self.top_left_f.encoder_z_entry.delete(0, 'end')
            self.top_left_f.encoder_z_entry.insert('end', val)
            self.top_left_f.encoder_z_entry['state'] = 'readonly'

        def clear_encoder_z_value(self):
            self.top_left_f.encoder_z_entry['state'] = 'normal'
            self.top_left_f.encoder_z_entry.delete(0, 'end')
            self.top_left_f.encoder_z_entry['state'] = 'readonly'

        def set_sample_counter_value(self, val: str):
            self.top_left_f.sample_counter_entry['state'] = 'normal'
            self.top_left_f.sample_counter_entry.delete(0, 'end')
            self.top_left_f.sample_counter_entry.insert('end', val)
            self.top_left_f.sample_counter_entry['state'] = 'readonly'

        def clear_sample_counter_value(self):
            self.top_left_f.sample_counter_entry['state'] = 'normal'
            self.top_left_f.sample_counter_entry.delete(0, 'end')
            self.top_left_f.sample_counter_entry['state'] = 'readonly'

        def set_order_encoder_callback(self, cmd):
            self.top_left_f._order_encoder_callback = cmd

        def clear_order_encoder_callback(self):
            self.top_left_f._order_encoder_callback = None

        def set_tt_update_callback(self, cmd):
            self._update_callback = cmd

        def clear_update_callback(self):
            self._update_callback = None

        # Update sample counter at the top left frame
        def update_data(self):
            if self._update_callback is not None:
                self._update_callback()
                self._after_id = self.after(10, self.update_data)

        def stop_update_data(self):
            if self._after_id:
                self.after_cancel(self._after_id)
                self._after_id = None

        # endregion
        """ Trigger Test - Bottom left Frame """

        # region
        def set_trigger_count(self, val: str):
            self.bottom_left_f.trigger_count_entry['state'] = 'normal'
            self.bottom_left_f.trigger_count_entry.delete(0, 'end')
            self.bottom_left_f.trigger_count_entry.insert('end', val)
            self.bottom_left_f.trigger_count_entry['state'] = 'readonly'

        def clear_trigger_count(self):
            self.bottom_left_f.trigger_count_entry['state'] = 'normal'
            self.bottom_left_f.trigger_count_entry.delete(0, 'end')
            self.bottom_left_f.trigger_count_entry['state'] = 'readonly'

        def set_trigger_happened(self, val: str):
            self.bottom_left_f.trigger_happened_entry['state'] = 'normal'
            self.bottom_left_f.trigger_happened_entry.delete(0, 'end')
            self.bottom_left_f.trigger_happened_entry.insert('end', val)
            self.bottom_left_f.trigger_happened_entry['state'] = 'readonly'

        def get_trigger_happened(self) -> str:
            return self.bottom_left_f.trigger_happened_entry.get()

        def clear_trigger_happened(self):
            self.bottom_left_f.trigger_happened_entry['state'] = 'normal'
            self.bottom_left_f.trigger_happened_entry.delete(0, 'end')
            self.bottom_left_f.trigger_happened_entry['state'] = 'readonly'

        def set_trigger_lost_info(self, val: str, warning=False):
            self.bottom_left_f.info_textbox['state'] = 'normal'
            if warning:
                self.bottom_left_f.info_textbox.insert('end', val, 'warning')
            else:
                self.bottom_left_f.info_textbox.insert('end', val)
            self.bottom_left_f.info_textbox['state'] = 'disabled'

        def clear_trigger_lost_info(self):
            self.bottom_left_f.info_textbox['state'] = 'normal'
            self.bottom_left_f.info_textbox.delete('1.0', 'end')
            self.bottom_left_f.info_textbox['state'] = 'disabled'

        def set_check_trigger_callback(self, cmd):
            self.bottom_left_f.check_trigger_callback = cmd

        def clear_check_trigger_callback(self):
            self.bottom_left_f.check_trigger_callback = None

        def set_check_check_trigger_btn_text(self, val: str):
            self.bottom_left_f.check_trigger_button['text'] = val

        def set_check_check_trigger_btn_green(self):
            self.bottom_left_f.check_trigger_button.set_button_color('g')

        def set_check_check_trigger_btn_red(self):
            self.bottom_left_f.check_trigger_button.set_button_color('r')

        def set_check_check_trigger_btn_normal(self):
            self.bottom_left_f.check_trigger_button.set_button_color('n')

        def get_check_check_trigger_btn_color(self) -> str:
            return self.bottom_left_f.check_trigger_button.get_button_color()
        # endregion

    class TriggerScanPage(Frame):
        class LeftFrame(Frame):
            class FirstRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    Label(self, text='Sample Counter (id:83)', bg=self['bg']).grid(column=0, row=0, pady=5, sticky='nw')
                    Label(self, text='Distance 1 Int16 (id:16640)', bg=self['bg']).grid(column=0, row=1, pady=5,
                                                                                        sticky='nw')
                    self.encoder_label_str = StringVar()
                    self.encoder_label_str.set('Encoder X (id: 65)')
                    Label(self, textvariable=self.encoder_label_str, bg=self['bg']).grid(column=0, row=2, pady=5,
                                                                                         sticky='nw')
                    self.sample_counter_progressbar = ttk.Progressbar(self, length=200)
                    self.sample_counter_progressbar.grid(column=1, row=0, padx=10, pady=7, sticky='nw')
                    self.distance_progressbar = ttk.Progressbar(self, length=200)
                    self.distance_progressbar.grid(column=1, row=1, padx=10, pady=7, sticky='nw')
                    self.encoder_progressbar = ttk.Progressbar(self, length=200)
                    self.encoder_progressbar.grid(column=1, row=2, padx=10, pady=7, sticky='nw')
                    self.sample_counter_var = StringVar()
                    Label(self, textvariable=self.sample_counter_var, bg=self['bg']).grid(column=2, row=0, pady=5,
                                                                                          sticky='nw')
                    self.distance_var = StringVar()
                    Label(self, textvariable=self.distance_var, bg=self['bg']).grid(column=2, row=1, pady=5,
                                                                                    sticky='nw')
                    self.encoder_var = StringVar()
                    Label(self, textvariable=self.encoder_var, bg=self['bg']).grid(column=2, row=2, pady=5, sticky='nw')
                    self.init()
                    self._update_callback = None
                    self.sample_counter_after_id = None
                    # self.demo_animation()

                def init(self):
                    self.sample_counter_progressbar['value'] = 0
                    self.sample_counter_progressbar["maximum"] = 65532
                    self.distance_progressbar['value'] = 0
                    self.distance_progressbar["maximum"] = 32768
                    self.encoder_progressbar['value'] = 0
                    self.encoder_progressbar["maximum"] = 65532
                    self.sample_counter_var.set('0')
                    self.distance_var.set('0')
                    self.encoder_var.set('0')

                def set_tc_update_callback(self, cmd):
                    self._update_callback = cmd

                def clear_update_callback(self):
                    self._update_callback = None

                def update_data(self):
                    if self._update_callback is not None:
                        self._update_callback()
                        self.sample_counter_after_id = self.after(10, self.update_data)

            class SecondRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.CTN = 0
                    self.SYNC = 1
                    self.TRE = 2
                    self._selected_option = IntVar()
                    self._selected_buffer = IntVar()
                    options = (('Free Run Mode', self.CTN),
                               ('Sync-In Trigger', self.SYNC),
                               ('Encoder Trigger', self.TRE))

                    # s = ttk.Style()
                    # s.configure('Wild.TRadiobutton', background='SystemButtonFace')
                    for index, option in enumerate(options):
                        r = ttk.Radiobutton(self, text=option[0], value=option[1], variable=self._selected_option,
                                            takefocus=False, command=self._trigger_mode_selected)
                        r.grid(column=0, row=index, padx=10, pady=5, sticky='w')
                    self._selected_option.set(self.CTN)
                    self.trig_mode_sel_callback = None

                def set_tc_trig_mode_value(self, val: int):
                    self._selected_option.set(val)
                    self._selected_buffer.set(val)

                def get_tc_trig_mode_value(self):
                    try:
                        return self._selected_option.get()
                    except TclError:
                        return None

                def _trigger_mode_selected(self):
                    try:
                        sel_option = self._selected_option.get()
                    except TclError:
                        sel_option = None
                    try:
                        sel_buffer = self._selected_buffer.get()
                    except TclError:
                        sel_buffer = None
                    if sel_option != sel_buffer:
                        self._selected_buffer.set(sel_option)
                        if self.trig_mode_sel_callback:
                            self.trig_mode_sel_callback()

            class ThirdRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                    Label(self, text='Axis:', bg=self['bg'], justify='left').grid(column=0, row=0, pady=2, sticky='nw')
                    self.selected_axis = StringVar()
                    s = ttk.Style()
                    s.configure("TCombobox", fieldbackground="white", background="white")
                    self.axis_combobox = ttk.Combobox(self, textvariable=self.selected_axis, width=20,
                                                      height=20, state='readonly', values=['x', 'y', 'z', 'u', 'v'])
                    self.selected_axis.set(self.axis_combobox['values'][0])
                    self.axis_combobox.grid(column=1, row=0, padx=10, pady=4, sticky='nw')

                    Label(self, text='Encoder resolution (um/pulse):', bg=self['bg'],
                          justify='left').grid(column=3, row=0, padx=5, sticky='nw')
                    self.encoder_resolution_entry = Entry(self, validate="key",
                                                          validatecommand=(
                                                              self.register(validate_entry_digit_decimal_p),
                                                              "%P"), width=10)
                    self.encoder_resolution_entry.grid(column=4, row=0, pady=3, sticky='nw')

                    self.tc_axis_select_callback = None
                    self.encoder_resolution_callback = None
                    self.axis_combobox.bind("<<ComboboxSelected>>", self._axis_sel)
                    self.encoder_resolution_entry.bind('<Return>', self._encoder_resolution_enter)
                    self.encoder_resolution_entry.bind('<Button-1>', lambda x: switch_to_english_input())

                def _axis_sel(self, e):
                    if self.tc_axis_select_callback is not None:
                        self.tc_axis_select_callback()

                def _encoder_resolution_enter(self, e):
                    if self.encoder_resolution_callback is not None:
                        self.encoder_resolution_callback()

            class ForthRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    frame_1 = Frame(self, bg=self['bg'])
                    frame_1.grid(column=0, row=0, padx=10, pady=2, sticky='nw')
                    Label(frame_1, text='X scan length (mm): ', bg=self['bg'], justify='left').pack(side='left',
                                                                                                    fill='x')
                    self.x_scan_length_entry = Entry(frame_1, validate="key",
                                                     validatecommand=(self.register(validate_entry_digit_decimal_p),
                                                                      "%P"), width=10)
                    self.x_scan_length_entry.pack(side='left', fill='x')

                    frame_2 = Frame(self, bg=self['bg'])
                    frame_2.grid(column=1, row=0, padx=10, pady=2, sticky='nw')
                    Label(frame_2, text='dX step resolution(um):', bg=self['bg'], justify='left').pack(side='left',
                                                                                                       fill='x')
                    self.dx_entry = Entry(frame_2, validate="key",
                                          validatecommand=(self.register(validate_entry_digit_decimal_p),
                                                           "%P"), width=10)
                    self.dx_entry.pack(side='left', fill='x')

                    max_speed_f = Frame(frame_2, bg=self['bg'])
                    max_speed_f.pack(side='left', padx=5)
                    Label(max_speed_f, text='max. axis speed:', bg=self['bg'], justify='left').pack(side='left',
                                                                                                    fill='x')
                    self.speed_var = StringVar()
                    Label(max_speed_f, textvariable=self.speed_var, bg=self['bg'], fg='red',
                          justify='left', width=8).pack(side='left', fill='x')
                    self.speed_var.set("0 mm/s")  # 預設值

                    self._help_button = HelpButton(master=frame_2, size=(14, 14), command=self._help)
                    self._help_button.pack(side='left', fill='x', pady=2)

                    frame_3 = Frame(self, bg=self['bg'])
                    frame_3.grid(column=0, row=1, padx=10, pady=2, sticky='nw')
                    Label(frame_3, text='Y line count (*n):      ', bg=self['bg'], justify='left').pack(side='left',
                                                                                                        fill='x')
                    self.y_line_count_entry = Entry(frame_3, validate="key",
                                                    validatecommand=(self.register(validate_entry_digit), "%P"),
                                                    width=10)
                    self.y_line_count_entry.pack(side='left', fill='x')
                    self.y_line_count_entry.insert('end', '1')

                    frame_4 = Frame(self, bg=self['bg'])
                    frame_4.grid(column=1, row=1, padx=10, pady=2, sticky='nw')
                    Label(frame_4, text='dY step resolution(um):', bg=self['bg'], justify='left').pack(side='left',
                                                                                                       fill='x')
                    self.dy_entry = Entry(frame_4, width=10, state='readonly')
                    self.dy_entry.pack(side='left', fill='x')

                    self.x_scan_length_entry_callback = None
                    self.dx_entry_callback = None

                    self.x_scan_length_entry.bind('<Return>', self._x_scan_length)
                    self.x_scan_length_entry.bind('<Button-1>', lambda x: switch_to_english_input())
                    self.dx_entry.bind('<Return>', self.tc_dx_callback)
                    self.dx_entry.bind('<Button-1>', lambda x: switch_to_english_input())

                def _help(self):
                    self._help_button.disable()
                    PowerPointWindow(master=self, title='Recommended Max. Axis Speed',
                                     close_command=self._help_button.enable,
                                     image_dir_en='images\\max speed\\en',
                                     image_dir_cn='images\\max speed\\cn')

                def _x_scan_length(self, e):
                    if self.x_scan_length_entry_callback is not None:
                        self.x_scan_length_entry_callback()

                def tc_dx_callback(self, e):
                    if self.dx_entry_callback is not None:
                        self.dx_entry_callback()

            class FifthRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    frame_1 = Frame(self, bg=self['bg'])
                    frame_1.grid(column=0, row=0, padx=10, pady=2, sticky='nw')
                    Label(frame_1, text='[Encoder Count]    Start Pos:', bg=self['bg'],
                          justify='left').pack(side='left', fill='x')
                    self.en_start_pos_entry = Entry(frame_1, width=10)
                    self.en_start_pos_entry.pack(side='left', fill='x')
                    self.en_start_pos_entry.insert('end', '0')

                    frame_2 = Frame(self, bg=self['bg'])
                    frame_2.grid(column=1, row=0, padx=10, pady=2, sticky='nw')
                    Label(frame_2, text='Stop Pos:', bg=self['bg'], justify='left').pack(side='left', fill='x')
                    self.en_stop_pos_entry = Entry(frame_2, width=10)
                    self.en_stop_pos_entry.pack(side='left', fill='x')

                    frame_3 = Frame(self, bg=self['bg'])
                    frame_3.grid(column=2, row=0, padx=10, pady=2, sticky='nw')
                    Label(frame_3, text='Interval:', bg=self['bg'], justify='left').pack(side='left', fill='x')
                    self.en_interval_entry = Entry(frame_3, width=10)
                    self.en_interval_entry.pack(side='left', fill='x')

                    frame_4 = Frame(self, bg=self['bg'])
                    frame_4.grid(column=0, row=1, padx=10, pady=2, sticky='nw')
                    Label(frame_4, text='[Position in mm]   Start Pos:', bg=self['bg'],
                          justify='left').pack(side='left', fill='x')
                    self.pos_start_pos_entry = Entry(frame_4, validate="key",
                                                     validatecommand=(self.register(validate_entry_digit_decimal_p),
                                                                      "%P"), width=10)
                    self.pos_start_pos_entry.pack(side='left', fill='x')
                    self.pos_start_pos_entry.insert('end', '0.0')

                    frame_5 = Frame(self, bg=self['bg'])
                    frame_5.grid(column=1, row=1, padx=10, pady=2, sticky='nw')
                    Label(frame_5, text='Stop Pos:', bg=self['bg'], justify='left').pack(side='left', fill='x')
                    self.pos_stop_pos_entry = Entry(frame_5, validate="key",
                                                    validatecommand=(self.register(validate_entry_digit_decimal_p),
                                                                     "%P"), width=10)
                    self.pos_stop_pos_entry.pack(side='left', fill='x')

                    frame_6 = Frame(self, bg=self['bg'])
                    frame_6.grid(column=2, row=1, padx=10, pady=2, sticky='nw')
                    Label(frame_6, text='Interval:', bg=self['bg'], justify='left').pack(side='left', fill='x')
                    self.pos_interval_entry = Entry(frame_6, validate="key",
                                                    validatecommand=(self.register(validate_entry_digit_decimal_p),
                                                                     "%P"), width=10)
                    self.pos_interval_entry.pack(side='left', fill='x')

                    self.tc_en_start_pos_callback = None
                    self.tc_en_stop_pos_callback = None
                    self.tc_en_interval_callback = None
                    self.tc_pos_start_pos_callback = None
                    self.tc_pos_stop_pos_callback = None
                    self.tc_pos_interval_callback = None

                    self.en_start_pos_entry.bind('<Return>', self._en_start_pos)
                    self.en_stop_pos_entry.bind('<Return>', self._en_end_pos)
                    self.en_interval_entry.bind('<Return>', self._en_interval_pos)
                    self.pos_start_pos_entry.bind('<Return>', self._pos_start_pos)
                    self.pos_start_pos_entry.bind('<Button-1>', lambda x: switch_to_english_input())
                    self.pos_stop_pos_entry.bind('<Return>', self._pos_end_pos)
                    self.pos_stop_pos_entry.bind('<Button-1>', lambda x: switch_to_english_input())
                    self.pos_interval_entry.bind('<Return>', self._pos_interval_pos)
                    self.pos_interval_entry.bind('<Button-1>', lambda x: switch_to_english_input())

                def _en_start_pos(self, e):
                    if self.tc_en_start_pos_callback is not None:
                        self.tc_en_start_pos_callback()

                def _en_end_pos(self, e):
                    if self.tc_en_stop_pos_callback is not None:
                        self.tc_en_stop_pos_callback()

                def _en_interval_pos(self, e):
                    if self.tc_en_interval_callback is not None:
                        self.tc_en_interval_callback()

                def _pos_start_pos(self, e):
                    if self.tc_pos_start_pos_callback is not None:
                        self.tc_pos_start_pos_callback()

                def _pos_end_pos(self, e):
                    if self.tc_pos_stop_pos_callback is not None:
                        self.tc_pos_stop_pos_callback()

                def _pos_interval_pos(self, e):
                    if self.tc_pos_interval_callback is not None:
                        self.tc_pos_interval_callback()

            class SixthRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # self.set_en_pos_button = RoundCornerButton(master=self, text='Set Trigger Axis Encoder Position',
                    #                                            size='m', width=180, height=20, bg=self['bg'])
                    # self.set_en_pos_button.grid(column=0, row=0, sticky='nw')
                    # self.set_en_pos_entry = Entry(self, width=10)
                    # self.set_en_pos_entry.grid(column=1, row=0, padx=5, pady=3, sticky='nw')
                    self.trigger_on_return_checkbox_var = IntVar()
                    self.trigger_on_return_checkbutton = ttk.Checkbutton(self, text='Trigger on return move',
                                                                         command=self._trigger_on_return_on_click,
                                                                         takefocus=False, onvalue=1, offvalue=0,
                                                                         variable=self.trigger_on_return_checkbox_var,
                                                                         style='blue.TCheckbutton')
                    self.trigger_on_return_checkbutton.grid(column=0, row=0, sticky='nw', padx=5, pady=2)

                    sample_cnt_f = Frame(self, bg=self['bg'])
                    sample_cnt_f.grid(column=1, row=0, sticky='nw', padx=45, pady=0)
                    Label(sample_cnt_f, text='Sample Count (per line):', bg=self['bg'],
                          justify='left').grid(column=0, row=0, sticky='nw', padx=5, pady=0)
                    self.sample_count_entry = Entry(sample_cnt_f, validate="key", width=10,
                                                    validatecommand=(self.register(validate_entry_digit), "%P"))
                    self.sample_count_entry.insert('end', '1000')
                    self.sample_count_entry.grid(column=1, row=0, sticky='nw', padx=0, pady=2)

                    self._trigger_on_return_callback = None

                def _trigger_on_return_on_click(self):
                    if self._trigger_on_return_callback is not None:
                        self._trigger_on_return_callback()

            class SeventhRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.set_trig_pos_button = RoundCornerButton(master=self, width=200, height=20,
                                                                 text='Set Trigger Axis Encoder Position:', size='m',
                                                                 bg=self['bg'], command=self._trig_pos)
                    self.set_trig_pos_button.pack(side='left', anchor='n', padx=5)
                    self.encoder_position_entry = Entry(self, width=15)
                    self.encoder_position_entry.insert('end', '-20')
                    self.encoder_position_entry.pack(side='left', anchor='n', pady=2)

                    self.tc_set_trig_pos_callback = None

                def _trig_pos(self):
                    if self.tc_set_trig_pos_callback is not None:
                        self.tc_set_trig_pos_callback()

            class EighthRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    Label(self, text='Intensity Saturation Level:', bg=self['bg'], justify='left').pack(side='left',
                                                                                                        fill='x')
                    self.sat_lvl_entry = Entry(self, width=10)
                    self.sat_lvl_entry.pack(side='left', fill='x', padx=5)
                    self.help_button = HelpButton(master=self, size=(14, 14), command=self._help)
                    self.help_button.pack(side='left', fill='x', padx=5, pady=2)

                def _help(self):
                    self.help_button.disable()
                    PowerPointWindow(master=self, title='Intensity Saturation Level',
                                     close_command=self.help_button.enable,
                                     image_dir_en='images\\intensity_saturation_level\\intensity_saturation_level_en',
                                     image_dir_cn='images\\intensity_saturation_level\\intensity_saturation_level_cn')

            class NinthRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.start_scan_button = RoundCornerButtonGR(master=self, text='Start Scan', size='m', width=100,
                                                                 height=20, bg=self['bg'], state='disabled',
                                                                 command=self._start_scan)
                    self.start_scan_button.grid(column=0, row=0, sticky='nw')
                    self.stop_scan_button = RoundCornerButton(master=self, text='Stop Scan', size='m', width=100,
                                                              height=20, bg=self['bg'], command=self._stop_scan)
                    self.stop_scan_button.grid(column=1, row=0, sticky='nw')
                    self.reset_ctn_button = RoundCornerButton(master=self, text='Reset to CTN', size='m', width=100,
                                                              height=20, bg=self['bg'], command=self._reset_ctn)
                    self.reset_ctn_button.grid(column=2, row=0, sticky='nw')
                    self.save_data_button = RoundCornerButton(master=self, text='Save Peak Data', size='m',
                                                              width=110, height=20, bg=self['bg'],
                                                              command=self._save_data)
                    self.save_data_button.grid(column=3, row=0, sticky='nw')

                    self.data_format = StringVar()
                    s = ttk.Style()
                    s.configure("TCombobox", fieldbackground="white", background="white")
                    self.data_format_combobox = ttk.Combobox(self, textvariable=self.data_format, width=6,
                                                             state='readonly', values=['*.asc', '*.bcrf'])
                    self.data_format.set(self.data_format_combobox['values'][0])
                    self.data_format_combobox.grid(column=4, row=0, padx=5, sticky='nw')

                    self._help_button = HelpButton(master=self, size=(14, 14), command=self._help)
                    self._help_button.grid(column=5, row=0, sticky='nw')

                    self.start_scan_callback = None
                    self.stop_scan_callback = None
                    self.reset_ctn_callback = None
                    self.save_data_callback = None

                def _help(self):
                    self._help_button.disable()
                    PowerPointWindow(master=self, title='Save File Description', close_command=self._help_button.enable,
                                     image_dir_en='images\\save_file_description\\en',
                                     image_dir_cn='images\\save_file_description\\cn')

                def _start_scan(self):
                    if self.start_scan_callback is not None and self.start_scan_button.get_button_color() == 'n':
                        self.start_scan_callback()

                def _stop_scan(self):
                    if self.stop_scan_callback is not None and self.start_scan_button.get_button_color() == 'g':
                        self.stop_scan_callback()

                def _reset_ctn(self):
                    if self.reset_ctn_callback is not None:
                        self.reset_ctn_callback()

                def _save_data(self):
                    if self.save_data_callback is not None:
                        self.save_data_callback()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.first_r_f = self.FirstRowFrame(self, bg=self['bg'])
                self.first_r_f.pack(side='top', fill='x')
                self.second_r_f = self.SecondRowFrame(self, bg=self['bg'])
                self.second_r_f.pack(side='top', fill='x')
                self.third_r_f = self.ThirdRowFrame(self, bg=self['bg'])
                self.third_r_f.pack(side='top', fill='x', padx=8, pady=10)
                self.forth_r_f = self.ForthRowFrame(self, bg=self['bg'])
                self.forth_r_f.pack(side='top', fill='x')
                self.fifth_r_f = self.FifthRowFrame(self, bg=self['bg'])
                self.fifth_r_f.pack(side='top', fill='x', pady=10)
                self.sixth_r_f = self.SixthRowFrame(self, bg=self['bg'])
                self.sixth_r_f.pack(side='top', fill='x', padx=8, pady=5)
                self.seventh_r_f = self.SeventhRowFrame(self, bg=self['bg'])
                self.seventh_r_f.pack(side='top', fill='x', padx=8, pady=5)
                self.eighth_r_f = self.EighthRowFrame(self, bg=self['bg'])
                self.eighth_r_f.pack(side='top', fill='x', padx=8, pady=5)
                self.ninth_r_f = self.NinthRowFrame(self, bg=self['bg'])
                self.ninth_r_f.pack(side='top', fill='x', padx=8, pady=5)

        class RightFrame(Frame):
            class FirstRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    frame_1 = Frame(self, bg=self['bg'])
                    frame_1.grid(column=0, row=0, sticky='nw', padx=10)

                    self.display_switch_status = ctk.StringVar(value="on")
                    ctk.CTkSwitch(frame_1, text="", command=self._toggle_plot_switch, progress_color="#30d158",
                                  button_color="white", variable=self.display_switch_status, onvalue="on",
                                  offvalue="off", width=45).pack(side='left')

                    Label(frame_1, text='Display Peak Signal:', bg=self['bg'], justify='left').pack(side='left',
                                                                                                    fill='y')
                    self.selected_peak_signal = StringVar()
                    s = ttk.Style()
                    s.configure("TCombobox", fieldbackground="white", background="white")
                    self.selected_buffer = None
                    self.peak_signal_combobox = ttk.Combobox(frame_1, textvariable=self.selected_peak_signal, width=20,
                                                             height=20, state='readonly', values=[])
                    self.peak_signal_combobox.pack(side='left', fill='y')
                    self.peak_signal_combobox.bind("<<ComboboxSelected>>", self._select_combobox)
                    self.select_peak_signal_callback = None

                    self.sat_int_switch_status = ctk.StringVar(value="on")
                    ctk.CTkSwitch(frame_1, text="Add Highlight Saturation Intensity", progress_color="#30d158",
                                  button_color="white", variable=self.sat_int_switch_status, onvalue="on",
                                  offvalue="off", width=45, text_color="#504c54").pack(side='left', padx=10)
                    self.sat_int_switch_status.set('off')

                    # frame_2 = Frame(self, bg=self['bg'])
                    # frame_2.grid(column=1, row=0, sticky='nw', padx=5)
                    # Label(frame_2, text='Min:', bg=self['bg'], justify='left').pack(side='left', fill='y')
                    # self.min_entry = Entry(frame_2, width=10)
                    # self.min_entry.pack(side='left', fill='y')
                    #
                    # frame_3 = Frame(self, bg=self['bg'])
                    # frame_3.grid(column=2, row=0, sticky='nw', padx=5)
                    # Label(frame_3, text='Max:', bg=self['bg'], justify='left').pack(side='left', fill='y')
                    # self.max_entry = Entry(frame_3, width=10)
                    # self.max_entry.pack(side='left', fill='x')

                def _toggle_plot_switch(self):
                    current_state = self.peak_signal_combobox.cget('state')  # 取得 'state' 屬性的值
                    if current_state.string == 'disabled':
                        self.peak_signal_combobox.config(state='readonly')
                    else:
                        self.peak_signal_combobox.config(state='disabled')

                def _select_combobox(self, e):
                    _ = e
                    selected_id = self.peak_signal_combobox.get()
                    if selected_id != self.selected_buffer:
                        self.selected_buffer = selected_id
                        if self.select_peak_signal_callback is not None:
                            self.select_peak_signal_callback()

            class SecondRowFrame(Frame):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.scan_plot = BasicMatplot(master=self, fig_size=(8, 6), tool_bar=True, bg_color=self['bg'])
                    self.scan_plot.pack(side='top', fill='x')

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.first_row_f = self.FirstRowFrame(self, bg=self['bg'])
                self.first_row_f.pack(side='top', fill='x', anchor='w')
                self.second_row_f = self.SecondRowFrame(self, bg=self['bg'])
                self.second_row_f.pack(side='top', fill='x', anchor='w', pady=10)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_frame = Frame(self, bg=self['bg'])
            main_frame.pack(side='top', fill='x', padx=30, pady=15)
            self.top_left_f = self.LeftFrame(main_frame, bg=self['bg'])
            self.top_left_f.grid(column=0, row=0, sticky='nw')
            self.right_f = self.RightFrame(main_frame, bg=self['bg'])
            self.right_f.grid(column=1, row=0, sticky='nw', padx=15)
            self.set_tc_trig_mode_value(self.top_left_f.second_r_f.CTN)

        """ Right Frame """

        # region
        def tc_set_scan_plot(self, data):
            self.right_f.second_row_f.scan_plot.plot(data)

        def tc_clear_plot(self):
            self.right_f.second_row_f.scan_plot.clear_plot()

        def tc_reset_plot_scale(self):
            self.right_f.second_row_f.scan_plot.reset_scale()

        def tc_set_peak_id_options(self, ids):
            self.right_f.first_row_f.peak_signal_combobox['values'] = ids

        def tc_set_peak_id(self, id_str: str):
            self.right_f.first_row_f.selected_buffer = id_str
            self.right_f.first_row_f.peak_signal_combobox.set(id_str)

        def tc_get_peak_id(self) -> str:
            return self.right_f.first_row_f.peak_signal_combobox.get()

        def tc_set_plot_unit(self, unit_str: str):
            self.right_f.second_row_f.scan_plot.set_unit_str(unit_str)

        # endregion

        """ Top Left Frame - First Line """

        # region
        def set_tc_encoder_bar(self, val: str):
            self.top_left_f.first_r_f.encoder_progressbar['value'] = int(val)
            self.top_left_f.first_r_f.encoder_var.set(val)

        def set_tc_encoder_type(self, encoder: str):
            if encoder.lower() == 'x':
                self.top_left_f.first_r_f.encoder_label_str.set('Encoder X (id: 65)')
            elif encoder.lower() == 'y':
                self.top_left_f.first_r_f.encoder_label_str.set('Encoder Y (id: 66)')
            elif encoder.lower() == 'z':
                self.top_left_f.first_r_f.encoder_label_str.set('Encoder Z (id: 67)')
            elif encoder.lower() == 'u':
                self.top_left_f.first_r_f.encoder_label_str.set('Encoder U (id: 68)')
            elif encoder.lower() == 'v':
                self.top_left_f.first_r_f.encoder_label_str.set('Encoder V (id: 69)')

        def set_tc_sample_counter_bar(self, val: str):
            self.top_left_f.first_r_f.sample_counter_progressbar['value'] = val
            self.top_left_f.first_r_f.sample_counter_var.set(val)

        def set_tc_distance_bar(self, val: str):
            self.top_left_f.first_r_f.distance_progressbar['value'] = val
            self.top_left_f.first_r_f.distance_var.set(val)

        def start_auto_update_sample_counter(self):
            self.top_left_f.first_r_f.update_data()

        def stop_auto_update_sample_counter(self):
            if self.top_left_f.first_r_f.sample_counter_after_id is not None:
                self.after_cancel(self.top_left_f.first_r_f.sample_counter_after_id)

        # endregion

        """ Top Left Frame - Third Line """

        # region
        def tc_check_trigger_each_widgets_state(self):
            trig_mode = self.top_left_f.second_r_f.get_tc_trig_mode_value()
            if trig_mode == self.top_left_f.second_r_f.TRE:
                self.top_left_f.third_r_f.axis_combobox['state'] = 'readonly'
                self.top_left_f.third_r_f.encoder_resolution_entry['state'] = 'normal'
                self.top_left_f.forth_r_f.dx_entry['state'] = 'normal'
                self.top_left_f.fifth_r_f.en_start_pos_entry['state'] = 'normal'
                self.top_left_f.fifth_r_f.pos_start_pos_entry['state'] = 'normal'
                self.top_left_f.fifth_r_f.en_stop_pos_entry['state'] = 'normal'
                self.top_left_f.fifth_r_f.pos_stop_pos_entry['state'] = 'normal'
                self.top_left_f.fifth_r_f.en_interval_entry['state'] = 'normal'
                self.top_left_f.fifth_r_f.pos_interval_entry['state'] = 'normal'
                self.top_left_f.sixth_r_f.sample_count_entry['state'] = 'disabled'
                self.top_left_f.sixth_r_f.trigger_on_return_checkbutton['state'] = 'normal'
                self.top_left_f.seventh_r_f.set_trig_pos_button['state'] = 'normal'
                self.top_left_f.seventh_r_f.encoder_position_entry['state'] = 'normal'
            else:
                self.top_left_f.third_r_f.axis_combobox['state'] = 'disable'
                self.top_left_f.third_r_f.encoder_resolution_entry['state'] = 'disable'
                self.top_left_f.forth_r_f.dx_entry['state'] = 'disable'
                self.top_left_f.fifth_r_f.en_start_pos_entry['state'] = 'disable'
                self.top_left_f.fifth_r_f.pos_start_pos_entry['state'] = 'disable'
                self.top_left_f.fifth_r_f.en_stop_pos_entry['state'] = 'disable'
                self.top_left_f.fifth_r_f.pos_stop_pos_entry['state'] = 'disable'
                self.top_left_f.fifth_r_f.en_interval_entry['state'] = 'disable'
                self.top_left_f.fifth_r_f.pos_interval_entry['state'] = 'disable'
                self.top_left_f.sixth_r_f.sample_count_entry['state'] = 'normal'
                self.top_left_f.sixth_r_f.trigger_on_return_checkbutton['state'] = 'disable'
                self.top_left_f.seventh_r_f.set_trig_pos_button['state'] = 'disable'
                self.top_left_f.seventh_r_f.encoder_position_entry['state'] = 'disable'

        # endregion

        """ Top Left Frame - Fifth Line """

        # region
        def set_tc_sample_count(self, val: str):
            if self.top_left_f.sixth_r_f.sample_count_entry['state'] == 'disabled':
                self.top_left_f.sixth_r_f.sample_count_entry['state'] = 'normal'
                self.top_left_f.sixth_r_f.sample_count_entry.delete(0, 'end')
                self.top_left_f.sixth_r_f.sample_count_entry.insert('end', val)
                self.top_left_f.sixth_r_f.sample_count_entry['state'] = 'disabled'
            else:
                self.top_left_f.sixth_r_f.sample_count_entry.delete(0, 'end')
                self.top_left_f.sixth_r_f.sample_count_entry.insert('end', val)

        def get_tc_sample_count(self) -> str:
            return self.top_left_f.sixth_r_f.sample_count_entry.get()

        # endregion

        """ Top Left Frame - Sixth Line """

        # region
        def get_tc_y_line_count(self) -> int:
            count = self.top_left_f.forth_r_f.y_line_count_entry.get()
            if len(count) > 0:
                return int(count)
            else:
                return 0

        # endregion

        """ Top Left Frame - Seventh Line """

        # region
        def get_tc_trig_axis_encoder_pos(self):
            return self.top_left_f.seventh_r_f.encoder_position_entry.get()

        def set_tc_trig_pos_callback(self, cmd):
            self.top_left_f.seventh_r_f.tc_set_trig_pos_callback = cmd

        # endregion

        """ Top Left Frame - Eighth Line """

        # region
        def set_tc_saturation_level(self, val: str):
            self.top_left_f.eighth_r_f.sat_lvl_entry.delete(0, 'end')
            self.top_left_f.eighth_r_f.sat_lvl_entry.insert('end', val)

        def get_tc_saturation_level(self) -> str:
            return self.top_left_f.eighth_r_f.sat_lvl_entry.get()

        # endregion

        """ Top Left Frame - Ninth Line """

        # region
        def set_tc_start_scan_btn(self, start: bool):
            if start:
                self.top_left_f.ninth_r_f.start_scan_button.set_button_color('g')
                self.top_left_f.ninth_r_f.start_scan_button['text'] = 'Scanning...'
            else:
                self.top_left_f.ninth_r_f.start_scan_button.set_button_color('n')
                self.top_left_f.ninth_r_f.start_scan_button['text'] = 'Start'

        def tc_start_scan_btn_stat(self, stat):
            if stat:
                self.top_left_f.ninth_r_f.start_scan_button['stat'] = 'normal'
            else:
                self.top_left_f.ninth_r_f.start_scan_button['stat'] = 'disabled'

        def set_tc_selected_peak_signal_callback(self, cmd):
            self.right_f.first_row_f.select_peak_signal_callback = cmd

        def set_tc_save_asc_callback(self, cmd):
            self.top_left_f.ninth_r_f.save_data_callback = cmd

        def get_tc_data_format(self) -> str:
            return self.top_left_f.ninth_r_f.data_format.get()

        # endregion

        def set_tc_trig_mode_value(self, val: int):
            self.top_left_f.second_r_f.set_tc_trig_mode_value(val)
            self.tc_check_trigger_each_widgets_state()

        def get_tc_trig_mode_value(self):
            return self.top_left_f.second_r_f.get_tc_trig_mode_value()

        def set_tc_axis(self, val: str):
            self.top_left_f.third_r_f.selected_axis.set(val)

        def get_tc_axis(self) -> str:
            return self.top_left_f.third_r_f.selected_axis.get()

        def set_encoder_resolution(self, val: str):
            self.top_left_f.third_r_f.encoder_resolution_entry.delete(0, 'end')
            self.top_left_f.third_r_f.encoder_resolution_entry.insert('end', val)

        def get_encoder_resolution(self) -> float:
            res = self.top_left_f.third_r_f.encoder_resolution_entry.get()
            return float(res) if res else None

        def set_tc_en_start_pos(self, val: str):
            self.top_left_f.fifth_r_f.en_start_pos_entry.delete(0, 'end')
            self.top_left_f.fifth_r_f.en_start_pos_entry.insert('end', val)

        def get_tc_en_start_pos(self) -> int:
            pos = self.top_left_f.fifth_r_f.en_start_pos_entry.get().replace(',', '')
            return int(pos) if pos else None

        def set_tc_en_stop_pos(self, val: str):
            self.top_left_f.fifth_r_f.en_stop_pos_entry.delete(0, 'end')
            self.top_left_f.fifth_r_f.en_stop_pos_entry.insert('end', val)

        def get_tc_en_stop_pos(self) -> int:
            pos = self.top_left_f.fifth_r_f.en_stop_pos_entry.get().replace(',', '')
            return int(pos) if pos else None

        def set_tc_en_interval(self, val: str):
            self.top_left_f.fifth_r_f.en_interval_entry.delete(0, 'end')
            self.top_left_f.fifth_r_f.en_interval_entry.insert('end', val)

        def get_tc_en_interval(self) -> int:
            interval = self.top_left_f.fifth_r_f.en_interval_entry.get().replace(',', '')
            return int(interval) if interval else None

        def set_tc_pos_start_pos(self, val: str):
            self.top_left_f.fifth_r_f.pos_start_pos_entry.delete(0, 'end')
            self.top_left_f.fifth_r_f.pos_start_pos_entry.insert('end', val)

        def get_tc_pos_start_pos(self) -> float:
            pos = self.top_left_f.fifth_r_f.pos_start_pos_entry.get().replace(',', '')
            return float(pos) if pos else None

        def set_tc_pos_stop_pos(self, val: str):
            self.top_left_f.fifth_r_f.pos_stop_pos_entry.delete(0, 'end')
            self.top_left_f.fifth_r_f.pos_stop_pos_entry.insert('end', val)

        def get_tc_pos_stop_pos(self) -> float:
            pos = self.top_left_f.fifth_r_f.pos_stop_pos_entry.get().replace(',', '')
            return float(pos) if pos else None

        def set_tc_pos_interval(self, val: str):
            self.top_left_f.fifth_r_f.pos_interval_entry.delete(0, 'end')
            self.top_left_f.fifth_r_f.pos_interval_entry.insert('end', val)

        def get_tc_pos_interval(self) -> float:
            interval = self.top_left_f.fifth_r_f.pos_interval_entry.get().replace(',', '')
            return float(interval) if interval else None

        def set_x_scan_length(self, val: str):
            self.top_left_f.forth_r_f.x_scan_length_entry.delete(0, 'end')
            self.top_left_f.forth_r_f.x_scan_length_entry.insert('end', val)

        def get_x_scan_length(self) -> float:
            length = self.top_left_f.forth_r_f.x_scan_length_entry.get().replace(',', '')
            return float(length) if length else None

        def set_dx_value(self, val: str):
            self.top_left_f.forth_r_f.dx_entry.delete(0, 'end')
            self.top_left_f.forth_r_f.dx_entry.insert('end', val)

        def get_dx_value(self) -> float:
            dx = self.top_left_f.forth_r_f.dx_entry.get()
            return float(dx) if dx else None

        def set_max_speed(self, speed: str):
            self.top_left_f.forth_r_f.speed_var.set(f"{speed} mm/s")

        def set_dy_value(self, val: str):
            self.top_left_f.forth_r_f.dy_entry['state'] = 'normal'
            self.top_left_f.forth_r_f.dy_entry.delete(0, 'end')
            self.top_left_f.forth_r_f.dy_entry.insert('end', val)
            self.top_left_f.forth_r_f.dy_entry['state'] = 'readonly'

        def get_dy_value(self) -> float:
            dy = self.top_left_f.forth_r_f.dy_entry.get()
            return float(dy) if dy else None

        def set_tc_trig_on_return(self, val: int):
            self.top_left_f.sixth_r_f.trigger_on_return_checkbox_var.set(val)

        def get_tc_trig_on_return(self):
            return self.top_left_f.sixth_r_f.trigger_on_return_checkbox_var.get()

        def set_tc_start_scan_callback(self, cmd):
            self.top_left_f.ninth_r_f.start_scan_callback = cmd

        def set_tc_stop_scan_callback(self, cmd):
            self.top_left_f.ninth_r_f.stop_scan_callback = cmd

        def set_tc_trig_mode_sel_callback(self, cmd):
            self.top_left_f.second_r_f.trig_mode_sel_callback = cmd

        def clear_tc_trig_mode_sel_callback(self):
            self.top_left_f.second_r_f.trig_mode_sel_callback = None

        def set_tc_axis_select_callback(self, cmd):
            self.top_left_f.third_r_f.tc_axis_select_callback = cmd

        def clear_tc_axis_select_callback(self):
            self.top_left_f.third_r_f.tc_axis_select_callback = None

        def set_tc_encoder_resolution_callback(self, cmd):
            self.top_left_f.third_r_f.encoder_resolution_callback = cmd

        def clear_tc_encoder_resolution_callback(self):
            self.top_left_f.third_r_f.encoder_resolution_callback = None

        def set_tc_en_start_pos_callback(self, cmd):
            self.top_left_f.fifth_r_f.tc_en_start_pos_callback = cmd

        def clear_tc_en_start_pos_callback(self):
            self.top_left_f.fifth_r_f.tc_en_start_pos_callback = None

        def set_tc_en_stop_pos_callback(self, cmd):
            self.top_left_f.fifth_r_f.tc_en_stop_pos_callback = cmd

        def clear_tc_en_end_pos_callback(self):
            self.top_left_f.fifth_r_f.tc_en_stop_pos_callback = None

        def set_tc_en_interval_callback(self, cmd):
            self.top_left_f.fifth_r_f.tc_en_interval_callback = cmd

        def clear_tc_en_interval_callback(self):
            self.top_left_f.fifth_r_f.tc_en_interval_callback = None

        def set_tc_pos_start_pos_callback(self, cmd):
            self.top_left_f.fifth_r_f.tc_pos_start_pos_callback = cmd

        def clear_tc_pos_start_pos_callback(self):
            self.top_left_f.fifth_r_f.tc_pos_start_pos_callback = None

        def set_tc_pos_stop_pos_callback(self, cmd):
            self.top_left_f.fifth_r_f.tc_pos_stop_pos_callback = cmd

        def clear_tc_pos_end_pos_callback(self):
            self.top_left_f.fifth_r_f.tc_pos_stop_pos_callback = None

        def set_tc_pos_interval_callback(self, cmd):
            self.top_left_f.fifth_r_f.tc_pos_interval_callback = cmd

        def clear_tc_pos_interval_callback(self):
            self.top_left_f.fifth_r_f.tc_pos_interval_callback = None

        def set_tc_trig_on_return_callback(self, cmd):
            self.top_left_f.sixth_r_f._trigger_on_return_callback = cmd

        def clear_tc_trig_on_return_callback(self):
            self.top_left_f.sixth_r_f._trigger_on_return_callback = None

        def set_x_scan_length_callback(self, cmd):
            self.top_left_f.forth_r_f.x_scan_length_entry_callback = cmd

        def clear_x_scan_length_callback(self):
            self.top_left_f.forth_r_f.x_scan_length_entry_callback = None

        def set_dx_callback(self, cmd):
            self.top_left_f.forth_r_f.dx_entry_callback = cmd

        def clear_dx_callback(self):
            self.top_left_f.forth_r_f.dx_entry_callback = None

        def set_reset_ctn_callback(self, cmd):
            self.top_left_f.ninth_r_f.reset_ctn_callback = cmd

        def clear_reset_ctn_callback(self):
            self.top_left_f.ninth_r_f.reset_ctn_callback = None

    class MultiLayerSetting(Frame):
        class TopFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.label_frame = Frame(self, bg=self['bg'])
                self.label_frame.grid(column=0, row=0, sticky='nw')
                Label(self.label_frame, text='Dealing with Multiple Layers', bg='#ffffe1', anchor='w',
                      width=55).pack(side='left', fill='y')
                self.help_button = HelpButton(master=self.label_frame, command=self._help, bg='#ffffe1')
                self.help_button.pack(side='left', fill='y')
                setting_f = Frame(self, bg=self['bg'])
                setting_f.grid(column=0, row=1, sticky='nw')
                label_txt_list = ['Number Peak ($NOP):',
                                  'Peak Threshold ($THR):',
                                  'Detection Window ($DWD):',
                                  'Refractive Index:']
                for index, txt in enumerate(label_txt_list):
                    Label(setting_f, bg=self['bg'], text=txt).grid(column=0, row=index, sticky='nw')

                self._number_of_peak_entry = Entry(setting_f, width=10)
                self._number_of_peak_entry.grid(column=1, row=0, columns=2, sticky='nw')
                self.set_mf_number_of_peak('?')
                self._peak_threshold_entry = Entry(setting_f, width=10)
                self._peak_threshold_entry.grid(column=1, row=1, columns=2, sticky='nw')
                self.set_mf_peak_threshold('?')
                self._detection_window_entry_l = Entry(setting_f, width=8)
                self._detection_window_entry_l.grid(column=1, row=2, sticky='nw')
                self.set_detection_window_l('?')
                self._detection_window_entry_h = Entry(setting_f, width=8)
                self._detection_window_entry_h.grid(column=2, row=2, sticky='nw', padx=2)
                self.set_detection_window_h('?')
                self._reflection_index_entry = Entry(setting_f, width=10)
                self._reflection_index_entry.grid(column=1, columns=2, row=3, sticky='nw')
                self.set_reflection_index('?')

            def _help(self):
                self.help_button.disable()
                PowerPointWindow(master=self, title='Multi-layer Setting',
                                 close_command=self.help_button.enable,
                                 image_dir_en='images\\multi-layer setting\\en',
                                 image_dir_cn='images\\multi-layer setting\\cn')

            def set_mf_number_of_peak(self, val):
                self._number_of_peak_entry.delete(0, 'end')
                self._number_of_peak_entry.insert('end', val)

            def get_mf_number_of_peak(self):
                return self._number_of_peak_entry.get()

            def clear_mf_number_of_peak(self):
                self._number_of_peak_entry.delete(0, 'end')

            def set_mf_peak_threshold(self, val):
                self._peak_threshold_entry.delete(0, 'end')
                self._peak_threshold_entry.insert('end', val)

            def get_mf_peak_threshold(self):
                return self._peak_threshold_entry.get()

            def clear_mf_peak_threshold(self):
                self._peak_threshold_entry.delete(0, 'end')

            def set_detection_window_l(self, val):
                self._detection_window_entry_l.delete(0, 'end')
                self._detection_window_entry_l.insert('end', val)

            def get_detection_window_l(self):
                return self._detection_window_entry_l.get()

            def set_detection_window_h(self, val):
                self._detection_window_entry_h.delete(0, 'end')
                self._detection_window_entry_h.insert('end', val)

            def get_detection_window_h(self):
                return self._detection_window_entry_h.get()

            def set_reflection_index(self, val):
                self._reflection_index_entry.delete(0, 'end')
                self._reflection_index_entry.insert('end', val)

            def get_reflection_index(self):
                return self._reflection_index_entry.get()

        class SpectrumFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.spectrum_button = RoundCornerButtonGR(master=self, text='Start Spectrum',
                                                           green='G2', width=165, height=20, bg=self['bg'],
                                                           command=self._spectrum_switch)
                self.spectrum_button.grid(row=0, column=0, sticky='nw', pady=1)
                channel_f = Frame(self, bg=self['bg'])
                channel_f.grid(row=0, column=1, sticky='nw', pady=1)
                Label(channel_f, bg=self['bg'], text='Channel:').grid(row=0, column=0)
                self.channel_entry = Entry(channel_f, width=10)
                self.channel_entry.grid(row=0, column=1, padx=10)
                self.channel_entry.bind('<Return>', self._entry_command)
                self.spectrum_plot = SpectrumPlot(master=self, fig_size=(7, 6), tool_bar=False,
                                                  title='Spectrum View')
                self.spectrum_plot.grid(row=1, column=0, columnspan=3, sticky='nswe')

                self.spectrum_button_callback = None
                self.channel_entry_callback = None
                self.update_spectrum_callback = None
                self._after_id = None

            def update_multilayer_p_spectrum(self):
                if self.update_spectrum_callback is not None:
                    self.update_spectrum_callback()
                    self._after_id = self.after(200, self.update_multilayer_p_spectrum)

            def stop_multilayer_p_spectrum(self):
                if self._after_id:
                    self.after_cancel(self._after_id)
                    self._after_id = None

            def _spectrum_switch(self):
                if self.spectrum_button_callback is not None:
                    self.spectrum_button_callback()

            def _entry_command(self, e):
                if self.channel_entry_callback is not None:
                    self.channel_entry_callback()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            main_f = Frame(self, bg=self['bg'])
            main_f.pack(side='top', fill='x', padx=30, pady=15)
            self.top_f = self.TopFrame(main_f, bg=self['bg'])
            self.top_f.grid(column=0, row=0, sticky='nw')
            self.multi_layer_spectrum_f = self.SpectrumFrame(main_f, bg=self['bg'])
            self.multi_layer_spectrum_f.grid(column=0, row=1, sticky='nw', pady=10)

        def update_multilayer_spectrum(self, data):
            self.multi_layer_spectrum_f.spectrum_plot.plot(data)

        def set_multilayer_spectrum_channel(self, val):
            self.multi_layer_spectrum_f.channel_entry.delete(0, 'end')
            self.multi_layer_spectrum_f.channel_entry.insert('end', val)

        def get_multilayer_spectrum_channel(self):
            return self.multi_layer_spectrum_f.channel_entry.get()

        def set_multilayer_spectrum_btn_green(self):
            self.multi_layer_spectrum_f.spectrum_button.set_button_color('g')
            self.multi_layer_spectrum_f.spectrum_button['text'] = 'Stop Spectrum'

        def set_multilayer_spectrum_btn_normal(self):
            self.multi_layer_spectrum_f.spectrum_button.set_button_color('n')
            self.multi_layer_spectrum_f.spectrum_button['text'] = 'Start Spectrum'

        def get_multilayer_spectrum_btn_color(self):
            return self.multi_layer_spectrum_f.spectrum_button.get_button_color()

        def set_multilayer_spectrum_button_callback(self, cmd):
            self.multi_layer_spectrum_f.spectrum_button_callback = cmd

        def set_multilayer_update_spectrum_callback(self, cmd):
            self.multi_layer_spectrum_f.update_spectrum_callback = cmd

        def set_multilayer_channel_entry_callback(self, cmd):
            self.multi_layer_spectrum_f.channel_entry_callback = cmd

    class Others(Frame):
        class CLS2Frame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.label = Label(self, text='CLS2 Series', bg='#fffce1', anchor='w', width=40)
                self.label.pack(side='top', anchor='w')

                # region HW
                hw_f = Frame(self, bg=self['bg'])
                hw_f.pack(side='top', padx=10, pady=5)
                self._hw_help_button = HelpButton(master=hw_f, command=self._hw_help)
                self._hw_help_button.pack(side='left')
                self._hw_label = Label(hw_f, text='CLS2 HW', bg=self['bg'], anchor='w',
                                       width=40)
                self._hw_label.pack(side='left', padx=5)
                # endregion

                # region HW
                sw_f = Frame(self, bg=self['bg'])
                sw_f.pack(side='top', padx=10, pady=5)
                self._sw_help_button = HelpButton(master=sw_f, command=self._sw_help)
                self._sw_help_button.pack(side='left')
                self._sw_label = Label(sw_f, text='CLS2 SW', bg=self['bg'], anchor='w',
                                       width=40)
                self._sw_label.pack(side='left', padx=5)
                # endregion

                # region High Speed Mode
                high_speed_f = Frame(self, bg=self['bg'])
                high_speed_f.pack(side='top', padx=10, pady=5)
                self.h_s_m_help_button = HelpButton(master=high_speed_f, command=self._hsm_help)
                self.h_s_m_help_button.pack(side='left')
                self.high_speed_mode_label = Label(high_speed_f, text='CLS2 High Speed Mode', bg=self['bg'], anchor='w',
                                                   width=40)
                self.high_speed_mode_label.pack(side='left', padx=5)
                # endregion

                # region Intensity Percentage
                intensity_percentage_f = Frame(self, bg=self['bg'])
                intensity_percentage_f.pack(side='top', padx=10, pady=0)
                self.ip_help_button = HelpButton(master=intensity_percentage_f, command=self._ip_help)
                self.ip_help_button.pack(side='left')
                self.intensity_percentage_label = Label(intensity_percentage_f, text='Intensity Percentage Calculation',
                                                        bg=self['bg'], anchor='w', width=40)
                self.intensity_percentage_label.pack(side='left', padx=5)
                # endregion

                # region Mechanical Alignment
                mech_align_f = Frame(self, bg=self['bg'])
                mech_align_f.pack(side='top', padx=10, pady=5)
                self.m_a_help_button = HelpButton(master=mech_align_f, command=self._ma_help)
                self.m_a_help_button.pack(side='left')
                self.mech_align_label = Label(mech_align_f, text='Mechanical Alignment', bg=self['bg'], anchor='w',
                                              width=40)
                self.mech_align_label.pack(side='left', padx=5)
                # endregion

                self._intensity_level_attachment_callback = None

            def _hw_help(self):
                self._hw_help_button.disable()
                PowerPointWindow(master=self, title='CLS2 HW',
                                 close_command=self._hw_help_button.enable,
                                 image_dir_en='images\\CLS2 HW\\en',
                                 image_dir_cn='images\\CLS2 HW\\cn')

            def _sw_help(self):
                self._sw_help_button.disable()
                PowerPointWindow(master=self, title='CLS2 HW',
                                 close_command=self._sw_help_button.enable,
                                 image_dir_en='images\\CLS2 SW\\en',
                                 image_dir_cn='images\\CLS2 SW\\cn')

            def _hsm_help(self):
                self.h_s_m_help_button.disable()
                PowerPointWindow(master=self, title='CLS2 High Speed Mode',
                                 close_command=self.h_s_m_help_button.enable,
                                 image_dir_en='images\\CLS2 high speed mode\\en',
                                 image_dir_cn='images\\CLS2 high speed mode\\cn')

            def _ip_help(self):
                self.ip_help_button.disable()
                PowerPointWindow(master=self, title='CLS2 Intensity Percentage',
                                 close_command=self.ip_help_button.enable,
                                 attachment=self.open_intensity_level_attachment, attach_page=5,
                                 image_dir_en='images/intensity_level')

            def _ma_help(self):
                self.m_a_help_button.disable()
                PowerPointWindow(master=self, title='Mechanical Alignment',
                                 close_command=self.m_a_help_button.enable,
                                 image_dir_en='images\\CLS2 Mechanical Alignment\\en',
                                 image_dir_cn='images\\CLS2 Mechanical Alignment\\cn')

            def open_intensity_level_attachment(self):
                if self._intensity_level_attachment_callback is not None:
                    self._intensity_level_attachment_callback()

            def set_intensity_level_attachment_callback(self, cmd):
                self._intensity_level_attachment_callback = cmd

        class FSSFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.label = Label(self, text='FSS Series', bg='#fffce1', anchor='w', width=40)
                self.label.pack(side='top', anchor='w')

                # region FSS Hardware
                fss_hw_f = Frame(self, bg=self['bg'])
                fss_hw_f.pack(side='top', padx=10, pady=5)
                self.hw_help_button = HelpButton(master=fss_hw_f, command=self._hw_help)
                self.hw_help_button.pack(side='left')
                Label(fss_hw_f, text='FSS Hardware', bg=self['bg'], anchor='w', width=40).pack(side='left', padx=5)
                # endregion

                # region FSS Software
                fss_sw_f = Frame(self, bg=self['bg'])
                fss_sw_f.pack(side='top', padx=10, pady=5)
                self.sw_help_button = HelpButton(master=fss_sw_f, command=self._sw_help)
                self.sw_help_button.pack(side='left')
                Label(fss_sw_f, text='FSS Software', bg=self['bg'], anchor='w', width=40).pack(side='left', padx=5)
                # endregion

                # region FSS Firmware
                fss_fw_f = Frame(self, bg=self['bg'])
                fss_fw_f.pack(side='top', padx=10, pady=5)
                self.fw_help_button = HelpButton(master=fss_fw_f, command=self._fw_help)
                self.fw_help_button.pack(side='left')
                Label(fss_fw_f, text='FSS Firmware', bg=self['bg'], anchor='w', width=40).pack(side='left', padx=5)
                # endregion

                # region FSS Calibration
                fss_cal_f = Frame(self, bg=self['bg'])
                fss_cal_f.pack(side='top', padx=10, pady=5)
                self.cal_help_button = HelpButton(master=fss_cal_f, command=self._cal_help)
                self.cal_help_button.pack(side='left')
                Label(fss_cal_f, text='FSS Calibration', bg=self['bg'], anchor='w', width=40).pack(side='left', padx=5)
                # endregion

                # region FSS Commissioning
                fss_com_f = Frame(self, bg=self['bg'])
                fss_com_f.pack(side='top', padx=10, pady=5)
                self.com_help_button = HelpButton(master=fss_com_f, command=self._com_help)
                self.com_help_button.pack(side='left')
                Label(fss_com_f, text='FSS Commissioning', bg=self['bg'], anchor='w', width=40).pack(side='left',
                                                                                                     padx=5)
                # endregion

                # region FSS Measurement
                meas_com_f = Frame(self, bg=self['bg'])
                meas_com_f.pack(side='top', padx=10, pady=5)
                self.meas_help_button = HelpButton(master=meas_com_f, command=self._meas_help)
                self.meas_help_button.pack(side='left')
                Label(meas_com_f, text='FSS Measurement', bg=self['bg'], anchor='w', width=40).pack(side='left', padx=5)
                # endregion

            def _hw_help(self):
                self.hw_help_button.disable()
                PowerPointWindow(master=self, title='FSS Hardware', close_command=self.hw_help_button.enable,
                                 image_dir_en='images\\FSS\\FSS Hardware\\en',
                                 image_dir_cn='images\\FSS\\FSS Hardware\\cn')

            def _sw_help(self):
                self.sw_help_button.disable()
                PowerPointWindow(master=self, title='FSS Software', close_command=self.sw_help_button.enable,
                                 image_dir_en='images\\FSS\\FSS Software\\en',
                                 image_dir_cn='images\\FSS\\FSS Software\\cn')

            def _fw_help(self):
                self.fw_help_button.disable()
                PowerPointWindow(master=self, title='FSS Firmware', close_command=self.fw_help_button.enable,
                                 image_dir_en='images\\FSS\\FSS Firmware\\en',
                                 image_dir_cn='images\\FSS\\FSS Firmware\\cn')

            def _cal_help(self):
                self.cal_help_button.disable()
                PowerPointWindow(master=self, title='FSS Calibration', close_command=self.cal_help_button.enable,
                                 image_dir_en='images\\FSS\\FSS Calibration\\en',
                                 image_dir_cn='images\\FSS\\FSS Calibration\\cn')

            def _com_help(self):
                self.com_help_button.disable()
                PowerPointWindow(master=self, title='FSS Commissioning', close_command=self.com_help_button.enable,
                                 image_dir_en='images\\FSS\\FSS Commissioning\\en',
                                 image_dir_cn='images\\FSS\\FSS Commissioning\\cn')

            def _meas_help(self):
                self.meas_help_button.disable()
                PowerPointWindow(master=self, title='FSS Measurement', close_command=self.meas_help_button.enable,
                                 image_dir_en='images\\FSS\\FSS Measurement\\en',
                                 image_dir_cn='images\\FSS\\FSS Measurement\\cn')

        class OthersFrame(Frame):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.label = Label(self, text='Others', bg='#fffce1', anchor='w', width=40)
                self.label.pack(side='top', anchor='w')

                # region Linearity & Repeatability
                linearity_f = Frame(self, bg=self['bg'])
                linearity_f.pack(side='top', padx=10, pady=5)
                self.linearity_help_button = HelpButton(master=linearity_f, command=self._linearity_help)
                self.linearity_help_button.pack(side='left')
                Label(linearity_f, text='Linearity & Repeatability', bg=self['bg'], anchor='w', width=40).pack(side='left', padx=5)
                # endregion

            def _linearity_help(self):
                self.linearity_help_button.disable()
                PowerPointWindow(master=self, title='Linearity & Repeatability', close_command=self.linearity_help_button.enable,
                                 image_dir_en='images\\linearity_repeatability\\en',
                                 image_dir_cn='images\\linearity_repeatability\\cn')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            _frame = Frame(self, bg=self['bg'])
            _frame.pack(side='left', anchor='n', padx=20, pady=20)
            self.cls2_f = self.CLS2Frame(_frame, bg=self['bg'])
            self.cls2_f.pack(side='top', anchor='w')

            self.fss_f = self.FSSFrame(_frame, bg=self['bg'])
            self.fss_f.pack(side='top', anchor='w', pady=10)

            self.others_f = self.OthersFrame(_frame, bg=self['bg'])
            self.others_f.pack(side='top', anchor='w')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style = ttk.Style()
        style.layout("Tab", [('Notebook.tab', {'sticky': 'nswe', 'children': [('Notebook.padding',
                                                                               {'side': 'top', 'sticky': 'nswe',
                                                                                'children': [('Notebook.label',
                                                                                              {'side': 'top',
                                                                                               'sticky': ''})], })], })])
        # region Notebook
        nb_h = self['height']
        self.notebook = ttk.Notebook(self, width=self['width'], height=nb_h)
        self.notebook.pack(side='top', fill='both')
        self.introduction_p = self.IntroductionPage(self.notebook, bg='#daeffd')
        self.connection_p = self.ConnectionPage(self.notebook, bg='#daeffd')
        self.init_p = self.InitialPage(self.notebook, bg='#daeffd')
        self.focus_p = self.FocusPage(self.notebook, bg='#daeffd')
        self.trigger_test_p = self.TriggerTestPage(self.notebook, bg='#daeffd')
        self.trigger_scan_p = self.TriggerScanPage(self.notebook, bg='#daeffd')
        self.multi_layer_setting_p = self.MultiLayerSetting(self.notebook, bg='#daeffd')
        self.others_p = self.Others(self.notebook, bg='#daeffd')
        # self.introduction_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        # self.connection_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        # self.init_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        # self.focus_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        # self.trigger_test_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        # self.trigger_scan_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        # self.multi_layer_setting_p.grid(column=0, row=0, ipadx=0, pady=0, sticky='wn')
        self.introduction_p.pack(side='top')
        self.connection_p.pack(side='top')
        self.init_p.pack(side='top')
        self.focus_p.pack(side='top')
        self.trigger_test_p.pack(side='top')
        self.trigger_scan_p.pack(side='top')
        self.multi_layer_setting_p.pack(side='top')
        self.others_p.pack(side='left')
        self.notebook.add(self.introduction_p, text='Introduction')
        self.notebook.add(self.connection_p, text='Connection')
        self.notebook.add(self.init_p, text='Initial')
        self.notebook.add(self.focus_p, text='Focus')
        self.notebook.add(self.trigger_test_p, text='Trigger Test')
        self.notebook.add(self.trigger_scan_p, text='Trigger Scan')
        self.notebook.add(self.multi_layer_setting_p, text='Multi-Layer Setting')
        self.notebook.add(self.others_p, text='Others')
        # self.notebook.add(self.parameter_optimize_p, text='Parameter Optimize')
        self.notebook.select(self.notebook.tabs()[0])
        # endregion


class _CommandFrame(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['bg'] = '#f4f7fc'
        main_f = Frame(self, bg=self['bg'])
        main_f.grid_columnconfigure(1, weight=1)
        main_f.pack(side='top', fill='x', expand=True)
        Label(main_f, bg=self['bg'], text='Command:').grid(column=0, row=0, sticky='nw')
        self.command_entry = Entry(main_f)
        self.command_entry.bind('<Return>', lambda x: self.entry_on_enter())
        self.command_entry.bind('<Up>', lambda x: self.entry_on_up_arrow())
        self.command_entry.bind('<Down>', lambda x: self.entry_on_down_arrow())
        self.command_entry.grid(column=1, row=0, sticky='nwe')
        Label(main_f, bg=self['bg'], text='Response:').grid(column=0, row=1, sticky='nw')
        self.command_textbox = ScrolledText(master=self, height=235)
        self.command_textbox.state('disabled')
        self.command_textbox.pack(side='top', fill='x')

        self._entry_callback = None
        self.save_list = []
        self.display_index = 0
        self.save_list_max_count = 10

    def set_entry_callback(self, cmd):
        self._entry_callback = cmd

    def clear_entry_callback(self):
        self._entry_callback = None

    def entry_on_enter(self):
        txt = self.command_entry.get()
        if txt:
            if self._entry_callback:
                self._entry_callback()
            self.save_list.append(txt)
            self.display_index = 0
            if len(self.save_list) > self.save_list_max_count:
                self.save_list.pop(0)
            self.clear_entry_text()

    def entry_on_up_arrow(self):
        if self.save_list:
            try:
                self.display_index -= 1
                self.insert_entry(self.save_list[self.display_index])
            except IndexError:
                self.display_index += 1

    def entry_on_down_arrow(self):
        if self.save_list:
            try:
                self.display_index += 1
                self.insert_entry(self.save_list[self.display_index])
            except IndexError:
                self.display_index -= 1

    def clear_entry_text(self):
        self.command_entry.delete(0, 'end')

    def insert_entry(self, val):
        self.command_entry.delete(0, 'end')
        self.command_entry.insert('end', val)

    def get_entry(self):
        return self.command_entry.get()

    def insert_textbox(self, val):
        self.command_textbox.insert(val)
        self.command_textbox.focus_last_line()


def switch_to_english_input():
    input_language = ctypes.windll.user32.GetKeyboardLayout(0)
    if hex(input_language & 0xFFFF) != "0x409":
        PostMessage(HWND_BROADCAST, WM_INPUTLANGCHANGEREQUEST, 0, 0x0409)


def validate_entry_digit_decimal_p(p):
    if p.count('.') <= 1:
        parts = p.split('.')
        if parts[-1] == '':
            parts.pop(-1)
        if all(part.isdigit() for part in parts):
            return True
    return False


def validate_entry_digit(p):
    if p.isdigit() or len(p) == 0:
        return True
    return False


def run_as_admin_faq():
    PowerPointWindow(title='Failed to open FAQ Guide', image_dir_en='images/program_start/en',
                     image_dir_cn='images/program_start/cn', close_command=lambda: sys.exit())


if __name__ == "__main__":
    gui = MainGUI()
    gui.mainloop()
