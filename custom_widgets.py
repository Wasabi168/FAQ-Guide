from tkinter import Frame, Button, Toplevel, Label, StringVar
from scrolled_text import ScrolledText
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk
import win32clipboard
import win32con
import os
import io


class HelpButton(Frame):
    def __init__(self, command=None, size=(12, 12), *args, **kwargs):
        super().__init__(*args, **kwargs)
        image = Image.open('images/help_btn.png')
        resize_image = image.resize(size)
        self.btn_img = ImageTk.PhotoImage(resize_image)
        self.help_btn = Button(self, image=self.btn_img, bg='#e0ecfc', relief='groove', command=command)
        self.help_btn.bind("<Enter>", self.on_enter)
        self.help_btn.bind("<Leave>", self.on_leave)
        self.help_btn.pack()

    def on_enter(self, event):
        self.help_btn['background'] = 'green'

    def on_leave(self, event):
        self.help_btn['background'] = '#e0ecfc'

    def enable(self):
        self.help_btn['state'] = 'normal'

    def disable(self):
        self.help_btn['state'] = 'disable'


class NoteButton(Frame):
    def __init__(self, command=None, size=(14, 14), *args, **kwargs):
        super().__init__(*args, **kwargs)
        image = Image.open('images/note_btn.png')
        resize_image = image.resize(size)
        self.btn_img = ImageTk.PhotoImage(resize_image)
        self.note_btn = Button(self, image=self.btn_img, bg='#e0ecfc', relief='groove', command=command)
        self.note_btn.bind("<Enter>", self.on_enter)
        self.note_btn.bind("<Leave>", self.on_leave)
        self.note_btn.pack()

    def on_enter(self, event):
        self.note_btn['background'] = 'green'

    def on_leave(self, event):
        self.note_btn['background'] = '#e0ecfc'

    def state(self, state):
        self.note_btn['state'] = 'normal' if state else 'disable'

    def enable(self):
        self.note_btn['state'] = 'normal'

    def disable(self):
        self.note_btn['state'] = 'disable'


