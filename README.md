  # UniLand

  UniLand — маленький дружелюбный язык для скриптов: автоматизация, утилиты, работа с файлами, JSON и HTTP, простые
  оконные и консольные программы. Синтаксис похож на JavaScript, но проще: точки с запятой необязательны, есть шаблонные
  строки и лямбды, а ещё прямо внутри кода можно вставлять Python.

  Интерпретатор написан на Python и запускает файлы `.uni` из терминала.

  ```uniland
  let name = "мир"
  print(`Привет, {name}!`)
  ```

  ---

  ## Содержание

  - [Установка](#установка)
  - [Первая программа](#первая-программа)
  - [Курс: основы языка](#курс-основы-языка)
    - [Переменные](#переменные)
    - [Типы данных](#типы-данных)
    - [Строки и шаблоны](#строки-и-шаблоны)
    - [Операторы](#операторы)
    - [Условия](#условия)
    - [Циклы](#циклы)
    - [Функции и лямбды](#функции-и-лямбды)
    - [Массивы](#массивы)
    - [Объекты](#объекты)
    - [Обработка ошибок](#обработка-ошибок)
    - [Ввод и долгоживущие скрипты](#ввод-и-долгоживущие-скрипты)
  - [GUI: оконные программы](#gui-оконные-программы)
  - [Python внутри UniLand](#python-внутри-uniland)
  - [Справочник встроенных функций](#справочник-встроенных-функций)
  - [Примеры](#примеры)
  - [Лицензия](#лицензия)

  ---

  ## Установка

  Нужен Python 3.10 или новее.

  ```bash
  git clone https://codeberg.org/moyunni/uniland
  cd uniland
  pip install -e .
  ```

  После этого команда `uniland` доступна в терминале:

  ```bash
  uniland run script.uni
  uniland --version
  ```

  Базовый язык работает без сторонних зависимостей. `requests` нужен только для функций `http_*`:

  ```bash
  pip install -e ".[http]"
  ```

  GUI работает на стандартном `tkinter`, который уже идёт вместе с Python.

  ---

  ## Первая программа

  Создай файл `hello.uni`:

  ```uniland
  print("Привет, UniLand!")
  ```

  Запусти:

  ```bash
  uniland run hello.uni
  ```

  Готово. Теперь по порядку обо всём.

  ---

  ## Курс: основы языка

  ### Переменные

  `let` — обычная переменная, `const` — та, которую нельзя менять.

  ```uniland
  let x = 10
  x = x + 5        // ок

  const PI = 3.14
  // PI = 3        // ошибка: нельзя менять константу
  ```

  Точка с запятой в конце строки **необязательна** — перенос строки сам завершает инструкцию. Хочешь несколько команд в
  одной строке — раздели их `;`:

  ```uniland
  let a = 1; let b = 2; print(a + b)
  ```

  Комментарии:

  ```uniland
  // однострочный
  # тоже однострочный
  /* многострочный */
  ```

  ### Типы данных

  | Тип        | Пример                      |
  |------------|-----------------------------|
  | число      | `42`, `3.14`, `-7`          |
  | строка     | `"привет"`, `` `шаблон` ``  |
  | логический | `true`, `false`            |
  | пусто      | `null`                     |
  | массив     | `[1, 2, 3]`                |
  | объект     | `{name: "Аня", age: 20}`   |
  | функция    | `x => x + 1`               |

  Узнать тип значения:

  ```uniland
  print(typeof(42))        // "number"
  print(typeof("hi"))      // "string"
  print(typeof([1, 2]))    // "array"
  ```

  ### Строки и шаблоны

  Обычные строки — в двойных кавычках. Сложение строк работает через `+`:

  ```uniland
  let name = "Аня"
  print("Привет, " + name)
  ```

  **Шаблонные строки** — в обратных кавычках `` ` ``. Внутри `{ }` можно вставлять любые выражения, а сама строка может
  быть многострочной:

  ```uniland
  let a = 2
  let b = 3
  print(`{a} + {b} = {a + b}`)     // 2 + 3 = 5

  print(`Несколько
  строк подряд`)
  ```

  Чтобы написать настоящую фигурную скобку — удвой её: `{{` и `}}`.

  Полезные функции для строк:

  ```uniland
  uppercase("hi")            // "HI"
  lowercase("HI")            // "hi"
  trim("  hi  ")             // "hi"
  split("a,b,c", ",")        // ["a", "b", "c"]
  join(["a", "b"], "-")      // "a-b"
  replace("abc", "b", "X")   // "aXc"
  substring("hello", 1, 4)   // "ell"
  length("hello")            // 5
  includes("hello", "ell")   // true
  "hello"[0]                 // "h"
  ```

  ### Операторы

  ```
  Арифметика:   +  -  *  /  %  ^        (^ — возведение в степень)
  Сравнение:    ==  !=  <  >  <=  >=
  Логика:       &&  ||  !
  Присваивание: =  +=  -=  *=  /=  %=  ++  --
  ```

  ```uniland
  let n = 5
  n += 3          // 8
  n++             // 9
  print(2 ^ 10)   // 1024
  print(7 % 3)    // 1
  ```

  ### Условия

  ```uniland
  let age = 18

  if (age >= 18) {
      print("совершеннолетний")
  } else if (age >= 14) {
      print("подросток")
  } else {
      print("ребёнок")
  }
  ```

  «Истинно» — это любое ненулевое число, непустая строка/массив/объект и `true`. «Ложно» — `false`, `0`, `""`, пустые
  `[]` / `{}`, `null`.

  ### Циклы

  Классический `for`:

  ```uniland
  for (let i = 0; i < 3; i++) {
      print(i)        // 0, 1, 2
  }
  ```

  `for ... in` — перебор массива, строки или ключей объекта:

  ```uniland
  for (item in [10, 20, 30]) {
      print(item)
  }

  for (ch in "abc") {
      print(ch)
  }

  let user = {name: "Аня", age: 20}
  for (key in user) {
      print(key, "=", user[key])
  }
  ```

  `while`, а также `break` и `continue`:

  ```uniland
  let n = 0
  while (n < 100) {
      n++
      if (n == 5) { break }
      if (n % 2 == 0) { continue }
      print(n)
  }
  ```

  ### Функции и лямбды

  Объявление через `func`:

  ```uniland
  func add(a, b) {
      return a + b
  }
  print(add(2, 3))    // 5
  ```

  Функции — это значения: их можно класть в переменные, передавать в другие функции и возвращать. Короткая запись —
  **лямбда** через `=>`:

  ```uniland
  let square = x => x * x
  let sum = (a, b) => a + b

  print(square(5))    // 25
  print(sum(2, 3))    // 5
  ```

  Замыкания (функция помнит окружение, где её создали):

  ```uniland
  func adder(step) {
      return x => x + step
  }
  let add10 = adder(10)
  print(add10(5))     // 15
  ```

  Если в файле есть функция `main()` без аргументов, она запустится автоматически после загрузки файла.

  ### Массивы

  ```uniland
  let arr = [3, 1, 2]

  push(arr, 4)            // [3, 1, 2, 4]
  pop(arr)                // 4, массив снова [3, 1, 2]
  arr[0]                  // 3
  arr[0] = 99             // меняем элемент
  length(arr)             // 3
  sort(arr)               // [1, 2, 99]
  reverse(arr)            // [99, 2, 1]
  ```

  Функции высшего порядка — здесь лямбды особенно удобны:

  ```uniland
  let nums = [1, 2, 3, 4, 5]

  map(nums, x => x * 2)               // [2, 4, 6, 8, 10]
  filter(nums, x => x % 2 == 0)       // [2, 4]
  reduce(nums, (a, b) => a + b, 0)    // 15
  find(nums, x => x > 3)              // 4
  range(1, 6)                         // [1, 2, 3, 4, 5]
  ```

  ### Объекты

  Объект — это набор пар «ключ — значение».

  ```uniland
  let user = {name: "Аня", age: 20}

  user.name          // "Аня"    (через точку)
  user["age"]        // 20       (через ключ)

  user.age = 21      // изменить
  user.city = "Питер"// добавить новое поле

  keys(user)         // ["name", "age", "city"]
  values(user)       // ["Аня", 21, "Питер"]
  has(user, "name")  // true
  merge(user, {x: 1})// новый объект из двух
  ```

  ### Обработка ошибок

  ```uniland
  try {
      let data = read_file("нет-такого-файла.txt")
  } catch (e) {
      print("Что-то пошло не так:", e)
  } finally {
      print("Этот блок выполнится в любом случае")
  }
  ```

  Свою ошибку можно бросить через `throw`:

  ```uniland
  func divide(a, b) {
      if (b == 0) { throw "Деление на ноль!" }
      return a / b
  }
  ```

  ### Ввод и долгоживущие скрипты

  Спросить что-то у пользователя в консоли — `input`:

  ```uniland
  let name = input("Как тебя зовут? ")
  print(`Привет, {name}!`)

  let age = input("Сколько тебе лет? ")
  print(`Через год будет {to_number(age) + 1}.`)
  ```

  Скрипт может работать сколько угодно и не завершаться — например, как простая служба или бот. Для этого используй
  бесконечный цикл и паузу `sleep` (в миллисекундах). Остановить — `Ctrl+C`:

  ```uniland
  let tick = 0
  while (true) {
      tick += 1
      log_info(`тик #{tick}`)
      sleep(1000)     // ждём секунду
  }
  ```

  ---

  ## GUI: оконные программы

  Окна делаются на `tkinter` (входит в Python, ставить ничего не нужно). Кнопки принимают функцию-обработчик — отлично
  сочетается с лямбдами.

  ```uniland
  let win = gui_window("Моё окно", 320, 160)
  gui_label(win, "Как тебя зовут?")
  let field = gui_input(win, "")
  let out = gui_label(win, "")

  gui_button(win, "Поздороваться", () => {
      gui_set(out, `Привет, {gui_get(field)}!`)
  })

  gui_run(win)
  ```

  Функции GUI:

  | Функция | Что делает |
  |---------|------------|
  | `gui_window(title, width, height)` | создаёт окно |
  | `gui_label(win, text)` | надпись |
  | `gui_input(win, placeholder)` | поле ввода |
  | `gui_button(win, text, onClick)` | кнопка с обработчиком |
  | `gui_get(widget)` | получить текст из поля/надписи |
  | `gui_set(widget, text)` | задать текст |
  | `gui_run(win)` | показать окно (запустить цикл) |
  | `gui_close(win)` | закрыть окно |

  Диалоги (можно без своего окна):

  ```uniland
  alert("Привет!")
  let ok = confirm("Продолжить?")        // true / false
  let name = prompt("Как тебя зовут?")   // введённая строка или null
  ```

  ---

  ## Python внутри UniLand

  Иногда нужна сила Python — целая стандартная библиотека и любые пакеты. Просто положи Python-код в блок `python { ...
  }`. Обмен данными — через объект `uni`:

  ```uniland
  python {
      import math
      uni.phi = (1 + math.sqrt(5)) / 2     # отдаём значение в UniLand
  }
  print("Золотое сечение:", round(phi, 4))   // 1.618
  ```

  - `uni.имя = значение` — создать/изменить переменную UniLand из Python.
  - `uni.имя` — прочитать переменную UniLand в Python.
  - `uni.call("func", args...)` — вызвать функцию UniLand из Python.

  Быстрые однострочники без блока:

  ```uniland
  let x = pyeval("2 ** 100")                  // вычислить выражение Python и вернуть результат
  pyexec("import os; print(os.getcwd())")     // выполнить код
  ```

  > Python-блок выполняется с полными правами Python — как обычный скрипт.

  ---

  ## Справочник встроенных функций

  **Вывод и ввод**
  `print(...)`, `output(...)`, `input(prompt)`,
  `log_info(...)`, `log_debug(...)`, `log_warn(...)`, `log_error(...)`, `log_fatal(...)`

  **Типы и преобразования**
  `typeof(v)`, `to_string(v)`, `to_number(v)`, `to_boolean(v)`,
  `is_number(v)`, `is_string(v)`, `is_array(v)`, `is_object(v)`, `is_boolean(v)`, `is_null(v)`, `is_function(v)`

  **Строки**
  `length(s)`, `split(s, sep)`, `join(arr, sep)`, `replace(s, a, b)`, `substring(s, start, end)`,
  `trim(s)`, `uppercase(s)`, `lowercase(s)`, `startswith(s, p)`, `endswith(s, p)`,
  `repeat(s, n)`, `char_code(c)`, `from_char_code(n)`, `includes(s, part)`, `indexOf(s, part)`

  **Массивы**
  `length(a)`, `push(a, x)`, `pop(a)`, `shift(a)`, `unshift(a, x)`, `slice(a, start, end)`,
  `splice(a, start, count)`, `reverse(a)`, `sort(a)`, `includes(a, x)`, `indexOf(a, x)`,
  `map(a, fn)`, `filter(a, fn)`, `reduce(a, fn, init)`, `find(a, fn)`, `each(a, fn)`, `sum(a)`, `range(...)`

  **Объекты**
  `keys(o)`, `values(o)`, `entries(o)`, `has(o, key)`, `merge(o1, o2)`, `clone(v)`

  **Математика**
  `abs(x)`, `round(x[, digits])`, `floor(x)`, `ceil(x)`, `sqrt(x)`, `pow(b, e)`,
  `min(...)`, `max(...)`, `random()`, `random(min, max)`, `random_int(min, max)`

  **Регулярные выражения**
  `regex_match(pattern, s)`, `regex_findall(pattern, s)`, `regex_replace(pattern, s, repl)`

  **Файлы и папки**
  `read_file(path)`, `write_file(path, text)`, `append_file(path, text)`, `file_exists(path)`,
  `delete_file(path)`, `list_dir(path)`, `create_dir(path)`, `copy_file(src, dst)`,
  `rename_file(src, dst)`, `file_info(path)`

  **Время**
  `get_time()`, `get_date()`, `sleep(ms)`, `format_time(ts[, fmt])`

  **JSON**
  `parse_json(s)`, `stringify_json(v[, indent])`

  **HTTP** (нужен `requests`)
  `http_get(url)`, `http_post(url, data)`, `http_put(url, data)`, `http_delete(url)` — возвращают `{status, body,
  headers}`

  **Система**
  `system(cmd)` → `{stdout, stderr, returncode}`, `env(name[, default])`, `argv()`, `exit(code)`

  **Python**
  `pyeval(code)`, `pyexec(code)`, `py(code)`

  **GUI** — см. раздел [выше](#gui-оконные-программы).

  ---

  ## Примеры

  В папке `examples/`:

  - `hello.uni` — самое первое.
  - `selftest.uni` — набор проверок самого интерпретатора: `uniland run examples/selftest.uni`.
  - `greet_cli.uni` — спрашивает имя в консоли и отвечает.
  - `gui_demo.uni` — маленькое окно с приветствием.
  - `ticker.uni` — долгоживущий скрипт-«служба», тикает раз в секунду (стоп — `Ctrl+C`).
  - `wordcount.uni` — счётчик слов в файле: `uniland run examples/wordcount.uni README.md`.

  Аргументы командной строки доступны через `argv()`:

  ```uniland
  let args = argv()
  if (length(args) == 0) {
      print("Передай имя файла")
      exit(1)
  }
  print("Первый аргумент:", args[0])
  ```

  ```bash
  uniland run script.uni файл.txt
  ```

  ---

  ## Лицензия

  MIT — делай с кодом что хочешь.