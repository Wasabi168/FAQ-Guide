from tkinter import Frame, Tk, Button, Scale
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
from threading import Thread, Event
from queue import Queue
from time import sleep
import numpy as np


class BasicMatplot(Frame):
    class CustomNavigationToolbar(NavigationToolbar2Tk):
        def __init__(self, *args, bg_color='blue', **kwargs):
            super().__init__(*args, **kwargs)

            # 取得標籤物件
            label = self._message_label

            # 設定標籤背景顏色
            label.config(bg=bg_color)

    def __init__(self, fig_size=(5, 4), tool_bar=True, bg_color='white', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unit_str = ''
        self.fig = plt.figure(figsize=fig_size, dpi=80)
        self.fig.subplots_adjust(left=0.057, right=0.97, top=0.974, bottom=0.057)
        self.fig.set_facecolor(bg_color)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
        self.canvas.draw()
        if tool_bar:
            # pack_toolbar=False will make it easier to use a layout manager later on.
            self.toolbar = self.CustomNavigationToolbar(self.canvas, self, bg_color=bg_color)
            self.toolbar.configure(bg=bg_color)
            self.toolbar.update()
            self.toolbar.pack(side='bottom', fill='x')

        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

        self.ax = self.fig.add_subplot()

        # 連接滑鼠游標事件
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        self._is_data = None
        self.data_buffer = None
        self.mesh = None

    # def plot(self, data):
    #     self.ax.clear()
    #     self.ax.pcolormesh(data)
    #     self.ax.invert_yaxis()  # 反轉y軸
    #     self.fig.canvas.draw_idle()
    #     self._is_data = True
    #     self.data_buffer = data

    # Added on 2024.10.14: for faster plotting
    def plot(self, data):
        if self._is_data is None:
            # 初次繪圖，使用 pcolormesh
            self.mesh = self.ax.pcolormesh(data, cmap='viridis')
            self.ax.invert_yaxis()  # 反轉y軸
            self.fig.canvas.draw_idle()
            self._is_data = True
        else:
            # 更新圖像數據，避免清空重畫
            self.mesh.set_array(data.ravel())  # ravel展平數據以匹配pcolormesh的要求
            self.fig.canvas.draw_idle()

        self.data_buffer = data

    def clear_plot(self):
        self.mesh = None
        self._is_data = None
        self.data_buffer = None
        self.ax.clear()  # 清除 ax 內容
        white_data = np.ones((10, 10))  # 創建一個全一（代表全白）的矩陣，大小依您的需求來調整
        self.ax.pcolormesh(white_data, cmap='gray', vmin=0, vmax=1)  # 繪製全白（全零）的圖像
        self.ax.invert_yaxis()  # 如果需要，反轉 y 軸
        self.fig.canvas.draw_idle()  # 重新繪製

    def set_unit_str(self, unit_str):
        self._unit_str = unit_str

    def reset_scale(self):
        self.ax.autoscale()
        self.fig.canvas.draw_idle()

    def on_mouse_move(self, event):
        if event.inaxes is not None and self._is_data:
            x, y = event.xdata, event.ydata
            z = int(self.data_buffer[int(y), int(x)])  # 取得對應的 z 值
            self.toolbar.set_message('x={:.2f}, y={:.2f}, z={:.0f}{}'.format(x, y, z, self._unit_str))
        else:
            self.toolbar.set_message('')


class BasicScatter(Frame):
    def __init__(self, fig_size=(5, 4), tool_bar=True, title='Demo', x_label='', y_label='', dot_size=0.1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fig = plt.figure(figsize=fig_size, dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
        self.canvas.draw()

        if tool_bar:
            # pack_toolbar=False will make it easier to use a layout manager later on.
            self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
            self.toolbar.update()
            self.toolbar.pack(side='bottom', fill='x')

        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

        # Set up the figure and axes...
        self.ax = self.fig.add_subplot()
        self.ax.set_title(title)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self._dot_size = dot_size
        self.scat = None

    def setup_plot(self):
        """Initial drawing of the scatter plot."""
        self.scat = self.ax.scatter([], [], c='#084484', s=self._dot_size, vmin=0, vmax=1, cmap="jet")
        self.ax.axis([0, 10, 0, 10])

    def set_x_lim(self, left_val: int, right_val: int) -> None:
        self.ax.set_xlim(left_val, right_val)

    def get_x_lim(self):
        return self.ax.get_xlim()

    def set_y_lim(self, bottom_val: int, top_val: int) -> None:
        self.ax.set_ylim(bottom_val, top_val)

    def get_y_lim(self):
        return self.ax.get_ylim()

    def set_scatter(self, offsets):
        """Update the scatter plot."""
        self.scat.set_offsets(offsets)
        self.fig.canvas.draw_idle()


class SpectrumPlot(Frame):
    def __init__(self, fig_size=(5, 4), tool_bar=True, title='Demo', x_label='', y_label='', dot_size=0.1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fig = plt.figure(figsize=fig_size, dpi=80)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # A tk.DrawingArea.
        self.canvas.draw()

        if tool_bar:
            # pack_toolbar=False will make it easier to use a layout manager later on.
            self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
            self.toolbar.update()
            self.toolbar.pack(side='bottom', fill='x')

        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)

        # Set up the figure and axes...
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.ax.grid(zorder=0)

        self.line = None

    def plot(self, data):
        if self.line is None:
            x = np.arange(0, data.size)
            self.line, = self.ax.plot(x, data)

        self.line.set_ydata(data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

        # to flush the GUI events
        self.fig.canvas.flush_events()


class DynamicScatterPlot(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # Initialize the figure and axis
        self.fig, self.ax = plt.subplots(figsize=(7, 6), dpi=80)
        self.line, = self.ax.plot([], [], marker='o', linestyle='-', color='blue', markersize=5, label='1 CHRPort: Distance 1')

        # Set labels and title
        self.ax.set_xlabel('Measuring Point')
        self.ax.set_ylabel('Distance')
        self.ax.set_title('MultiChannel Profile View')

        # Set y-axis limits
        self.ax.set_ylim(0, 600)

        # Add legend
        self.ax.legend()

        # Add grid
        self.ax.grid(True)

        # Create a FigureCanvasTkAgg widget to display the plot in the tkinter frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True)

    def update_plot(self, y, auto_scale_y=False):
        # Generate x data based on the length of y
        x = np.arange(1, len(y) + 1)
        # Update data for the plot
        if len(y) > 1200:
            y = y[:1200]  # Truncate if necessary
            x = x[:1200]  # Truncate x accordingly
        self.line.set_data(x, y)
        self.ax.set_xlim(min(x)-max(x)*0.03, max(x)*1.03)  # Adjust x-axis limits dynamically
        if auto_scale_y:
            max_range = max(y).astype(np.int32) - min(y).astype(np.int32)
            self.ax.set_ylim(min(y)-max_range*0.03, max(y)+max_range*0.03)
        self.canvas.draw()

    def update_label(self, new_label):
        # Update the label of the line
        self.line.set_label(f'1 CHRPort: {new_label}')
        self.ax.legend()  # Update legend to reflect the new label
        self.canvas.draw()

    def update_y_lim(self, y_lim):
        self.ax.set_ylim(y_lim[0], y_lim[1])


if __name__ == "__main__":
    pass
    # root = Tk()
    # root.wm_title("Embedding in Tk")
    # matplot = BasicMatplot(master=root, default_animate=True)
    # matplot.pack()
    # root.mainloop()
    # test_scatter()
