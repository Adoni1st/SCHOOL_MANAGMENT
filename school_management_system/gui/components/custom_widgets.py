import customtkinter as ctk
import tkinter as tk
import threading
import time

PASTEL_BG = '#f7fafd'
PASTEL_CARD = '#ffffff'
PASTEL_ACCENT = '#b3e5fc'
PASTEL_HOVER = '#e3f2fd'
PASTEL_SELECTED = '#bbdefb'
PASTEL_SHADOW = '#e0e3e7'
FONT = ("Segoe UI", 15)
HEADER_FONT = ("Segoe UI", 16, "bold")

class CardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=PASTEL_CARD, corner_radius=14, **kwargs)
        self.configure(border_width=1, border_color=PASTEL_SHADOW)

class SearchBar(ctk.CTkFrame):
    def __init__(self, master, placeholder="Search...", on_search=None, **kwargs):
        super().__init__(master, fg_color=PASTEL_BG, **kwargs)
        self.var = tk.StringVar()
        self.entry = ctk.CTkEntry(
            self, textvariable=self.var, placeholder_text=placeholder, width=220, font=FONT,
            border_color="#b3e5fc", border_width=2, fg_color="#fff", text_color="#1976d2",
            corner_radius=18
        )
        self.entry.pack(side="left", padx=(0, 8), pady=8, ipady=4)
        self.entry.bind('<KeyRelease>', lambda event: self._search())
        self.clear_btn = ctk.CTkButton(
            self, text="✕", width=36, height=36, fg_color="#e3f2fd", text_color="#1976d2",
            hover_color="#b3e5fc", corner_radius=18, command=self.clear, font=("Segoe UI", 16, "bold")
        )
        self.clear_btn.pack(side="left", padx=(0, 8), pady=4)
        self.on_search = on_search
        self.var.trace_add("write", lambda *_: self._search())
    def clear(self):
        self.var.set("")
        self._search()
    def _search(self):
        if self.on_search:
            self.on_search(self.var.get())

class TableRow(ctk.CTkFrame):
    def __init__(self, master, columns, selected=False, on_click=None, row_index=0, **kwargs):
        pastel_even = '#ffffff'
        pastel_odd = '#f0f4fa'
        bg = PASTEL_SELECTED if selected else (pastel_even if row_index % 2 == 0 else pastel_odd)
        super().__init__(master, fg_color=bg, corner_radius=12, **kwargs)
        self.on_click = on_click
        self.selected = selected
        for i, col in enumerate(columns):
            lbl = ctk.CTkLabel(self, text=col, font=("Segoe UI", 20), anchor="w", padx=16, pady=10)
            lbl.grid(row=0, column=i, sticky="ew", padx=8, pady=6)
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_hover)
            child.bind("<Leave>", self._on_leave)
            child.bind("<Button-1>", self._on_click)
    def _on_hover(self, e=None):
        if not self.selected:
            self.configure(fg_color=PASTEL_HOVER)
    def _on_leave(self, e=None):
        if not self.selected:
            pastel_even = '#ffffff'
            pastel_odd = '#f0f4fa'
            bg = pastel_even if getattr(self, 'row_index', 0) % 2 == 0 else pastel_odd
            self.configure(fg_color=bg)
    def _on_click(self, e=None):
        if self.on_click:
            self.on_click()

class ToastPopup(ctk.CTkToplevel):
    def __init__(self, master, message, duration=2):
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(fg_color=PASTEL_ACCENT)
        ctk.CTkLabel(self, text=message, font=FONT, text_color="#1976d2").pack(padx=20, pady=12)
        try:
            self.after(int(duration*1000), self.safe_destroy)
        except Exception:
            pass
        self.update_idletasks()
        x = master.winfo_rootx() + master.winfo_width()//2 - self.winfo_width()//2
        y = master.winfo_rooty() + 60
        self.geometry(f"+{x}+{y}")
    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass

class LoadingSpinner(ctk.CTkFrame):
    def __init__(self, master, text="Loading...", **kwargs):
        super().__init__(master, fg_color=PASTEL_BG, **kwargs)
        self.label = ctk.CTkLabel(self, text=text, font=FONT)
        self.label.pack(padx=20, pady=20)
        # Optionally add a spinner animation here
    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass
