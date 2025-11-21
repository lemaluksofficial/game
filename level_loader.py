# level_loader.py

import os

# базовая папка проекта (где лежит этот файл)
BASE_DIR = os.path.dirname(__file__)
LEVELS_DIR = os.path.join(BASE_DIR, "assets", "levels")


def load_level(level_name="level1"):
    """
    Загружает уровень из файла assets/levels/<level_name>.txt
    и возвращает список строк.
    """
    path = os.path.join(LEVELS_DIR, f"{level_name}.txt")

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip("\n")]

    return lines
