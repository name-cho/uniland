"""Minimal GUI toolkit for UniLand, built on Python's standard tkinter.

Nothing here imports tkinter until a GUI function is actually called, so
scripts that don't use a GUI (and headless environments) are unaffected.
"""
from .errors import UniLandError
from .builtins import call_fn, uland_str


def _tk():
    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog
        return tk, messagebox, simpledialog
    except Exception as e:
        raise UniLandError(f"GUI is not available (tkinter missing?): {e}")


def gui_window(args):
    tk, _, _ = _tk()
    title = uland_str(args[0]) if len(args) > 0 else "UniLand"
    width = int(args[1]) if len(args) > 1 else 400
    height = int(args[2]) if len(args) > 2 else 300
    root = tk.Tk()
    root.title(title)
    root.geometry(f"{width}x{height}")
    return root


def _parent(args, name):
    if not args:
        raise UniLandError(f"{name}() needs a parent window")
    return args[0]


def gui_label(args):
    tk, _, _ = _tk()
    parent = _parent(args, "gui_label")
    text = uland_str(args[1]) if len(args) > 1 else ""
    w = tk.Label(parent, text=text)
    w.pack(padx=8, pady=4)
    return w


def gui_button(args):
    tk, _, _ = _tk()
    parent = _parent(args, "gui_button")
    text = uland_str(args[1]) if len(args) > 1 else "Button"
    callback = args[2] if len(args) > 2 else None
    cmd = (lambda: call_fn(callback, [])) if callback is not None else None
    w = tk.Button(parent, text=text, command=cmd)
    w.pack(padx=8, pady=4)
    return w


def gui_input(args):
    tk, _, _ = _tk()
    parent = _parent(args, "gui_input")
    w = tk.Entry(parent, width=30)
    if len(args) > 1 and args[1]:
        w.insert(0, uland_str(args[1]))
    w.pack(padx=8, pady=4)
    return w


def gui_get(args):
    if not args:
        raise UniLandError("gui_get() needs a widget")
    w = args[0]
    if hasattr(w, "get"):
        return w.get()
    try:
        return w.cget("text")
    except Exception:
        return ""


def gui_set(args):
    if len(args) < 2:
        raise UniLandError("gui_set() needs a widget and a value")
    w, value = args[0], uland_str(args[1])
    import tkinter as tk
    if isinstance(w, tk.Entry):
        w.delete(0, "end")
        w.insert(0, value)
    else:
        try:
            w.config(text=value)
        except Exception:
            raise UniLandError("gui_set(): widget does not support text")
    return None


def gui_run(args):
    if not args:
        raise UniLandError("gui_run() needs a window")
    args[0].mainloop()
    return None


def gui_close(args):
    if not args:
        raise UniLandError("gui_close() needs a window")
    args[0].destroy()
    return None


def alert(args):
    _, messagebox, _ = _tk()
    _ensure_root()
    messagebox.showinfo("UniLand", uland_str(args[0]) if args else "")
    return None


def confirm(args):
    _, messagebox, _ = _tk()
    _ensure_root()
    return bool(messagebox.askyesno("UniLand", uland_str(args[0]) if args else ""))


def prompt(args):
    _, _, simpledialog = _tk()
    _ensure_root()
    message = uland_str(args[0]) if args else ""
    default = uland_str(args[1]) if len(args) > 1 else ""
    result = simpledialog.askstring("UniLand", message, initialvalue=default)
    return result if result is not None else None


_HIDDEN_ROOT = None

def _ensure_root():
    """Dialogs need a Tk root; create a hidden one if the user has none."""
    global _HIDDEN_ROOT
    import tkinter as tk
    if tk._default_root is None and _HIDDEN_ROOT is None:
        _HIDDEN_ROOT = tk.Tk()
        _HIDDEN_ROOT.withdraw()


GUI_FUNCTIONS = {
    'gui_window': gui_window,
    'gui_label': gui_label,
    'gui_button': gui_button,
    'gui_input': gui_input,
    'gui_get': gui_get,
    'gui_set': gui_set,
    'gui_run': gui_run,
    'gui_close': gui_close,
    # friendly aliases / dialogs
    'alert': alert, 'show_alert': alert,
    'confirm': confirm, 'show_confirm': confirm,
    'prompt': prompt, 'show_prompt': prompt,
    'get_value': gui_get, 'set_text': gui_set,
}
