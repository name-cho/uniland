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


# Tkinter выбрасывает картинки сборщиком мусора, если на них нет ссылки.
# Держим их здесь на всё время жизни программы.
_REFS = []


def _load_photo(path, width=None, height=None):
    """Загрузить картинку в PhotoImage. С Pillow — любой формат и ресайз;
    без Pillow — нативно png/gif/ppm (для остального — понятная подсказка)."""
    tk, _, _ = _tk()
    width = int(width) if width else None
    height = int(height) if height else None
    try:
        from PIL import Image, ImageTk
        img = Image.open(path)
        if width and height:
            img = img.resize((width, height))
        photo = ImageTk.PhotoImage(img)
    except ImportError:
        try:
            photo = tk.PhotoImage(file=path)
        except Exception as e:
            raise UniLandError(
                f"Не удалось загрузить '{path}': {e}. "
                f"Для jpg/webp и ресайза установи Pillow (pip install Pillow).")
    except Exception as e:
        raise UniLandError(f"Не удалось загрузить изображение '{path}': {e}")
    _REFS.append(photo)
    return photo


def gui_image(args):
    """gui_image(win, path[, width, height]) — показать картинку."""
    tk, _, _ = _tk()
    parent = _parent(args, "gui_image")
    path = uland_str(args[1]) if len(args) > 1 else ""
    w = args[2] if len(args) > 2 else None
    h = args[3] if len(args) > 3 else None
    photo = _load_photo(path, w, h)
    lbl = tk.Label(parent, image=photo)
    lbl.image = photo
    lbl.pack(padx=8, pady=4)
    return lbl


def gui_image_button(args):
    """gui_image_button(win, path, onClick[, width, height]) — кнопка-картинка."""
    tk, _, _ = _tk()
    parent = _parent(args, "gui_image_button")
    path = uland_str(args[1]) if len(args) > 1 else ""
    callback = args[2] if len(args) > 2 else None
    w = args[3] if len(args) > 3 else None
    h = args[4] if len(args) > 4 else None
    photo = _load_photo(path, w, h)
    cmd = (lambda: call_fn(callback, [])) if callback is not None else None
    btn = tk.Button(parent, image=photo, command=cmd,
                    borderwidth=0, highlightthickness=0, cursor="hand2")
    btn.image = photo
    btn.pack(padx=8, pady=6)
    return btn


def gui_gif(args):
    """gui_gif(win, path[, width, height]) — анимированный GIF (нативно)."""
    tk, _, _ = _tk()
    parent = _parent(args, "gui_gif")
    path = uland_str(args[1]) if len(args) > 1 else ""
    w = int(args[2]) if len(args) > 2 else None
    h = int(args[3]) if len(args) > 3 else None
    frames = []
    delay = 100
    try:
        from PIL import Image, ImageTk
        im = Image.open(path)
        delay = im.info.get("duration", 100) or 100
        i = 0
        while True:
            try:
                im.seek(i)
            except EOFError:
                break
            fr = im.convert("RGBA")
            if w and h:
                fr = fr.resize((w, h))
            frames.append(ImageTk.PhotoImage(fr))
            i += 1
    except ImportError:
        i = 0
        while True:
            try:
                frames.append(tk.PhotoImage(file=path, format=f"gif -index {i}"))
            except Exception:
                break
            i += 1
    except Exception as e:
        raise UniLandError(f"Не удалось загрузить GIF '{path}': {e}")
    if not frames:
        raise UniLandError(f"В файле нет кадров GIF: {path}")
    _REFS.extend(frames)
    lbl = tk.Label(parent, image=frames[0])
    lbl.image = frames[0]
    lbl.pack(padx=8, pady=4)
    state = {"i": 0}

    def tick():
        state["i"] = (state["i"] + 1) % len(frames)
        lbl.config(image=frames[state["i"]])
        lbl.after(delay, tick)

    if len(frames) > 1:
        lbl.after(delay, tick)
    return lbl


def gui_video(args):
    """gui_video(win, path) — видео в окне (без звука).
    Нужен опциональный пакет imageio (pip install 'uniland[video]').
    Если его нет — видео откроется во внешнем системном плеере."""
    tk, _, _ = _tk()
    parent = _parent(args, "gui_video")
    path = uland_str(args[1]) if len(args) > 1 else ""
    try:
        import imageio
        from PIL import Image, ImageTk
    except ImportError:
        from .builtins import b_open_file
        print(f"[INFO] imageio не установлен — открываю видео во внешнем плеере: {path}")
        b_open_file([path])
        return None
    try:
        reader = imageio.get_reader(path)
        meta = reader.get_meta_data()
        fps = meta.get("fps", 25) or 25
        delay = max(1, int(1000 / fps))
        lbl = tk.Label(parent)
        lbl.pack(padx=8, pady=4)
        frames = iter(reader)

        def show():
            try:
                frame = next(frames)
            except StopIteration:
                return
            photo = ImageTk.PhotoImage(Image.fromarray(frame))
            lbl.config(image=photo)
            lbl.image = photo  # держим ссылку на текущий кадр
            lbl.after(delay, show)

        show()
        return lbl
    except Exception as e:
        raise UniLandError(f"Не удалось воспроизвести видео '{path}': {e}")


def _filedialog():
    _tk()
    from tkinter import filedialog
    _ensure_root()
    return filedialog


def pick_file(args):
    """pick_file([title]) — диалог выбора файла. Возвращает путь или null."""
    fd = _filedialog()
    title = uland_str(args[0]) if args else "Выбери файл"
    r = fd.askopenfilename(title=title)
    return r if r else None


def pick_save(args):
    """pick_save([title]) — диалог 'сохранить как'. Возвращает путь или null."""
    fd = _filedialog()
    title = uland_str(args[0]) if args else "Сохранить как"
    r = fd.asksaveasfilename(title=title)
    return r if r else None


def pick_folder(args):
    """pick_folder([title]) — диалог выбора папки. Возвращает путь или null."""
    fd = _filedialog()
    title = uland_str(args[0]) if args else "Выбери папку"
    r = fd.askdirectory(title=title)
    return r if r else None


def gui_on_close(args):
    """gui_on_close(win, fn) — вызвать fn при закрытии окна (напр. автосохранение)."""
    if len(args) < 2:
        raise UniLandError("gui_on_close() needs a window and a function")
    win, fn = args[0], args[1]

    def handler():
        try:
            call_fn(fn, [])
        finally:
            win.destroy()

    win.protocol("WM_DELETE_WINDOW", handler)
    return None


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
    'gui_on_close': gui_on_close,
    # media widgets
    'gui_image': gui_image,
    'gui_image_button': gui_image_button,
    'gui_gif': gui_gif,
    'gui_video': gui_video,
    # file pickers
    'pick_file': pick_file,
    'pick_save': pick_save,
    'pick_folder': pick_folder,
    # friendly aliases / dialogs
    'alert': alert, 'show_alert': alert,
    'confirm': confirm, 'show_confirm': confirm,
    'prompt': prompt, 'show_prompt': prompt,
    'get_value': gui_get, 'set_text': gui_set,
}