class AttachButton(Frame):
    def __init__(self, command=None, size=(14, 14), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normal_color = '#ffffe1'
        self._highlight_color = '#68b868'
        image = Image.open('images/attachment.png')
        resize_image = image.resize(size)
        self.btn_img = ImageTk.PhotoImage(resize_image)
        self.btn = Button(self, image=self.btn_img, bg=self._normal_color, relief='groove', command=command)
        self.btn.bind("<Enter>", self.on_enter)
        self.btn.bind("<Leave>", self.on_leave)
        self.btn.pack()

    def on_enter(self, event):
        self.btn['background'] = self._highlight_color

    def on_leave(self, event):
        self.btn['background'] = self._normal_color


class CopyButton(Frame):
    def __init__(self, command=None, size=(15, 15), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._command = command
        self._animation_speed = 2
        self._normal_color = '#ffffe1'
        self._highlight_color = '#68b868'
        self._copy_img = Image.open('images/copy_btn.png').resize(size)
        self._check_img = Image.open('images/check_btn.png').resize(size)
        self._current_width, self._current_height = self._copy_img.size
        self._original_width, self._original_height = self._check_img.size
        self._copy_btn_img = ImageTk.PhotoImage(self._copy_img)
        self._check_btn_img = ImageTk.PhotoImage(self._check_img)
        self._btn = Button(self, image=self._copy_btn_img, bg=self._normal_color, relief='groove', compound=tk.LEFT,
                           command=self.btn_command, height=15, width=15)
        self._btn.bind("<Enter>", self._on_enter)
        self._btn.bind("<Leave>", self._on_leave)
        self._btn.pack()

        self._shrink_after_id = None
        self._enlarge_after_id = None
        self._count_after_id = None
        self._count_down = 0
        self._animation_flag = False

    def invoke(self):
        self._btn.invoke()

    def _shrink_copy_img(self):
        self._current_width -= self._animation_speed  # 減小寬度
        self._current_height -= self._animation_speed  # 減小高度
        if self._current_width > 0 and self._current_height > 0:
            resized_image = self._copy_img.resize((self._current_width, self._current_height), Image.ANTIALIAS)
            new_photo = ImageTk.PhotoImage(resized_image)
            self._btn.config(image=new_photo)
            self._btn.image = new_photo   # 需要保存圖片對象的引用，否則圖片會被垃圾回收
            self._shrink_after_id = self.after(8, self._shrink_copy_img)  # 每50毫秒調用一次shrink_image函數，創建動畫效果
        else:
            resized_image = self._copy_img.resize((1, 1), Image.ANTIALIAS)
            new_photo = ImageTk.PhotoImage(resized_image)
            self._btn.config(image=new_photo)
            if self._shrink_after_id:
                self.after_cancel(self._shrink_after_id)
            self._enlarge_check_img()

    def _enlarge_check_img(self):
        self._current_width += self._animation_speed
        self._current_height += self._animation_speed
        if self._current_width < self._original_width and self._current_height < self._original_height:
            resized_image = self._check_img.resize((self._current_width, self._current_height), Image.ANTIALIAS)
            new_photo = ImageTk.PhotoImage(resized_image)
            self._btn.config(image=new_photo)
            self._btn.image = new_photo   # 需要保存圖片對象的引用，否則圖片會被垃圾回收
            self._enlarge_after_id = self.after(8, self._enlarge_check_img)  # 每50毫秒調用一次shrink_image函數，創建動畫效果
        else:
            self._btn.config(image=self._check_btn_img)
            if self._enlarge_after_id:
                self.after_cancel(self._enlarge_after_id)
            self._count_down_to_copy_img()

    def _count_down_to_copy_img(self):
        # 10 times 100ms = 1 sec
        if self._count_down < 10:
            self._count_down += 1
            self._count_after_id = self.after(100, self._count_down_to_copy_img)
        else:
            self._btn.config(image=self._copy_btn_img)
            self._count_down = 0
            if self._count_after_id:
                self.after_cancel(self._count_after_id)
            self._animation_flag = False

    def btn_command(self):
        if not self._animation_flag:
            self._btn['background'] = self._normal_color
            self._current_width, self._current_height = self._copy_img.size
            if self._command is not None:
                self._command()
            self._animation_flag = True
            self._shrink_copy_img()

    def _on_enter(self, event):
        if not self._animation_flag:
            self._btn['background'] = self._highlight_color

    def _on_leave(self, event):
        if not self._animation_flag:
            self._btn['background'] = self._normal_color


class NextButton(Frame):
    def __init__(self, command=None, size=(15, 15), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normal_color = '#ffffe1'
        self._highlight_color = 'green'
        image = Image.open('images/next_arrow.png')
        resize_image = image.resize(size)
        self.btn_img = ImageTk.PhotoImage(resize_image)
        self.btn = Button(self, image=self.btn_img, bg=self._normal_color, relief='groove', command=command)
        self.btn.bind("<Enter>", self.on_enter)
        self.btn.bind("<Leave>", self.on_leave)
        self.btn.pack()

    def on_enter(self, event):
        self.btn['background'] = self._highlight_color

    def on_leave(self, event):
        self.btn['background'] = self._normal_color

    def enable(self):
        self.btn['state'] = 'normal'

    def disable(self):
        self.btn['state'] = 'disable'


class PrevButton(Frame):
    def __init__(self, command=None, size=(15, 15), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normal_color = '#ffffe1'
        self._highlight_color = 'green'
        image = Image.open('images/previous_arrow.png')
        resize_image = image.resize(size)
        self.btn_img = ImageTk.PhotoImage(resize_image)
        self.btn = Button(self, image=self.btn_img, bg=self._normal_color, relief='groove', command=command)
        self.btn.bind("<Enter>", self.on_enter)
        self.btn.bind("<Leave>", self.on_leave)
        self.btn.pack()

    def on_enter(self, event):
        self.btn['background'] = self._highlight_color

    def on_leave(self, event):
        self.btn['background'] = self._normal_color

    def enable(self):
        self.btn['state'] = 'normal'

    def disable(self):
        self.btn['state'] = 'disable'


class RoundCornerButton(Button):
    def __init__(self, size='L', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['takefocus'] = False
        if size.upper() == 'L':
            normal_img_path = 'images/round_corner_btn_normal_l.png'
            active_img_path = 'images/round_corner_btn_active_l.png'
        elif size.upper() == 'M':
            normal_img_path = 'images/round_corner_btn_normal_m.png'
            active_img_path = 'images/round_corner_btn_active_m.png'
        elif size.upper() == 'S':
            normal_img_path = 'images/round_corner_btn_normal_s.png'
            active_img_path = 'images/round_corner_btn_active_s.png'
        elif size.upper() == 'XS':
            normal_img_path = 'images/round_corner_btn_normal_xs.png'
            active_img_path = 'images/round_corner_btn_active_xs.png'
        elif size.upper() == 'LF':
            normal_img_path = 'images/round_corner_btn_normal_long_flat.png'
            active_img_path = 'images/round_corner_btn_active_long_flat.png'
        else:
            normal_img_path = 'images/round_corner_btn_normal_l.png'
            active_img_path = 'images/round_corner_btn_active_l.png'
        normal_resized_image = Image.open(normal_img_path).resize((self['width'], self['height']))
        active_resized_image = Image.open(active_img_path).resize((self['width'], self['height']))
        self.normal_button_img = ImageTk.PhotoImage(normal_resized_image)
        self.active_button_img = ImageTk.PhotoImage(active_resized_image)

        self.configure(image=self.normal_button_img, relief='flat', activebackground=self['bg'], compound='center',
                       borderwidth=0)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind('<Button>', self.on_click)
        self.bind('<ButtonRelease>', self.on_release)

    def on_enter(self, event):
        self['image'] = self.active_button_img

    def on_leave(self, event):
        self['image'] = self.normal_button_img

    def on_click(self, event):
        self['image'] = self.normal_button_img
        self['relief'] = 'flat'

    def on_release(self, event):
        self['image'] = self.active_button_img


class RoundCornerButtonGR(Button):
    def __init__(self, size='M', normal='1_1', green='1_1', red='1_1', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['takefocus'] = False
        if normal == '1_1':
            normal_img_path = 'images/round_corner_btn_normal_m.png'
            active_img_path = 'images/round_corner_btn_active_m.png'
        else:
            normal_img_path = 'images/round_corner_btn_normal_m_2.png'
            active_img_path = 'images/round_corner_btn_active_m_2.png'
        if green == '1_1':
            g_normal_img_path = 'images/round_corner_green_btn_normal_m.png'
            g_active_img_path = 'images/round_corner_green_btn_active_m.png'
        elif green == '1_2':
            g_normal_img_path = 'images/round_corner_green_btn_normal_m_2.png'
            g_active_img_path = 'images/round_corner_green_btn_active_m_2.png'
        else:
            g_normal_img_path = 'images/round_corner_green2_btn_normal_m.png'
            g_active_img_path = 'images/round_corner_green2_btn_active_m.png'
        if red == '1_1':
            r_normal_image_path = 'images/round_corner_red_btn_normal_m.png'
            r_active_image_path = 'images/round_corner_red_btn_active_m.png'
        else:
            r_normal_image_path = 'images/round_corner_red_btn_normal_m_2.png'
            r_active_image_path = 'images/round_corner_red_btn_active_m_2.png'
        normal_resized_image = Image.open(normal_img_path).resize((self['width'], self['height']))
        active_resized_image = Image.open(active_img_path).resize((self['width'], self['height']))
        g_normal_resized_image = Image.open(g_normal_img_path).resize((self['width'], self['height']))
        g_active_resized_image = Image.open(g_active_img_path).resize((self['width'], self['height']))
        r_normal_resized_image = Image.open(r_normal_image_path).resize((self['width'], self['height']))
        r_active_resized_image = Image.open(r_active_image_path).resize((self['width'], self['height']))
        self.normal_button_img = ImageTk.PhotoImage(normal_resized_image)
        self.active_button_img = ImageTk.PhotoImage(active_resized_image)
        self.g_normal_button_img = ImageTk.PhotoImage(g_normal_resized_image)
        self.g_active_button_img = ImageTk.PhotoImage(g_active_resized_image)
        self.r_normal_button_img = ImageTk.PhotoImage(r_normal_resized_image)
        self.r_active_button_img = ImageTk.PhotoImage(r_active_resized_image)

        self.configure(image=self.normal_button_img, relief='flat', activebackground=self['bg'], compound='center',
                       borderwidth=0)
        self._state = 'n'
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind('<Button>', self.on_click)
        self.bind('<ButtonRelease>', self.on_release)

    def text(self, txt):
        self.configure(text=txt)

    def cmd(self, cmd):
        self.configure(command=cmd)

    def disable(self):
        self.configure(state='disabled')

    def enable(self):
        self.configure(state='normal')

    def set_button_color(self, color):
        if color == 'g':
            self._state = 'g'
            self['image'] = self.g_normal_button_img
        elif color == 'r':
            self._state = 'r'
            self['image'] = self.r_normal_button_img
        else:
            self._state = 'n'
            self['image'] = self.normal_button_img

    def get_button_color(self):
        return self._state

    def on_enter(self, event):
        if self._state == 'g':
            self['image'] = self.g_active_button_img
        elif self._state == 'r':
            self['image'] = self.r_active_button_img
        else:
            self['image'] = self.active_button_img

    def on_leave(self, event):
        if self._state == 'g':
            self['image'] = self.g_normal_button_img
        elif self._state == 'r':
            self['image'] = self.r_normal_button_img
        else:
            self['image'] = self.normal_button_img

    def on_click(self, event):
        if self._state == 'g':
            self['image'] = self.g_normal_button_img
        elif self._state == 'r':
            self['image'] = self.r_normal_button_img
        else:
            self['image'] = self.normal_button_img

    def on_release(self, event):
        if self._state == 'g':
            self['image'] = self.g_active_button_img
        elif self._state == 'r':
            self['image'] = self.r_active_button_img
        else:
            self['image'] = self.active_button_img


class ImageDescriptionWindow(Toplevel):
    def __init__(self, size: list, image_en=None, image_cn=None, close_command=None, title='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.close_command = close_command
        self['bg'] = 'white'
        self._default_lan = 'en'
        self._btn_enabled_color = 'SystemButtonFace'
        self._btn_disabled_color = '#ffffe1'
        self.title(title)
        size[1] += 49
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = size[0] + 2 * frm_width
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = size[1] + titlebar_height + frm_width
        x = self.winfo_screenwidth() // 2 - win_width // 2
        y = self.winfo_screenheight() // 2 - win_height // 2
        self.geometry('{}x{}+{}+{}'.format(size[0], size[1], x, y))

        self.resizable(False, False)
        # self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())

        self._image_en = image_en
        self._image_cn = image_cn
        self._image_label = Label(self, image=self._image_en, height=win_height-49, bg='white', anchor=tk.N)
        self._image_label.pack(side='top', anchor=tk.W)

        language_btn_f = Frame(self, bg='#ffffe1')
        language_btn_f.pack(side='top', fill='x')
        Label(language_btn_f, bg='#ffffe1').pack(side='left', fill='x')
        if image_cn is not None:
            self.cn_btn = Button(language_btn_f, text='CN', font=('calibri', 8), bg='#ffffe1', relief='groove',
                                 command=lambda: self._language_btn_clicked('cn'))
            self.cn_btn.pack(side='right')
        if image_en is not None:
            self.en_btn = Button(language_btn_f, text='EN', font=('calibri', 8), bg='#ffffe1', relief='groove',
                                 command=lambda: self._language_btn_clicked('en'))
            self.en_btn.pack(side='right', padx=1)
        self._set_language(self._default_lan)
        RoundCornerButton(master=self, text='Close Window', size='lf', width=size[0], height=25,
                          command=self._on_close, bg=self['bg']).pack(side='top', fill='x')
        self.focus_set()

    def _on_close(self):
        self.destroy()
        if self.close_command is not None:
            self.close_command()

    def _set_language(self, lan):
        if lan == 'en':
            if self._image_en is not None:
                self.en_btn['relief'] = 'sunken'
                self.en_btn['bg'] = self._btn_enabled_color
            if self._image_cn is not None:
                self.cn_btn['relief'] = 'groove'
                self.cn_btn['bg'] = self._btn_disabled_color
        elif lan == 'cn':
            if self._image_en is not None:
                self.en_btn['relief'] = 'groove'
                self.en_btn['bg'] = self._btn_disabled_color
            if self._image_cn is not None:
                self.cn_btn['relief'] = 'sunken'
                self.cn_btn['bg'] = self._btn_enabled_color

    def _language_btn_clicked(self, lan):
        if lan == 'en':
            if self.en_btn['relief'] == 'groove':
                self._image_label.config(image=self._image_en)
                self._set_language('en')
        elif lan == 'cn':
            if self.cn_btn['relief'] == 'groove':
                self._image_label.config(image=self._image_cn)
                self._set_language('cn')


class ImageFrame(tk.Frame):
    def __init__(self, master=None, image_path=''):
        super().__init__(master)
        self.master = master
        self.image_path = image_path
        self.image = tk.PhotoImage(file=self.image_path)
        self.PIL_img = Image.open(self.image_path)
        self.label = tk.Label(self, image=self.image)
        self.label.pack()


class PowerPointWindow(Toplevel):
    def __init__(self, image_dir_en: str = '', image_dir_cn: str = '', close_command=None, attachment=None,
                 attach_page: int = None, title='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.close_command = close_command
        self['bg'] = 'white'
        self._btn_enabled_color = 'SystemButtonFace'
        self._btn_disabled_color = '#ffffe1'
        self._default_lan = 'en'
        self._current_lan = self._default_lan
        self.title(title)
        self._attach_page = attach_page
        self.image_dir_en = image_dir_en
        self.image_dir_cn = image_dir_cn

        # Find the images with the given directory
        image_list_en = []
        for file in os.listdir(self.image_dir_en):
            if file.lower().startswith("slide") and file.lower().endswith(".png"):
                image_list_en.append(os.path.join(self.image_dir_en, file))

        image_list_cn = []
        if self.image_dir_cn:
            for file in os.listdir(self.image_dir_cn):
                if file.lower().startswith("slide") and file.lower().endswith(".png"):
                    image_list_cn.append(os.path.join(self.image_dir_cn, file))

        # Check the image size and set up the size of the window
        img = Image.open(image_list_en[0])
        size = [img.size[0], img.size[1]]
        size[1] += 55
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = size[0] + 2 * frm_width
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = size[1] + titlebar_height + frm_width
        x = self.winfo_screenwidth() // 2 - win_width // 2
        y = self.winfo_screenheight() // 2 - win_height // 2
        self.geometry('{}x{}+{}+{}'.format(size[0], size[1], x, y))

        # Set up the window
        self.resizable(False, False)
        # self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda e: self._on_close())

        # Set up the images
        image_f = tk.Frame(self)
        image_f.grid(column=0, row=0, sticky=tk.EW, columnspan=2)
        # self.images = [ImageFrame(image_f, i) for i in image_list_en]
        self.images = {'en': [ImageFrame(image_f, i) for i in image_list_en]}
        self._image_len = len(image_list_en)
        if image_list_cn:
            self.images['cn'] = [ImageFrame(image_f, i) for i in image_list_cn]
        self.current_image_index = 0
        self.images[self._default_lan][self.current_image_index].pack(side=tk.TOP, anchor=tk.W)

        # Set up the shortcuts
        if len(self.images[self._default_lan]) > 1:
            self.bind("<Left>", lambda e: self._show_previous_image())
            self.bind("<Up>", lambda e: self._show_previous_image())
            self.bind("<Right>", lambda e: self._show_next_image())
            self.bind("<Down>", lambda e: self._show_next_image())
            self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Control-C>", lambda e: self._on_ctrl_c())
        self.bind("<Control-c>", lambda e: self._on_ctrl_c())

        # Set up the navigation buttons
        nav_frame = tk.Frame(self, bg='white')
        nav_frame.grid(column=0, row=1, columnspan=2, sticky=tk.S)
        self.prev_button = PrevButton(master=nav_frame, command=self._show_previous_image)
        self.prev_button.disable()
        self.prev_button.pack(side=tk.LEFT, padx=3)
        self.page = StringVar()
        self.page.set('1 / {}'.format(len(self.images[self._default_lan])))
        page_number = Label(nav_frame, textvariable=self.page, bg='white')
        page_number.pack(side=tk.LEFT, padx=3)
        self.next_button = NextButton(master=nav_frame, command=self._show_next_image)
        if self._image_len == 1:
            self.next_button.disable()
        self.next_button.pack(side=tk.LEFT, padx=3)
        # Set up the copy button
        self.copy_btn = CopyButton(master=nav_frame, size=(15, 15), command=self._copy_img_to_clipboard)
        self.copy_btn.pack(side=tk.LEFT, padx=3)

        # Set up the attachment button
        attachment_frame = tk.Frame(self, bg='white')
        attachment_frame.grid(column=1, row=1, sticky=tk.SE, padx=int(size[0]/2 - 70))
        if attachment is not None:
            self.attachment_btn = AttachButton(master=attachment_frame, size=(15, 15), command=attachment)
        else:
            self.attachment_btn = None

        # Set up the language button
        language_f = tk.Frame(nav_frame, bg='white')
        language_f.pack(side=tk.RIGHT, padx=3)
        if self.image_dir_cn:
            self._cn_btn = Button(language_f, text='CN', font=('calibri', 8), bg='#ffffe1', relief='groove',
                                  command=lambda: self._language_btn_clicked('cn'))
            self._cn_btn.pack(side='right')
            self._en_btn = Button(language_f, text='EN', font=('calibri', 8), bg='#ffffe1', relief='groove',
                                  command=lambda: self._language_btn_clicked('en'))
            self._en_btn.pack(side='right', padx=1)
            ttk.Separator(language_f, orient='vertical').pack(side='right', fill='y', padx=5)
            self._set_language(self._default_lan)

        # Set up the close button
        RoundCornerButton(master=self, text='Close Window', size='lf', width=size[0], height=25,
                          command=self._on_close, bg=self['bg']).grid(column=0, row=2, sticky=tk.EW, columnspan=2)

        self.focus_set()
        self.mainloop()

    def _on_close(self):
        self.destroy()
        if self.close_command is not None:
            self.close_command()

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._show_previous_image()
        else:
            self._show_next_image()

    def _on_ctrl_c(self):
        self.copy_btn.invoke()

    def _copy_img_to_clipboard(self):
        output = io.BytesIO()
        # 將圖片保存到內存中的二進制流
        self.images[self._current_lan][self.current_image_index].PIL_img.save(output, format='BMP')
        data = output.getvalue()[14:]  # BMP文件頭部為14位元組，去除頭部資料

        # 打開剪貼簿
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        # 將圖片資料放入剪貼簿
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        # 關閉剪貼簿
        win32clipboard.CloseClipboard()

    def _show_previous_image(self):
        self.images[self._current_lan][self.current_image_index].pack_forget()
        self.current_image_index -= 1
        self.next_button.enable()
        if self.current_image_index < 0:
            self.current_image_index = 0
        if self.current_image_index == 0:
            self.prev_button.disable()
        else:
            self.prev_button.enable()
        self.images[self._current_lan][self.current_image_index].pack(side='top', anchor=tk.W)
        self.page.set('{} / {}'.format(str(int(self.current_image_index) + 1), self._image_len))
        self._attach_btn_pack()

    def _show_next_image(self):
        self.images[self._current_lan][self.current_image_index].pack_forget()
        self.current_image_index += 1
        self.prev_button.enable()
        if self.current_image_index >= self._image_len:
            self.current_image_index = self._image_len - 1
        if self.current_image_index == self._image_len - 1:
            self.next_button.disable()
        else:
            self.next_button.enable()
        self.images[self._current_lan][self.current_image_index].pack(side='top', anchor=tk.W)
        self.page.set('{} / {}'.format(str(int(self.current_image_index) + 1), self._image_len))
        self._attach_btn_pack()

    def _set_language(self, lan):
        self.images[self._current_lan][self.current_image_index].pack_forget()
        if lan == 'en':
            self._en_btn['relief'] = 'sunken'
            self._en_btn['bg'] = self._btn_enabled_color
            self._cn_btn['relief'] = 'groove'
            self._cn_btn['bg'] = self._btn_disabled_color
        elif lan == 'cn':
            self._en_btn['relief'] = 'groove'
            self._en_btn['bg'] = self._btn_disabled_color
            self._cn_btn['relief'] = 'sunken'
            self._cn_btn['bg'] = self._btn_enabled_color
        self._current_lan = lan
        self.images[lan][self.current_image_index].pack(side='top', anchor=tk.W)

    def _language_btn_clicked(self, lan):
        if lan == 'en':
            if self._en_btn['relief'] == 'groove':
                self._set_language('en')
        elif lan == 'cn':
            if self._cn_btn['relief'] == 'groove':
                self._set_language('cn')

    def _attach_btn_pack(self):
        if self.attachment_btn is not None:
            if self.current_image_index+1 == self._attach_page:
                self.attachment_btn.pack()
            else:
                self.attachment_btn.pack_forget()
