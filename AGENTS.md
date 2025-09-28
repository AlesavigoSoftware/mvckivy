# Repository Guidelines

## Project Structure & Modules
- `src/mvckivy/`: main package (app, base_mvc, uix, network, properties, translate, utils, project_management). 
KV assets live alongside their Python modules (e.g., `uix/buttons/icon_button.py` + `icon_button.kv`).
- `test/`: runnable UI demos and probes (e.g., `test/dialog_with_text_field_test/`), useful for manual verification.
- `pyproject.toml`: Hatch/PEP 621 config with uv integration. Must be compatible with both `uv` and `pip` commands.

## Test and Dev Commands
- Install `uv` (if it is not presented) — a lightweight CLI for managing virtual envs and dependencies.
  - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - macOS/Linux: `curl -fsSL https://astral.sh/uv/install.sh | sh` or `wget -qO- https://astral.sh/uv/install.sh | sh`
- Create venv: `uv venv .venv` — sets up a `.venv/` USE ONLY if it doesn't exist.
- Install (dev): `uv sync` — creates a virtual env and installs with `[dev]` group. `uv sync --upgrade` must be called before tests execution.
- Run a demo: `uv run python test/<concrete_test>/main.py` (e.g., `test/lists_test/main.py`).
- Pytest: `uv run pytest -q` — headless tests preferred.

## Coding Style & Naming
- Python 3.11, 4‑space indents, UTF‑8.
- Follow Black defaults; keep lines ≤ 88 chars and files length ≤ 500 lines.
- Naming: modules/files `snake_case.py`, classes `PascalCase`, functions/vars `snake_case`, constants `UPPER_SNAKE_CASE`.
- KV files mirror Python names (e.g., `label.py` ↔ `label.kv`). 
- Keep widget classes in `uix/*`.

## Designing and Adding New Widgets

This section explains **how to design, implement, and test** new widgets in mvckivy. It reflects the project’s core patterns (MVC, alias-properties, and safe KV overrides) and includes **updated code samples** you can copy into `mvckivy/` modules.
Key constraints for new code:

* **No local/relative imports.** Always import from fully qualified modules (e.g., `from mvckivy.properties.extended_alias_property import ExtendedAliasProperty`).
* **Base vs. concrete:** the **base** widget contains **only core logic and properties** (no rigid KV layout). 
The **concrete** widget holds the **specific KV layout** and presentation logic. 
This allows multiple layouts for the same base behavior without subclassing chains.
* **Alias get/calc contract:** each alias getter must **call** a corresponding `_calc_*` method, and **both** must accept the `prop` parameter:
  * `_get_alias_padding(self, prop)` → `return self._calc_alias_padding(prop)`
  * `_calc_alias_padding(self, prop)` → actual calculation
* **Alias override safety:** use `AliasDedupeMixin` so a child’s KV rule **can override** a parent alias-driven property 
(even with a **constant**); the mixin will detach the parent alias’ internal bindings on that child instance.

### Step-by-Step Plan

1. **Design at a high level.**
   Decide the widget’s purpose and the minimal set of **core properties** and **sub-containers** it needs 
(e.g., leading/text/trailing areas in a list item).

2. **Create the Base widget (Python only).**
   * Inherit from `AliasDedupeMixin` and the appropriate Kivy/KivyMD bases.
   * Define **reactive inputs** as normal Kivy properties (`NumericProperty`, `BooleanProperty`, etc.).
   * Define **computed outputs** as `ExtendedAliasProperty`.
   * For every alias, implement **two methods**:
     * `_get_<name>(self, prop)` that **calls** `_calc_<name>(self, prop)`
     * `_calc_<name>(self, prop)` that returns the computed value
   * Keep the base class **KV-free** (no rigid layout).

3. **Enable KV overrides safely.**
   * Keep the base using alias properties (`alias_padding`, `alias_height`, etc.).
   * In concrete widgets’ KV, assign constants or alternative expressions to those same targets; `AliasDedupeMixin` will **detach** the base alias bindings on that instance when overridden.

4. **Create a Concrete widget (Python + KV).**
   * Subclass the base widget (or compose it) and define the **KV rule** that lays out its **specific structure** (containers, labels, icons, etc.).
   * Wire any event-based behavior specific to this variant.

5. **Trigger strategy.**
   * For **frequently changing** values (could change multiple times per frame), coalesce work using a **single `Clock.create_trigger`** and refresh once per frame.
   * For **rare toggles** (e.g., `disabled`, `use_divider`), update directly without a trigger.

6. **Testing.**
   * Unit-test alias computations and container routing without rendering.
   * Use graphical tests only where layout/interaction needs verification.
   * Ensure child KV overrides **do not call** parent alias getters on the child (the dedupe must detach them).

### Minimal, Working Examples

#### 1) Base List Container

```python
# mvckivy/uix/list.py
from __future__ import annotations

from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty
from kivymd.uix.gridlayout import MDGridLayout

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.utils.constants import DENSITY  # global density map {int: dp(...)}


class MKVList(AliasDedupeMixin, MDGridLayout):
    density = NumericProperty(0)
    use_divider = BooleanProperty(True)

    def _get_alias_padding(self, prop: ExtendedAliasProperty) -> list[float]:
        # ALWAYS call the calculator:
        return self._calc_alias_padding(prop)

    def _calc_alias_padding(self, prop: ExtendedAliasProperty) -> list[float]:
        # Top/bottom padding grows with density
        return [0, dp(8) + DENSITY.get(self.density, dp(0))]

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding,
        None,
        bind=("density", "padding"),
        cache=True,
        watch_before_use=True,
    )
```

```kv
# mvckivy/uix/list.kv
<MKVList>
    cols: 1
    adaptive_height: True
    padding: self.alias_padding
```
---

#### 2) Base List Item

```python
# mvckivy/uix/list_item_base.py
from __future__ import annotations

from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty

from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import DeclarativeBehavior, RectangularRippleBehavior, BackgroundColorBehavior
from kivymd.uix.behaviors.state_layer_behavior import StateLayerBehavior

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty
from mvckivy.properties.null_dispatcher import create_null_dispatcher
from mvckivy.utils.constants import DENSITY

class MKVBaseListItem(
    AliasDedupeMixin,
    DeclarativeBehavior,
    BackgroundColorBehavior,
    RectangularRippleBehavior,
    ThemableBehavior,
    StateLayerBehavior,
):
    density = NumericProperty(0)

    # Safe placeholder containers (avoid None)
    leading_container = ObjectProperty(create_null_dispatcher(children=[]), rebind=True, cache=True)
    text_container    = ObjectProperty(create_null_dispatcher(children=[]), rebind=True, cache=True)
    trailing_container= ObjectProperty(create_null_dispatcher(children=[]), rebind=True, cache=True)

    HEIGHTS = {0: dp(100), 1: dp(56), 2: dp(72), 3: dp(88)}

    # --- md_bg_color (example) ---
    def _get_alias_md_bg_color(self, prop: ExtendedAliasProperty) -> list[float]:
        return self._calc_alias_md_bg_color(prop)

    def _calc_alias_md_bg_color(self, prop: ExtendedAliasProperty) -> list[float]:
        if self.theme_bg_color == "Primary":
            return self.theme_cls.surfaceColor
        return self.md_bg_color

    alias_md_bg_color = ExtendedAliasProperty(
        _get_alias_md_bg_color,
        None,
        bind=("md_bg_color", "theme_bg_color", "theme_cls.surfaceColor"),
        cache=True,
        watch_before_use=True,
    )

    # --- height ---
    def _get_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self._calc_alias_height(prop)

    def _calc_alias_height(self, prop: ExtendedAliasProperty) -> float:
        return self.HEIGHTS[len(self.text_container.children)] + DENSITY.get(self.density, dp(0))

    alias_height = ExtendedAliasProperty(
        _get_alias_height, None, bind=("density", "text_container.children", "height"), cache=True, watch_before_use=True
    )
```

```kv
<MKVBaseListItem>
    size_hint_y: None
    md_bg_color: self.alias_md_bg_color
    height: self.alias_height
```

**Note**

---
* Every `_get_*` **must call** its `_calc_*` counterpart and accept `prop`.
* Do not use getattr or setattr for properties defined in the class body. 
Use `self.property_name` instead (e.g., `self.alias_height`, not `getattr(self, "alias_height")`).
Exceptions are cases like `[getattr(self, key) for key in keys]` where key is dynamic.
* For access to Properties itself use self.property('property_name') but only when necessary.

#### 3) Concrete List Item

