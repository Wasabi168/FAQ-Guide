from tkinter.ttk import Scrollbar
from tkinter import Text, Frame


class ScrolledText(Frame):
    def __init__(self, font='calibri 10', relief='sunken', borderwidth=1, scroll_bar=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ensure a consistent GUI size
        self.grid_propagate(False)
        # implement stretchability
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Text widget
        self.txt = Text(self, font=font, relief=relief, borderwidth=borderwidth)
        # if state:
        #     self.txt.configure(state=state)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=0, pady=1)

        # create a Scrollbar and associate it with txt
        v_scroll_bar = Scrollbar(self, command=self.txt.yview)
        if scroll_bar:
            v_scroll_bar.grid(row=0, column=1, sticky='nsew')
        self.txt['yscrollcommand'] = v_scroll_bar.set

    def state(self, state=None):
        if state:
            self.txt.configure(state=state)
        else:
            return self.txt['state']

    def focus_last_line(self):
        self.txt.yview_pickplace('end')

    def insert(self, txt):
        state = self.state()
        self.state('normal')
        self.txt.insert('end', txt+'\n')
        self.state(state)
