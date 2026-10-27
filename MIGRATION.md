# Переход на UniLand на Go

Python-версия остановлена на 2.2.0: новых возможностей и исправлений здесь
не будет. Актуальный интерпретатор — [UniLand на Go](https://github.com/name-cho/uniland-go)
(зеркало: [gitgud](https://gitgud.io/name-cho/uniland-go)).

Этот репозиторий остаётся публичным как история и как эталон совместимости:
на нём построены golden-снимки в `uniland-go/compat`.

## Почему Go-версия

- Один бинарник: Python нужен только там, где скрипт сам использует
  `python { }`.
- Язык, синтаксис, CLI и тексты ошибок те же — совместимость проверяется
  автоматически: 16 golden-кейсов, 15 дампов токенов и сверка вывода
  с эталоном.
- Перенесены все встроенные функции эталона и все `gui_*`.
- Скрипты исполняет байткод-машина, это заметно быстрее.
- Дополнительно: блоки `go { }`, `goeval`, `goexec`, форматтер
  `uniland fmt`, Language Server `uniland lsp`.

## Что переносится без изменений

- файлы `.uni` и синтаксис языка;
- команды `run`, `-e`, `-i`, `-c`, `run -d`, коды возврата и сообщения
  об ошибках;
- `python { }`, `pyeval`, `pyexec`, `py` и объект `uni`;
- `gui_window`, `gui_label`, `gui_button`, `gui_input`, `gui_get`,
  `gui_set`, `gui_run`, `gui_close`, `gui_on_close`, `gui_image`,
  `gui_image_button`, `gui_gif`, `gui_video`, `pick_file`, `pick_save`,
  `pick_folder`, `alert`, `confirm`, `prompt` и алиасы.

## Что проверить при переезде

Полный список отличий — в
[docs/COMPAT.md](https://github.com/name-cho/uniland-go/blob/main/docs/COMPAT.md).
Самое заметное:

1. Окна рисует Fyne, а не tkinter: набор функций тот же, внешний вид другой.
2. `gui_video` открывает файл внешним плеером, GIF анимируется вручную,
   диалоги и выбор файлов идут через системные окна zenity.
3. Цикл событий Fyne запускается один раз: после закрытия окна второе окно
   в том же запуске не открыть, повторный `gui_run` вернёт ловящуюся ошибку.
   В tkinter-версии следующее окно открывалось.
4. Ctrl+C в REPL завершает процесс, а не просто очищает строку ввода.
5. Ошибки Python внутри `python { }` приходят как `UniLandError` с тем же
   текстом, но без traceback.
6. `list_dir` сортирует имена, `system()` не перекодирует вывод,
   `http_*` работает на `net/http` без пакета `requests`.
7. На Windows Python-блоки запускаются в UTF-8, поэтому `open()` без
   `encoding=` читает UTF-8, а не cp1251.
8. Пути внутри zip-архивов всегда разделяются через `/`.

## Установка

Нужен Go 1.23 или новее. Готовых сборок пока нет — бинарник собирается из
исходников. Подробная пошаговая инструкция для Windows, Linux и Termux:
[docs/install.md](https://github.com/name-cho/uniland-go/blob/main/docs/install.md).

Кратко, Windows (CLI):

```powershell
git clone https://github.com/name-cho/uniland-go.git
cd uniland-go
go build -trimpath -ldflags "-s -w" -o uniland.exe .
.\uniland.exe run script.uni
```

Окна на Windows требуют mingw-w64; без компилятора собирайте с
`$env:CGO_ENABLED='0'`, тогда `gui_*` вернут ошибку, которую можно поймать.

Linux и macOS:

```bash
git clone https://github.com/name-cho/uniland-go.git
cd uniland-go
sudo apt install gcc libgl1-mesa-dev xorg-dev libwayland-dev libxkbcommon-dev
go build -trimpath -ldflags "-s -w" -o uniland .
```

Termux: `CGO_ENABLED=0 go build -o uniland .`

Есть и установка без клонирования:

```bash
go install github.com/name-cho/uniland-go@main
```

Команда ставит бинарник `uniland-go` в `$(go env GOPATH)/bin`. Без
компилятора C соберётся заглушка GUI; для окон нужен cgo и mingw-w64
(Windows) или gcc с заголовками GL/Wayland (Linux).

## Если что-то не работает

Откройте issue в [uniland-go](https://github.com/name-cho/uniland-go/issues)
и приложите скрипт, вывод этой версии и вывод Go-версии. Старую версию можно
держать рядом и запускать из её каталога через `python -m uniland`, чтобы
сравнить поведение.
