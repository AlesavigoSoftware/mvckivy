import logging
from pathlib import Path
from kivy.lang import BuilderBase, Builder
from typing import Union, Iterable, Literal

from src.mvckivy.project_management.path_manager import PathItem, MVCPathManager


logger = logging.getLogger("mvckivy")


class MVCBuilder(BuilderBase):
    """
    Recursively loads or unloads all .kv files under a directory,
    with support for directory-name filters specified per-call.
    Inherits from Kivy's Builder.

    This class provides two main operations:
      - load_all_kv_files
      - unload_all_kv_files

    Both operations accept an optional list of directory names to exclude
    (case-insensitive) from processing.
    """

    @staticmethod
    def _is_excluded(kv_path: Path, filters: set[str]) -> bool:
        """
        Determines whether a given .kv file should be skipped based on
        its path and provided filter set.

        Exclusion rules:
          - Filename is exactly 'style.kv'.
          - Any path segment is in the built-in exclusion set: {'venv', '.buildozer', 'kivymd'}.
          - Any path segment is in the provided filters set.
          - Path contains a segment matching '__MACOS' (case-insensitive).

        :param kv_path: Path to a .kv file.
        :param filters: Set of lowercase directory names to exclude.
        :returns: True if the file should be skipped, False otherwise.
        """
        name: str = kv_path.name.lower()
        if name == "style.kv":
            return True

        parts: set[str] = set(p.lower() for p in kv_path.parts)
        # Built-in exclusion rules
        if parts & {"venv", ".buildozer", "kivymd"}:
            return True
        # User-provided filters
        if parts & filters:
            return True
        # macOS artifact folders
        if "__macos" in str(kv_path).lower():
            return True

        return False

    @classmethod
    def _process_files(
        cls,
        directory: Path,
        mode: Literal["load", "unload"],
        directory_filters: Iterable[str] | None = None,
    ) -> None:
        """
        Core routine that locates all .kv files and performs the specified operation.

        :param directory: Root directory to search for .kv files.
        :param mode: Operation mode ('load' or 'unload').
        :param directory_filters: Optional iterable of directory names to skip.
        """
        filters: set[str] = {f.lower() for f in (directory_filters or [])}

        for kv_file in directory.rglob("*.kv"):
            if cls._is_excluded(kv_file, filters):
                continue

            try:
                if mode == "load":
                    Builder.load_file(filename=str(kv_file))
                    logger.debug(f"Loaded KV file: {kv_file}")
                else:
                    if not hasattr(cls, "unload_file"):
                        logger.error(
                            "Builder.unload_file not available; cannot unload."
                        )
                        return
                    Builder.unload_file(filename=str(kv_file))
                    logger.debug(f"Unloaded KV file: {kv_file}")
            except Exception as exc:
                logger.error(f"{mode.capitalize()} failed for {kv_file}: {exc}")

    @classmethod
    def load_all_kv_files(
        cls,
        directory: Union[str, Path, PathItem],
        directory_filters: Iterable[str | Path | PathItem] | None = None,
    ) -> None:
        """
        Loads all .kv files under the specified directory, applying exclusions.

        :param directory: Root directory to search.
        :param directory_filters: Optional list of directory names to ignore.
        """
        path = directory.path() if isinstance(directory, PathItem) else Path(directory)
        dir_filters = (
                d.str() if isinstance(d, PathItem) else str(d)
                for d in directory_filters
            ) if directory_filters else None
        cls._process_files(
            path,
            mode="load",
            directory_filters=dir_filters,
        )

    @classmethod
    def unload_all_kv_files(
        cls,
        directory: Union[str, Path, PathItem],
        directory_filters: Iterable[str | Path | PathItem] | None = None,
    ) -> None:
        """
        Unloads all previously loaded .kv files under the specified directory,
        applying the same exclusion rules.

        :param directory: Root directory to search.
        :param directory_filters: Optional list of directory names to ignore.
        """
        path = directory.path() if isinstance(directory, PathItem) else Path(directory)
        dir_filters = (
                d.str() if isinstance(d, PathItem) else str(d)
                for d in directory_filters
            ) if directory_filters else None
        cls._process_files(
            path,
            mode="unload",
            directory_filters=dir_filters,
        )

    @classmethod
    def load_libs_kv_files(cls) -> None:
        """
        Load all KivyMD and MVCKivy KV files for the application.
        Order of loading is important! MVCKivy files always must be loaded after KivyMD files.
        :return: None
        """
        cls._load_kivymd_kv_files()
        cls._load_mvckivy_kv_files()

    @classmethod
    def _load_kivymd_kv_files(cls) -> None:
        """
        Register the MDKivy files for the application.
        This function is called to ensure that all necessary MDKivy files are loaded.
        """
        from kivymd.uix.segmentedbutton import (
            MDSegmentedButton,
            MDSegmentedButtonItem,
            MDSegmentButtonIcon,
            MDSegmentButtonLabel,
        )
        from kivymd.uix.scrollview import MDScrollView
        from kivymd.uix.recycleview import MDRecycleView
        from kivymd.uix.responsivelayout import MDResponsiveLayout
        from kivymd.uix.sliverappbar import (
            MDSliverAppbar,
            MDSliverAppbarContent,
            MDSliverAppbarHeader,
        )
        from kivymd.uix.navigationrail import (
            MDNavigationRailItem,
            MDNavigationRail,
            MDNavigationRailFabButton,
            MDNavigationRailMenuButton,
            MDNavigationRailItemIcon,
            MDNavigationRailItemLabel,
        )
        from kivymd.uix.swiper import MDSwiper
        from kivymd.uix.widget import MDWidget
        from kivymd.uix.floatlayout import MDFloatLayout
        from kivymd.uix.anchorlayout import MDAnchorLayout
        from kivymd.uix.screen import MDScreen
        from kivymd.uix.screenmanager import MDScreenManager
        from kivymd.uix.recyclegridlayout import MDRecycleGridLayout
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.relativelayout import MDRelativeLayout
        from kivymd.uix.gridlayout import MDGridLayout
        from kivymd.uix.stacklayout import MDStackLayout
        from kivymd.uix.expansionpanel import (
            MDExpansionPanel,
            MDExpansionPanelHeader,
            MDExpansionPanelContent,
        )
        from kivymd.uix.fitimage import FitImage
        from kivymd.uix.tooltip import (
            MDTooltip,
            MDTooltipPlain,
            MDTooltipRich,
            MDTooltipRichActionButton,
            MDTooltipRichSubhead,
            MDTooltipRichSupportingText,
        )
        from kivymd.uix.bottomsheet import (
            MDBottomSheet,
            MDBottomSheetDragHandle,
            MDBottomSheetDragHandleButton,
            MDBottomSheetDragHandleTitle,
        )
        from kivymd.uix.navigationbar import (
            MDNavigationBar,
            MDNavigationItem,
            MDNavigationItemLabel,
            MDNavigationItemIcon,
        )
        from kivymd.uix.card import MDCard
        from kivymd.uix.divider import MDDivider
        from kivymd.uix.chip import (
            MDChip,
            MDChipLeadingAvatar,
            MDChipLeadingIcon,
            MDChipTrailingIcon,
            MDChipText,
        )
        from kivymd.uix.imagelist import (
            MDSmartTile,
            MDSmartTileOverlayContainer,
            MDSmartTileImage,
        )
        from kivymd.uix.label import MDLabel, MDIcon
        from kivymd.uix.badge import MDBadge
        from kivymd.uix.behaviors.hover_behavior import HoverBehavior
        from kivymd.uix.behaviors.focus_behavior import FocusBehavior
        from kivymd.uix.behaviors.magic_behavior import MagicBehavior
        from kivymd.uix.refreshlayout import MDScrollViewRefreshLayout
        from kivymd.uix.selectioncontrol import MDCheckbox, MDSwitch
        from kivymd.uix.slider import MDSlider
        from kivymd.uix.progressindicator import (
            MDCircularProgressIndicator,
            MDLinearProgressIndicator,
        )
        from kivymd.uix.tab import (
            MDTabsPrimary,
            MDTabsSecondary,
            MDTabsItem,
            MDTabsItemSecondary,
            MDTabsBadge,
            MDTabsItemIcon,
            MDTabsItemText,
            MDTabsCarousel,
        )
        from kivymd.uix.textfield import (
            MDTextField,
            MDTextFieldHelperText,
            MDTextFieldMaxLengthText,
            MDTextFieldHintText,
            MDTextFieldLeadingIcon,
            MDTextFieldTrailingIcon,
        )
        from kivymd.uix.dropdownitem import (
            MDDropDownItem,
            MDDropDownItemText,
        )
        from kivymd.uix.circularlayout import MDCircularLayout
        from kivymd.uix.hero import MDHeroFrom, MDHeroTo

    @classmethod
    def _load_mvckivy_kv_files(cls) -> None:
        """
        Register the MVCKivy files for the application.
        This function is called to ensure that all necessary MVCKivy files are loaded.
        """
        cls.load_all_kv_files(MVCPathManager.proj_dir)
