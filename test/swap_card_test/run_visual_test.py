from __future__ import annotations

import shutil
from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window


BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / ".cache"


def _clear_cache_dir():
    if CACHE_DIR.exists():
        for p in CACHE_DIR.glob("*.png"):
            try:
                p.unlink()
            except Exception:
                pass
    else:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)


def run_case(window_size: tuple[int, int], tag: str) -> Path:
    """Запускает приложение, разворачивает меню и делает скриншот.

    Возвращает путь к созданному изображению (который отдаёт Kivy).
    """

    # импортируем приложение локально из файла демо
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "swap_card_test_main", str(BASE_DIR / "main.py")
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    Window.size = window_size
    app = mod.DemoApp()
    snap_path_holder: dict[str, str | None] = {"p": None}

    def expand_and_shoot(*_):
        # Разворачиваем карточку полностью
        root = app.root
        if root is None:
            root = app.build()
        # гарантируем целевой размер окна после сборки интерфейса
        Window.size = window_size
        try:
            root.animate_to(0.0)
        except Exception:
            pass

        def _shoot(*__):
            # Имя файла — в temp, но Kivy всё равно добавляет суффикс 000N
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            fname = f"swap_card_{tag}.png"
            target = (CACHE_DIR / fname).resolve()
            path = Window.screenshot(name=str(target))
            snap_path_holder["p"] = path
            # подождём, чтобы запись точно успела
            Clock.schedule_once(lambda *_: app.stop(), 0.2)

        Clock.schedule_once(_shoot, 0.6)

    # даём время на сборку интерфейса
    Clock.schedule_once(expand_and_shoot, 0.6)
    app.run()

    res = Path(snap_path_holder["p"]) if snap_path_holder["p"] else Path()
    return res


def main():
    # очистка .cache перед запуском
    _clear_cache_dir()

    # Мобильный режим (горизонтальная ориентация) — единственный тестовый прогон
    img = run_case((820, 420), tag="mobile_landscape")
    print(
        "MOBILE-LANDSCAPE:",
        img,
        "exists=",
        img.exists(),
        "size=",
        img.stat().st_size if img.exists() else -1,
    )


if __name__ == "__main__":
    main()