```python
# mvckivy/uix/list.py
from __future__ import annotations

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

from mvckivy.uix.list import MKVBaseListItem

class MKVListItem(MKVBaseListItem, BoxLayout):
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        # If any of these change frequently, coalesce via a trigger
        self._trigger_layout = Clock.create_trigger(self._refresh_layout, 0)
        self.leading_container.bind(children=lambda *_: self._trigger_layout())
        self.text_container.bind(children=lambda *_: self._trigger_layout())
        self.trailing_container.bind(children=lambda *_: self._trigger_layout())

    def _refresh_layout(self, *_):
        # Example: align leading/trailing child depending on text rows
        if self.leading_container.children:
            self.leading_container.children[0].pos_hint = (
                {"top": 1} if len(self.text_container.children) == 3 else {"center_y": 0.5}
            )
        if self.text_container.children and self.trailing_container.children:
            self.trailing_container.children[0].pos_hint = (
                {"top": 1} if len(self.text_container.children) == 3 else {"center_y": 0.5}
            )
```

```kv
# mvckivy/uix/list_item.kv
<MKVListItem>
    orientation: "horizontal"
    leading_container: leading_container
    text_container: text_container
    trailing_container: trailing_container

    BoxLayout:
        id: leading_container
        size_hint_x: None
        width: 0

    AnchorLayout:
        anchor_y: "center"

        BoxLayout:
            id: text_container
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(2)

    BoxLayout:
        id: trailing_container
        size_hint_x: None
        width: 0
```

**Notes**

* The concrete widget **consumes** alias values from the base 
(via `self.alias_*` from the parent (Base) class).
* This KV file defines one **specific** presentation. 
You can create other variants with different KV while reusing the same base logic.
* **Important!** Main container class (`MKVListItem` here) must control 
the `leading_container`, `text_container`, and `trailing_container` (any inherited containers) dynamic properties.
That guarantees that all logic centrally routes through this instance, and avoids confusion if children are added directly to sub-containers.
Also, it allows to use basic classes like `BoxLayout` or `AnchorLayout` as the main container, without needing to subclass them,
and replace them with other layouts if needed by just changing the KV rule (keeping the same `MKVBaseListItem` in common).

### KV Override Examples (AliasDedupeMixin in action)

**Parent provides alias-driven padding; Child overrides with a constant:**

```python
# mvckivy/examples/list_override.py
from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty

from mvckivy.properties.alias_dedupe_mixin import AliasDedupeMixin
from mvckivy.properties.extended_alias_property import ExtendedAliasProperty

class Parent(AliasDedupeMixin, BoxLayout):
    ui_scale = NumericProperty(1.0)

    def _get_alias_padding(self, prop: ExtendedAliasProperty):
        return self._calc_alias_padding(prop)

    def _calc_alias_padding(self, prop: ExtendedAliasProperty):
        v = dp(8) * self.ui_scale
        return v, v, v, v

    alias_padding = ExtendedAliasProperty(
        _get_alias_padding, None, bind=("ui_scale",), cache=False, watch_before_use=True
    )

class Child(Parent):
    pass
```

```kv
# mvckivy/examples/list_override.kv
#:import dp kivy.metrics.dp

<Parent>:
    padding: self.alias_padding

<Child>:
    padding: dp(10)   # Constant override → parent alias bindings detached on the child
```

**Notes:** 
* the child’s `padding` stays at `dp(10)` regardless of `ui_scale` changes, while the parent remains dynamic. 
This is exactly what `AliasDedupeMixin` guarantees.
* When implementing a new widget, always inherit from `AliasDedupeMixin` to enable this safe override behavior.
* Remember that Behaviors (e.g., `ThemableBehavior`) should come **after** `AliasDedupeMixin` in the inheritance list 
and before any concrete BaseWidget class (e.g., `BoxLayout` or `BaseListItem`).
* All numeric parameters in both py and kv must use `dp(...)` to ensure density independence and avoid using strings like `"10dp"`.

