"""
project_generator.py

Module for generating the skeleton of an MVCKivy application project.

This module provides a ProjectGenerator that creates directories and files for
models, controllers, and views based on a list of screen definitions.
"""

import logging
from pathlib import Path
from typing import List

# Configure logger
logger = logging.getLogger("mvckivy")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class DirectoryBuilder:
    """
    Utility for creating directories and optional __init__.py files.

    :cvar path: The directory path to ensure exists.
    :cvar with_init: Indicates whether to create an __init__.py in the directory.
    """

    @staticmethod
    def ensure_dir(path: Path, with_init: bool = False):
        """
        Ensure that a directory exists, optionally adding an __init__.py file.

        :param path: Filesystem path of the directory to create.
        :type path: Path
        :param with_init: If True, create an __init__.py inside the directory.
        :type with_init: bool
        """
        path.mkdir(parents=True, exist_ok=True)
        if with_init:
            (path / "__init__.py").touch()


class FileBuilder:
    """
    Utility for writing content to files.

    :cvar path: The file path to write to.
    :cvar content: The textual content to write.
    """

    @staticmethod
    def write(path: Path, content: str):
        """
        Write text content to a file, creating or overwriting as needed.

        :param path: Filesystem path of the file to write.
        :type path: Path
        :param content: Text content to write to the file.
        :type content: str
        """
        path.write_text(content, encoding="utf-8")


class ScreenDefinition:
    """
    Represents a screen definition, converting snake_case to PascalCase.

    :param snake_name: The screen name in snake_case.
    :type snake_name: str

    :ivar snake: The original screen name in snake_case.
    :ivar pascal: The generated class name in PascalCase.
    """

    def __init__(self, snake_name: str):
        self.snake = snake_name
        # e.g. "sign_in_screen" → "SignInScreen"
        self.pascal = "".join(part.capitalize() for part in snake_name.split("_"))


class ProjectGenerator:
    """
    Generates the project directory and file structure for an MVCKivy app.

    :param root: Root directory for project skeleton creation.
    :type root: Path
    :param screens: List of screen definitions to generate.
    :type screens: List[ScreenDefinition]
    """

    def __init__(self, root: Path, screens: List[ScreenDefinition]):
        """
        Initialize the generator with project root and screens.

        :param root: Filesystem path that will contain generated directories.
        :type root: Path
        :param screens: Definitions of screens to scaffold.
        :type screens: List[ScreenDefinition]
        """
        self.root = root
        self.screens = screens

    def generate(self):
        """
        Build the complete project structure.

        Creates base directories and then iterates over each screen to create
        model, controller, and view files along with necessary directories.
        """
        self._make_root_dirs()
        for screen in self.screens:
            self._make_model(screen)
            self._make_controller(screen)
            self._make_view(screen)
        logger.info("Project structure has been successfully created.")

    def _make_root_dirs(self):
        """
        Create top-level directories for assets, logs, utils, controllers,
        models, and views.
        """
        # Create base directories
        for d, need_init in [
            ("assets", False),
            ("logs", False),
            ("utils", False),
            ("controllers", True),
            ("models", True),
            ("views", True),
        ]:
            DirectoryBuilder.ensure_dir(self.root / d, with_init=need_init)

    def _make_model(self, screen: ScreenDefinition):
        """
        Scaffold the model directory and file for a given screen.

        :param screen: Definition of the screen to generate model for.
        :type screen: ScreenDefinition
        """
        dir_path = self.root / "models" / screen.snake
        DirectoryBuilder.ensure_dir(dir_path, with_init=True)

        file_path = dir_path / f"{screen.pascal}Model.py"
        content = f"""from mvckivy import BaseModel

class {screen.pascal}Model(BaseModel):
    pass
"""
        FileBuilder.write(file_path, content)
        logger.debug(f"Model created: {file_path}")

    def _make_controller(self, screen: ScreenDefinition):
        """
        Scaffold the controller directory and file for a given screen.

        :param screen: Definition of the screen to generate controller for.
        :type screen: ScreenDefinition
        """
        dir_path = self.root / "controllers" / screen.snake
        DirectoryBuilder.ensure_dir(dir_path, with_init=True)

        file_path = dir_path / f"{screen.pascal}Controller.py"
        content = f"""from mvckivy import BaseController

class {screen.pascal}Controller(BaseController):
    pass
"""
        FileBuilder.write(file_path, content)
        logger.debug(f"Controller created: {file_path}")

    def _make_view(self, screen: ScreenDefinition):
        """
        Scaffold the view directory, Python class, and KV template for a given screen.

        :param screen: Definition of the screen to generate view for.
        :type screen: ScreenDefinition
        """
        dir_path = self.root / "views" / screen.snake
        DirectoryBuilder.ensure_dir(dir_path, with_init=True)

        # Python screen class
        file_py = dir_path / f"{screen.pascal}.py"
        content_py = f"""from mvckivy import BaseScreen

class {screen.pascal}(BaseScreen):
    pass
"""
        FileBuilder.write(file_py, content_py)
        logger.debug(f"Screen class created: {file_py}")

        # KV layout template
        file_kv = dir_path / f"{screen.snake}.kv"
        content_kv = f"""<{screen.pascal}Screen>:
    # define your KV layout here
"""
        FileBuilder.write(file_kv, content_kv)
        logger.debug(f"KV file created: {file_kv}")


if __name__ == "__main__":
    # List all screens of your application
    screen_names = [
        "initial_screen",
        "sign_in_screen",
        "main_screen",
        "home_screen",
        "mission_screen",
        "ground_station_screen",
        "onboard_screen",
        "settings_screen",
    ]
    screens = [ScreenDefinition(name) for name in screen_names]

    project_root = Path.cwd()  # or specify your own path
    gen = ProjectGenerator(project_root, screens)
    gen.generate()
    # Use logger instead of print
    logger.info(
        "Project skeleton with directories and screen files has been generated!"
    )
