from __future__ import annotations

from pathlib import Path
from typing import NotRequired, TypedDict, TYPE_CHECKING

from mvckivy.project_management import PathItem

if TYPE_CHECKING:
    from mvckivy.mvc_base import BaseModel, BaseController, BaseScreen
    from mvckivy.app import MVCApp


class ScreensSchema(TypedDict):
    """
    TypedDict representing the schema for screens.

    :ivar name: The unique name of the screen schema.
    :vartype name: str

    :ivar model: The model class associated with the screen.
    :vartype model: Type[BaseModel]

    :ivar controller: The controller class handling screen logic.
    :vartype controller: Type[BaseController]

    :ivar screen: The screen implementation class.
    :vartype screen: Type[BaseScreen]

    :ivar children: list of child screen names.
    :vartype children: list[str]

    :ivar parent: Optional parent screen name.
    :vartype parent: str | None
    """

    name: str
    model_cls: type[BaseModel]
    controller_cls: type[BaseController]
    screen_cls: type[BaseScreen]
    children: NotRequired[list[str]]
    parent: NotRequired[str | None]
    kv_path: NotRequired[str | PathItem | Path | None]


class AppSchema:
    _schema: list[ScreensSchema] | None = None
    _ordered_schema: dict[str, int] | None = None

    @classmethod
    def get_schema(cls, recreate: bool = False) -> list[ScreensSchema]:
        """
        Retrieve and validate the application screen schema.
        Formats raw schema entries and runs full validation checks.

        :param recreate: If True, forces re-formatting even if schema exists.
        :return: Formatted and validated list of ScreensSchema dicts.
        """
        if cls._schema is None or recreate:
            cls._schema = cls.create_schema()
            cls._format_schema()
            cls._check_schema()

        return cls._schema

    @classmethod
    def _format_schema(cls) -> None:
        """
        Orchestrate schema normalization, relationship propagation and ordering.

        Steps order follows their invocation sequence for clarity:
        1) Ensure defaults for optional keys that are safe to auto-fill.
        2) Propagate parent relationships from children's declarations.
        3) Ensure parent/children consistency in both directions.
        4) Normalize kv_path: resolve explicit values, compute defaults, validate existence.
        5) Compute stable linear ordering for later validation checks.
        """
        schema = cls._schema
        if not schema:
            return

        cls._ensure_defaults(schema)
        cls._propagate_parents_to_children(schema)
        cls._ensure_parent_children_bidirectional(schema)
        cls._normalize_kv_paths(schema)
        cls._ordered_schema, cls._schema = cls._compute_linear_ordering(schema)

    @staticmethod
    def _ensure_defaults(schema: list[ScreensSchema]) -> None:
        """
        Ensure each schema entry contains default values for optional keys.

        Applied defaults:
        - "children" defaults to an empty list if not present.
        - "parent" defaults to None if not present.

        Intentionally NOT defaulting "kv_path":
        We keep absence of the key distinguishable from an explicit None.
        This is required by kv_path normalization rules.
        """
        for entry in schema:
            entry.setdefault("children", [])
            entry.setdefault("parent", None)
            # Do not set default for "kv_path" to preserve intent

    @staticmethod
    def _normalize_kv_paths(schema: list[ScreensSchema]) -> None:
        """
        Normalize and validate the `kv_path` field for each entry.

        Rules:
        - If the user did not provide `kv_path` (key absent), compute a default
          directory path according to the project structure and validate it exists.
            - Root screen: `views/<screen_name>`
            - Child screen: `<parent_dir>/children/<screen_name>`
        - If the user explicitly set `kv_path` to None, keep it as None.
        - Otherwise, wrap the provided path into `PathItem`, validate existence,
          and persist it.

        The function resolves parent chains recursively to build child paths.
        """
        from kivy.app import App

        app: MVCApp = App.get_running_app()
        if app:
            proj_dir: PathItem = app.path_manager.proj_dir
        else:
            proj_dir: PathItem = PathItem(Path("."))

        by_name: dict[str, ScreensSchema] = {e["name"]: e for e in schema}
        cache: dict[str, PathItem | None] = {}

        def assert_exists(screen_name: str, p: PathItem | None) -> None:
            if p is not None and not p.path().exists():
                raise FileNotFoundError(
                    f"Directory for screen '{screen_name}' not found: {p}"
                )

        def resolve(name: str) -> PathItem | None:
            if name in cache:
                return cache[name]

            entry = by_name[name]
            if "kv_path" not in entry:
                parent_name = entry.get("parent")
                if parent_name:
                    parent_path = resolve(parent_name)
                    if parent_path is None:
                        cache[name] = None
                        entry["kv_path"] = None
                        return None
                    default_path = parent_path.join("children", name)
                else:
                    default_path = proj_dir.join("views", name)

                assert_exists(name, default_path)
                cache[name] = default_path
                entry["kv_path"] = default_path
                return default_path

            provided = entry["kv_path"]
            if provided is None:
                cache[name] = None
                return None

            path_item = (
                provided if isinstance(provided, PathItem) else PathItem(provided)
            )
            assert_exists(name, path_item)
            entry["kv_path"] = path_item
            cache[name] = path_item
            return path_item

        for name in by_name.keys():
            resolve(name)

    @staticmethod
    def _propagate_parents_to_children(schema: list[ScreensSchema]) -> None:
        """
        Populate child entries' `parent` field based on their parent's `children` list.

        For each declared child name present in the schema, set that child's `parent`
        to the enclosing entry's name. This helps keep parent links consistent when
        only children are declared.
        """
        lookup: dict[str, ScreensSchema] = {entry["name"]: entry for entry in schema}
        for entry in schema:
            for child_name in entry["children"]:
                child = lookup.get(child_name)
                if child:
                    child["parent"] = entry["name"]

    @staticmethod
    def _ensure_parent_children_bidirectional(schema: list[ScreensSchema]) -> None:
        """
        Ensure parent/child relationships are bidirectional.

        If an entry specifies a `parent`, append the entry's name to that parent's
        `children` list when missing. This makes the relationship consistent both ways.
        """
        lookup: dict[str, ScreensSchema] = {entry["name"]: entry for entry in schema}
        for entry in schema:
            parent_name = entry.get("parent")
            if parent_name:
                parent = lookup.get(parent_name)
                if parent and entry["name"] not in parent["children"]:
                    parent["children"].append(entry["name"])

    @classmethod
    def _compute_linear_ordering(
        cls, schema: list[ScreensSchema]
    ) -> tuple[dict[str, int], list[ScreensSchema]]:
        """
        Compute a deterministic linear ordering of screens and update class state.

        Ordering rules:
        - If `app_screen` exists, perform DFS from it preserving declared child order.
        - Then append any remaining nodes in the original declaration order.
        - Populate `cls._ordered_schema` mapping names to indices.
        - Reorder `cls._schema` according to the computed ordering.

        This ordering is used by later validation checks that expect a stable index map.
        """
        lookup: dict[str, ScreensSchema] = {entry["name"]: entry for entry in schema}
        original_index: dict[str, int] = {
            entry["name"]: i for i, entry in enumerate(schema)
        }
        root_name = "app_screen"
        visited: set[str] = set()
        linear_order: list[str] = []

        def dfs(node_name: str) -> None:
            if node_name in visited or node_name not in lookup:
                return
            visited.add(node_name)
            linear_order.append(node_name)
            for child_name in lookup[node_name].get("children", []):
                if child_name in lookup:
                    dfs(child_name)

        if root_name in lookup:
            dfs(root_name)

        for name in sorted(lookup.keys(), key=lambda n: original_index.get(n, 10**9)):
            if name not in visited:
                dfs(name)

        index_map = {name: i for i, name in enumerate(linear_order)}
        ordered_schema = list(
            sorted(schema, key=lambda s: index_map.get(s["name"], 10**9))
        )
        return index_map, ordered_schema

    # register_screen_dirs and register_screen_dir were removed. Their logic
    # is now part of `_normalize_kv_paths`, which computes defaults and validates
    # existence directly into the `kv_path` field of each schema entry.

    @classmethod
    def _check_schema(cls) -> None:
        """
        Perform all schema validation checks by delegating to specialized methods.

        :raises ValueError: If any validation fails.
        """
        schema = cls._schema

        cls._check_duplicates(schema)
        cls._check_children_exist(schema)
        cls._check_no_self_child(schema)
        cls._check_parent_exists(schema)
        cls._check_parent_in_children(schema)
        cls._check_no_child_parent_cycles(schema)
        cls._check_single_screen_exists(schema, "app_screen")
        cls._check_single_screen_exists(schema, "initial_screen")
        cls._check_initial_screen_position(schema)

    @staticmethod
    def _check_duplicates(schema: list[ScreensSchema]) -> None:
        """
        Ensure screen names are unique.

        :raises ValueError: If duplicate names are found.
        """
        names = [s["name"] for s in schema]
        if len(names) != len(set(names)):
            raise ValueError("Schema contains duplicate screen names")

    @staticmethod
    def _check_children_exist(schema: list[ScreensSchema]) -> None:
        """
        Ensure each listed child is defined in the schema.

        :raises ValueError: If a child name is missing.
        """
        names = {s["name"] for s in schema}
        for s in schema:
            for child in s["children"]:
                if child not in names:
                    raise ValueError(f"Child screen '{child}' not found in schema")

    @staticmethod
    def _check_no_self_child(schema: list[ScreensSchema]) -> None:
        """
        Ensure no screen lists itself as a child.

        :raises ValueError: If a screen is its own child.
        """
        for s in schema:
            if s["name"] in s["children"]:
                raise ValueError(f"Screen '{s['name']}' cannot be its own child")

    @staticmethod
    def _check_parent_exists(schema: list[ScreensSchema]) -> None:
        """
        Ensure each specified parent exists in the schema.

        :raises ValueError: If a parent name is missing.
        """
        names = {s["name"]: s for s in schema}
        for s in schema:
            parent = s.get("parent")
            if parent and parent not in names:
                raise ValueError(f"No such parent: '{parent}' for '{s['name']}'")

    @staticmethod
    def _check_parent_in_children(schema: list[ScreensSchema]) -> None:
        """
        Ensure that if a screen specifies a parent, it appears in that parent's children list.

        :raises ValueError: If relationship is not bidirectional.
        """
        lookup = {s["name"]: s for s in schema}
        for s in schema:
            parent = s.get("parent")
            if parent:
                if s["name"] not in lookup[parent]["children"]:
                    raise ValueError(
                        f"Parent '{parent}' of '{s['name']}' is not aware of this child"
                    )

    @staticmethod
    def _check_no_child_parent_cycles(schema: list[ScreensSchema]) -> None:
        """
        Ensure there are no cyclic parent relationships.

        :raises ValueError: If a cycle is detected in parent chains.
        """
        lookup = {s["name"]: s for s in schema}
        for s in schema:
            visited = set()
            current = s.get("parent")
            while current:
                if current in visited:
                    cycle = " -> ".join(list(visited) + [current])
                    raise ValueError(f"Cyclic parent relationship detected: {cycle}")
                visited.add(current)
                current = lookup[current].get("parent")

    @staticmethod
    def _check_single_screen_exists(
        schema: list[ScreensSchema], screen_name: str
    ) -> None:
        """
        Ensure screen with name "initial screen" exists.

        :raises ValueError: If there is no such screen or there are more than one of them.
        """
        s_c = 0
        for s in schema:
            if s["name"] == screen_name:
                s_c += 1

        if s_c == 0:
            raise ValueError(f"There is no screen with name '{screen_name}' in schema")
        elif s_c > 1:
            raise ValueError(
                f"There are more than one screen with name '{screen_name}' in schema"
            )

    @classmethod
    def _check_initial_screen_position(cls, schema: list[ScreensSchema]) -> None:
        lookup = {s["name"]: s for s in schema}
        root = lookup.get("app_screen")
        init = lookup.get("initial_screen")
        if not root or not init:
            return

        is_child_of_root = init.get(
            "parent"
        ) == "app_screen" or "initial_screen" in root.get("children", [])
        if not is_child_of_root:
            raise ValueError("initial_screen must be a direct child of 'app_screen'")

        if not cls._ordered_schema:
            raise ValueError("Ordered schema indices are not computed")

        try:
            root_idx = cls._ordered_schema["app_screen"]
            init_idx = cls._ordered_schema["initial_screen"]
        except KeyError:
            raise ValueError("Ordered indices for required screens are missing")

        if init_idx != root_idx + 1:
            raise ValueError(
                "initial_screen must be registered immediately after 'app_screen'"
            )

        for name, entry in lookup.items():
            if name in ("app_screen", "initial_screen"):
                continue
            if entry.get("parent") == "app_screen":
                other_idx = cls._ordered_schema.get(name)
                if other_idx is not None and other_idx < init_idx:
                    raise ValueError(
                        "initial_screen must be earlier than other first-level screens"
                    )

    @classmethod
    def create_schema(cls) -> list[dict[str, str | type]]:
        """
        Should be implemented by subclasses to return raw screens schema list.
        """
        raise NotImplementedError()