### Important Note about theme_cls and ThemableBehavior
If your base widget inherits from `ThemableBehavior`, you must not use create_null_dispatcher inside its ObjectProperty defaultvalue.
This is because ThemableBehavior overrides the theme_cls property in its __init__ method, which happens after the ObjectProperty defaultvalue is set.
```python
    def __init__(self, **kwargs):
        if self.theme_cls is None:
            try:
                if not isinstance(
                    App.get_running_app().property("theme_cls", True),
                    ObjectProperty,
                ):
                    raise ValueError(
                        "KivyMD: App object must be inherited from "
                        "`kivymd.app.MDApp`"
                    )
            except AttributeError:
                raise ValueError(
                    "KivyMD: App object must be initialized before loading "
                    "root widget. See "
                    "https://github.com/kivymd/KivyMD/wiki/Modules-Material-App#exceptions"
                )
            self.theme_cls = App.get_running_app().theme_cls

        super().__init__(**kwargs)
```
As the result, if you use `create_null_dispatcher` in the `ObjectProperty` defaultvalue, the `theme_cls` property will not be `None` when assigned,
and `theme_cls` will not be set correctly. DO NOT USE `create_null_dispatcher` in this case.
Correct way to use `theme_cls` with `ExtendedAliasProperty`:
```python
theme_cls = ObjectProperty(None, rebind=True, cache=True)
alias_md_bg_color = ExtendedAliasProperty(
    _get_alias_md_bg_color,
    None,
    bind=("md_bg_color", "theme_bg_color", "theme_cls.surfaceColor"),
    cache=True,
    watch_before_use=True,
)
```

### What (and how) to Test

1. **Alias computations**: change inputs, verify alias outputs:
   * `density → alias_spacing`, `text_container.children → alias_height`, etc.
2. **KV overrides detach aliases**:
   * If a child sets `padding: dp(10)`, ensure the base’s alias getter is **not called** on the child when dependencies change.
3. **Container routing** in concrete widgets:
   * Adding `MKVListItemSupportingText` ends up in `text_container`, etc.
   * Using straight links to Child widgets through `leading_container`, `text_container`, `trailing_container` etc. 
   prefers over using other access ways using self.child[index] or self.ids.child_name!
4. **Trigger consolidation**:
   * Frequently changing inputs should coalesce into a single `_refresh_layout` per frame.
5. **Rare toggles** (e.g., `disabled`, `use_divider`) update directly without unintended side effects.
6. **Test app**: for tests must be used `MKVApp` as a base class for the App, not `MDApp` or `App` directly. Example:
```python
from mvckivy.app import MKVApp
class TestApp(MKVApp):
    ...
```

### Summary

* **Base widgets**: logic + alias properties (with `_get_*` calling `_calc_*`, both accepting `prop`).
* **Concrete widgets**: specific KV layouts consuming alias values from the base.
* **Override safety**: `AliasDedupeMixin` lets child KV assign constants or alternate expressions to parent targets; 
parent alias deps are detached only for that instance.
* **Triggers**: batch fast-changing updates; keep rare toggles simple.
* **Testing**: verify alias math, container routing, and that KV overrides truly detach parent aliases on children.

This pattern keeps your UI **reactive**, **customizable**, and **safe to override** — and makes it 
straightforward to maintain multiple layout variants over the same behavioral core.

## Testing Guidelines
- Test frameworks: `pytest` for CI‑friendly UI tests.
- Manual demos: run modules under `test/` to verify behavior changes.
- Test names: files `test_*.py`, functions `test_*`. Prefer small, focused assertions.
- Coverage: prioritize core widgets, behaviors, and `base_mvc` logic.
- Dev frameworks: `kivymd-production-fork` is a priority for UI components. 
It locates at `.venv/Lib/site-packages/kivymd` and must be read before implementing any new widget.
For example, `MDIconButton` is a base for `mvckivy.uix.buttons.icon_button.MKVIconButton` and should be understood first.
`MDIconButton` locates at `.venv/Lib/site-packages/kivymd/uix/button.py` 
and this file should be read before implementing `MKVIconButton`.

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject, optional body. Examples: `Add headless-kivy`, `Update imports`, `Fix icon_button hover state`.
- PRs: clear description, linked issues (`Fixes #123`), screenshots or short clips for UI changes, 
steps to reproduce/verify, and notes on migration/compat.

## Security & Configuration Tips
- Do not commit local envs (`.venv/`) or large assets; follow `.gitignore`.
- Pin external forks via `pyproject.toml`/`uv.lock`; avoid ad‑hoc edits in `site-packages`.
- Prefer `uv run` to ensure consistent env when invoking tools.
