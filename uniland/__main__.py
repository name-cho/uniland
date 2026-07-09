"""Позволяет запускать UniLand как `python -m uniland ...`.

Это кроссплатформенный способ без pip: пока есть Python, команда работает
на любой ОС. Например:  python -m uniland run script.uni
"""
from .cli import main

if __name__ == "__main__":
    main()
