import time
import os
import json
import re
import math
import random
import shutil
import subprocess
from datetime import datetime
from .errors import UniLandError


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
        self.consts = set()

    def define(self, name, value, is_const=False):
        self.vars[name] = value
        if is_const:
            self.consts.add(name)

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise UniLandError(f"Undefined variable: {name}")

    def set(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                if name in env.consts:
                    raise UniLandError(f"Cannot reassign constant: {name}")
                env.vars[name] = value
                return
            env = env.parent
        raise UniLandError(f"Undefined variable: {name}")


# ---------------------------------------------------------------------------
# Calling back into the interpreter (for map/filter/sort callbacks, etc.)
# ---------------------------------------------------------------------------
_CALLER = None

def set_caller(fn):
    global _CALLER
    _CALLER = fn

def call_fn(fn, args):
    if _CALLER is None:
        raise UniLandError("Interpreter is not ready to call functions")
    return _CALLER(fn, list(args))


# ---------------------------------------------------------------------------
# Value formatting (shared by print, templates, to_string)
# ---------------------------------------------------------------------------
def _num(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if v.is_integer():
        return str(int(v))
    return repr(v)

def _inner(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, str):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, list):
        return "[" + ", ".join(_inner(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f'"{k}": ' + _inner(val) for k, val in v.items()) + "}"
    if callable(v) or v.__class__.__name__ == 'UniFunction':
        return "<function>"
    return str(v)

def uland_str(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return _num(v)
    if isinstance(v, str):
        return v
    if isinstance(v, (list, dict)):
        return _inner(v)
    if callable(v) or v.__class__.__name__ == 'UniFunction':
        return "<function>"
    return str(v)

def uland_typeof(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    if callable(v) or v.__class__.__name__ == 'UniFunction':
        return "function"
    return "unknown"

def is_truthy(v):
    if v is None or v is False:
        return False
    if v is True:
        return True
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (str, list, dict)):
        return len(v) > 0
    return True


def _need(args, n, name):
    if len(args) != n:
        raise UniLandError(f"{name}() expects {n} argument(s), got {len(args)}")


# ---------------------------------------------------------------------------
# Output / logging
# ---------------------------------------------------------------------------
def b_print(args):
    print(' '.join(uland_str(a) for a in args), flush=True)
    return None

def _logger(prefix):
    def log(args):
        print(prefix, ' '.join(uland_str(a) for a in args), flush=True)
        return None
    return log


# ---------------------------------------------------------------------------
# Types & conversions
# ---------------------------------------------------------------------------
def b_typeof(args):
    _need(args, 1, "typeof")
    return uland_typeof(args[0])

def b_to_string(args):
    _need(args, 1, "to_string")
    return uland_str(args[0])

def b_to_number(args):
    _need(args, 1, "to_number")
    v = args[0]
    if isinstance(v, bool):
        return 1 if v else 0
    try:
        s = str(v).strip()
        return int(s) if re.fullmatch(r'[+-]?\d+', s) else float(s)
    except Exception:
        raise UniLandError(f"Cannot convert {uland_str(v)} to number")

def b_to_boolean(args):
    _need(args, 1, "to_boolean")
    return is_truthy(args[0])

def _is(check):
    def f(args):
        _need(args, 1, check.__name__)
        return check(args[0])
    return f


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------
def b_length(args):
    _need(args, 1, "length")
    v = args[0]
    if isinstance(v, (str, list, dict)):
        return len(v)
    raise UniLandError("length() needs a string, array or object")

def b_split(args):
    if len(args) not in (1, 2):
        raise UniLandError("split() expects (string) or (string, separator)")
    s = args[0]
    if not isinstance(s, str):
        raise UniLandError("split() first argument must be a string")
    if len(args) == 1:
        return s.split()
    sep = args[1]
    if sep == "":
        return list(s)
    return s.split(sep)

def b_join(args):
    _need(args, 2, "join")
    arr, sep = args
    if not isinstance(arr, list):
        raise UniLandError("join() first argument must be an array")
    return sep.join(uland_str(x) for x in arr)

def b_replace(args):
    _need(args, 3, "replace")
    s, old, new = args
    return s.replace(old, new)

def b_substring(args):
    if len(args) not in (2, 3):
        raise UniLandError("substring() expects (string, start[, end])")
    s = args[0]
    start = int(args[1])
    end = int(args[2]) if len(args) == 3 else len(s)
    return s[start:end]

def b_trim(args):
    _need(args, 1, "trim")
    return args[0].strip()

def b_upper(args):
    _need(args, 1, "uppercase")
    return args[0].upper()

def b_lower(args):
    _need(args, 1, "lowercase")
    return args[0].lower()

def b_startswith(args):
    _need(args, 2, "startswith")
    return args[0].startswith(args[1])

def b_endswith(args):
    _need(args, 2, "endswith")
    return args[0].endswith(args[1])

def b_repeat(args):
    _need(args, 2, "repeat")
    return args[0] * int(args[1])

def b_char_code(args):
    _need(args, 1, "char_code")
    return ord(args[0])

def b_from_char_code(args):
    _need(args, 1, "from_char_code")
    return chr(int(args[0]))


# ---------------------------------------------------------------------------
# Arrays
# ---------------------------------------------------------------------------
def _arr(args, name, idx=0):
    if not isinstance(args[idx], list):
        raise UniLandError(f"{name}() argument must be an array")
    return args[idx]

def b_push(args):
    _need(args, 2, "push")
    arr = _arr(args, "push")
    arr.append(args[1])
    return len(arr)

def b_pop(args):
    _need(args, 1, "pop")
    arr = _arr(args, "pop")
    if not arr:
        raise UniLandError("pop() from empty array")
    return arr.pop()

def b_shift(args):
    _need(args, 1, "shift")
    arr = _arr(args, "shift")
    if not arr:
        raise UniLandError("shift() from empty array")
    return arr.pop(0)

def b_unshift(args):
    _need(args, 2, "unshift")
    arr = _arr(args, "unshift")
    arr.insert(0, args[1])
    return len(arr)

def b_slice(args):
    if len(args) not in (2, 3):
        raise UniLandError("slice() expects (array, start[, end])")
    arr = _arr(args, "slice")
    start = int(args[1])
    end = int(args[2]) if len(args) == 3 else None
    return arr[start:end]

def b_splice(args):
    if len(args) < 2:
        raise UniLandError("splice() expects (array, start[, count])")
    arr = _arr(args, "splice")
    start = int(args[1])
    count = int(args[2]) if len(args) >= 3 else len(arr) - start
    removed = arr[start:start + count]
    del arr[start:start + count]
    return removed

def b_reverse(args):
    _need(args, 1, "reverse")
    arr = _arr(args, "reverse")
    arr.reverse()
    return arr

def b_sort(args):
    if len(args) not in (1, 2):
        raise UniLandError("sort() expects (array[, keyfn])")
    arr = _arr(args, "sort")
    try:
        if len(args) == 2:
            arr.sort(key=lambda x: call_fn(args[1], [x]))
        else:
            arr.sort()
    except TypeError:
        raise UniLandError("sort() cannot compare these elements")
    return arr

def b_includes(args):
    _need(args, 2, "includes")
    coll = args[0]
    if isinstance(coll, (list, str)):
        return args[1] in coll
    raise UniLandError("includes() first argument must be an array or string")

def b_index_of(args):
    _need(args, 2, "indexOf")
    coll = args[0]
    if not isinstance(coll, (list, str)):
        raise UniLandError("indexOf() first argument must be an array or string")
    try:
        return coll.index(args[1])
    except ValueError:
        return -1

def b_map(args):
    _need(args, 2, "map")
    arr = _arr(args, "map")
    return [call_fn(args[1], [x]) for x in arr]

def b_filter(args):
    _need(args, 2, "filter")
    arr = _arr(args, "filter")
    return [x for x in arr if is_truthy(call_fn(args[1], [x]))]

def b_reduce(args):
    if len(args) not in (2, 3):
        raise UniLandError("reduce() expects (array, fn[, initial])")
    arr = _arr(args, "reduce")
    if len(args) == 3:
        acc = args[2]
        items = arr
    else:
        if not arr:
            raise UniLandError("reduce() of empty array with no initial value")
        acc = arr[0]
        items = arr[1:]
    for x in items:
        acc = call_fn(args[1], [acc, x])
    return acc

def b_find(args):
    _need(args, 2, "find")
    arr = _arr(args, "find")
    for x in arr:
        if is_truthy(call_fn(args[1], [x])):
            return x
    return None

def b_each(args):
    _need(args, 2, "each")
    arr = _arr(args, "each")
    for x in arr:
        call_fn(args[1], [x])
    return None

def b_sum(args):
    _need(args, 1, "sum")
    arr = _arr(args, "sum")
    return sum(arr)

def b_range(args):
    if len(args) == 1:
        return list(range(int(args[0])))
    if len(args) == 2:
        return list(range(int(args[0]), int(args[1])))
    if len(args) == 3:
        return list(range(int(args[0]), int(args[1]), int(args[2])))
    raise UniLandError("range() expects 1-3 arguments")


# ---------------------------------------------------------------------------
# Objects
# ---------------------------------------------------------------------------
def b_keys(args):
    _need(args, 1, "keys")
    if not isinstance(args[0], dict):
        raise UniLandError("keys() argument must be an object")
    return list(args[0].keys())

def b_values(args):
    _need(args, 1, "values")
    if not isinstance(args[0], dict):
        raise UniLandError("values() argument must be an object")
    return list(args[0].values())

def b_entries(args):
    _need(args, 1, "entries")
    if not isinstance(args[0], dict):
        raise UniLandError("entries() argument must be an object")
    return [[k, v] for k, v in args[0].items()]

def b_has(args):
    _need(args, 2, "has")
    obj = args[0]
    if not isinstance(obj, dict):
        raise UniLandError("has() first argument must be an object")
    return args[1] in obj

def b_merge(args):
    _need(args, 2, "merge")
    a, b = args
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise UniLandError("merge() needs two objects")
    out = dict(a)
    out.update(b)
    return out

def b_clone(args):
    _need(args, 1, "clone")
    v = args[0]
    if isinstance(v, dict):
        return dict(v)
    if isinstance(v, list):
        return list(v)
    return v


# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------
def _num1(name):
    def f(args):
        _need(args, 1, name)
        if not isinstance(args[0], (int, float)) or isinstance(args[0], bool):
            raise UniLandError(f"{name}() argument must be a number")
        return args[0]
    return f

def b_abs(args):
    return abs(_num1("abs")(args))

def b_round(args):
    if len(args) == 2:
        return round(args[0], int(args[1]))
    return round(_num1("round")(args))

def b_floor(args):
    return math.floor(_num1("floor")(args))

def b_ceil(args):
    return math.ceil(_num1("ceil")(args))

def b_sqrt(args):
    return math.sqrt(_num1("sqrt")(args))

def b_min(args):
    if len(args) == 1 and isinstance(args[0], list):
        return min(args[0])
    return min(args)

def b_max(args):
    if len(args) == 1 and isinstance(args[0], list):
        return max(args[0])
    return max(args)

def b_pow(args):
    _need(args, 2, "pow")
    return args[0] ** args[1]

def b_random(args):
    if len(args) == 0:
        return random.random()
    if len(args) == 2:
        return random.randint(int(args[0]), int(args[1]))
    raise UniLandError("random() expects 0 or 2 arguments")

def b_random_int(args):
    _need(args, 2, "random_int")
    return random.randint(int(args[0]), int(args[1]))


# ---------------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------------
def b_regex_match(args):
    _need(args, 2, "regex_match")
    return re.search(args[0], args[1]) is not None

def b_regex_findall(args):
    _need(args, 2, "regex_findall")
    return list(re.findall(args[0], args[1]))

def b_regex_replace(args):
    _need(args, 3, "regex_replace")
    return re.sub(args[0], args[2], args[1])


# ---------------------------------------------------------------------------
# Files & filesystem
# ---------------------------------------------------------------------------
def b_read_file(args):
    _need(args, 1, "read_file")
    try:
        with open(args[0], 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise UniLandError(f"Failed to read file: {e}")

def b_write_file(args):
    _need(args, 2, "write_file")
    try:
        with open(args[0], 'w', encoding='utf-8') as f:
            f.write(uland_str(args[1]))
        return None
    except Exception as e:
        raise UniLandError(f"Failed to write file: {e}")

def b_append_file(args):
    _need(args, 2, "append_file")
    try:
        with open(args[0], 'a', encoding='utf-8') as f:
            f.write(uland_str(args[1]))
        return None
    except Exception as e:
        raise UniLandError(f"Failed to append to file: {e}")

def b_file_exists(args):
    _need(args, 1, "file_exists")
    return os.path.exists(args[0])

def b_delete_file(args):
    _need(args, 1, "delete_file")
    try:
        os.remove(args[0])
        return None
    except Exception as e:
        raise UniLandError(f"Failed to delete file: {e}")

def b_list_dir(args):
    _need(args, 1, "list_dir")
    try:
        return os.listdir(args[0])
    except Exception as e:
        raise UniLandError(f"Failed to list directory: {e}")

def b_create_dir(args):
    _need(args, 1, "create_dir")
    try:
        os.makedirs(args[0], exist_ok=True)
        return None
    except Exception as e:
        raise UniLandError(f"Failed to create directory: {e}")

def b_copy_file(args):
    _need(args, 2, "copy_file")
    try:
        shutil.copy(args[0], args[1])
        return None
    except Exception as e:
        raise UniLandError(f"Failed to copy file: {e}")

def b_rename_file(args):
    _need(args, 2, "rename_file")
    try:
        os.rename(args[0], args[1])
        return None
    except Exception as e:
        raise UniLandError(f"Failed to rename file: {e}")

def b_file_info(args):
    _need(args, 1, "file_info")
    path = args[0]
    if not os.path.exists(path):
        raise UniLandError(f"file_info(): path does not exist: {path}")
    st = os.stat(path)
    return {
        "size": st.st_size,
        "is_dir": os.path.isdir(path),
        "is_file": os.path.isfile(path),
        "modified": st.st_mtime,
    }


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------
def b_get_time(args):
    return time.time()

def b_get_date(args):
    return datetime.now().isoformat()

def b_sleep(args):
    _need(args, 1, "sleep")
    time.sleep(args[0] / 1000.0)
    return None

def b_format_time(args):
    if len(args) not in (1, 2):
        raise UniLandError("format_time() expects (timestamp[, format])")
    ts = args[0]
    fmt = args[1] if len(args) == 2 else "%Y-%m-%d %H:%M:%S"
    return datetime.fromtimestamp(ts).strftime(fmt)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def b_parse_json(args):
    _need(args, 1, "parse_json")
    try:
        return json.loads(args[0])
    except Exception as e:
        raise UniLandError(f"JSON parse error: {e}")

def b_stringify_json(args):
    if len(args) not in (1, 2):
        raise UniLandError("stringify_json() expects (value[, indent])")
    try:
        indent = int(args[1]) if len(args) == 2 else None
        return json.dumps(args[0], ensure_ascii=False, indent=indent)
    except Exception as e:
        raise UniLandError(f"JSON stringify error: {e}")


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _http(method):
    def f(args):
        if len(args) < 1 or not isinstance(args[0], str):
            raise UniLandError(f"http_{method}() needs a url string")
        try:
            import requests
        except ImportError:
            raise UniLandError("http_* functions need the 'requests' package (pip install requests)")
        url = args[0]
        data = args[1] if len(args) > 1 else None
        try:
            if method in ('post', 'put'):
                resp = requests.request(method, url, json=data)
            else:
                resp = requests.request(method, url)
            return {"status": resp.status_code, "body": resp.text, "headers": dict(resp.headers)}
        except Exception as e:
            raise UniLandError(f"HTTP {method.upper()} failed: {e}")
    return f


# ---------------------------------------------------------------------------
# System / process / environment
# ---------------------------------------------------------------------------
def b_system(args):
    _need(args, 1, "system")
    try:
        result = subprocess.run(args[0], shell=True, capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except Exception as e:
        raise UniLandError(f"Failed to execute command: {e}")

def b_env(args):
    if len(args) == 0:
        return dict(os.environ)
    name = args[0]
    default = args[1] if len(args) > 1 else None
    return os.environ.get(name, default)

def b_input(args):
    prompt = uland_str(args[0]) if args else ""
    try:
        return input(prompt)
    except EOFError:
        return ""

def b_exit(args):
    code = int(args[0]) if args else 0
    raise SystemExit(code)

_SCRIPT_ARGS = []

def set_argv(values):
    global _SCRIPT_ARGS
    _SCRIPT_ARGS = list(values)

def b_args(args):
    return list(_SCRIPT_ARGS)  # arguments passed after `uniland run script.uni`


BUILTIN_FUNCTIONS = {
    # output
    'print': b_print, 'output': b_print, 'input': b_input,
    'log_info': _logger("[INFO]"), 'log_debug': _logger("[DEBUG]"),
    'log_warn': _logger("[WARN]"), 'log_error': _logger("[ERROR]"),
    'log_fatal': _logger("[FATAL]"),
    # types
    'typeof': b_typeof, 'to_string': b_to_string, 'to_number': b_to_number,
    'to_boolean': b_to_boolean,
    'is_number': _is(lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)),
    'is_string': _is(lambda v: isinstance(v, str)),
    'is_array': _is(lambda v: isinstance(v, list)),
    'is_object': _is(lambda v: isinstance(v, dict)),
    'is_boolean': _is(lambda v: isinstance(v, bool)),
    'is_null': _is(lambda v: v is None),
    'is_function': _is(lambda v: callable(v) or v.__class__.__name__ == 'UniFunction'),
    # strings
    'length': b_length, 'split': b_split, 'join': b_join, 'replace': b_replace,
    'substring': b_substring, 'trim': b_trim, 'uppercase': b_upper,
    'lowercase': b_lower, 'startswith': b_startswith, 'endswith': b_endswith,
    'repeat': b_repeat, 'char_code': b_char_code, 'from_char_code': b_from_char_code,
    # arrays
    'push': b_push, 'pop': b_pop, 'shift': b_shift, 'unshift': b_unshift,
    'slice': b_slice, 'splice': b_splice, 'reverse': b_reverse, 'sort': b_sort,
    'includes': b_includes, 'indexOf': b_index_of, 'map': b_map, 'filter': b_filter,
    'reduce': b_reduce, 'find': b_find, 'each': b_each, 'sum': b_sum, 'range': b_range,
    # objects
    'keys': b_keys, 'values': b_values, 'entries': b_entries, 'has': b_has,
    'merge': b_merge, 'clone': b_clone,
    # math
    'abs': b_abs, 'round': b_round, 'floor': b_floor, 'ceil': b_ceil,
    'sqrt': b_sqrt, 'min': b_min, 'max': b_max, 'pow': b_pow,
    'random': b_random, 'random_int': b_random_int,
    # regex
    'regex_match': b_regex_match, 'regex_findall': b_regex_findall,
    'regex_replace': b_regex_replace,
    # files
    'read_file': b_read_file, 'write_file': b_write_file, 'append_file': b_append_file,
    'file_exists': b_file_exists, 'delete_file': b_delete_file, 'list_dir': b_list_dir,
    'create_dir': b_create_dir, 'copy_file': b_copy_file, 'rename_file': b_rename_file,
    'file_info': b_file_info,
    # time
    'get_time': b_get_time, 'get_date': b_get_date, 'sleep': b_sleep,
    'format_time': b_format_time,
    # json
    'parse_json': b_parse_json, 'stringify_json': b_stringify_json,
    # http
    'http_get': _http('get'), 'http_post': _http('post'),
    'http_put': _http('put'), 'http_delete': _http('delete'),
    # system
    'system': b_system, 'env': b_env, 'exit': b_exit, 'argv': b_args,
}
