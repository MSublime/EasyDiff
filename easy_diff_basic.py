"""
Easy Diff Basic Commands.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import sublime_plugin
from os.path import basename
from EasyDiff.easy_diff_global import load_settings, log, get_external_diff, get_target, get_group_view
from EasyDiff.easy_diff_dynamic_menu import update_menu
from EasyDiff.easy_diff import EasyDiffView, EasyDiffInput, EasyDiff

LEFT = None


###############################
# Helper Functions
###############################
def diff(left, right, external=False):
    """
    Initiate diff by getting left side and right side compare.

    Call the appropriate diff method and call internal or external diff.
    """

    lw = None
    rw = None
    lv = None
    rv = None

    for w in sublime.windows():
        if w.id() == left["win_id"]:
            lw = w
        if w.id() == right["win_id"]:
            rw = w
        if lw is not None and rw is not None:
            break

    if lw is not None:
        for v in lw.views():
            if v.id() == left["view_id"]:
                lv = v
                break
    else:
        if left["clip"]:
            lv = left["clip"]

    if rw is not None:
        for v in rw.views():
            if v.id() == right["view_id"]:
                rv = v
                break
    else:
        if right["clip"]:
            rv = right["clip"]

    if lv is not None and rv is not None:
        ext_diff = get_external_diff()
        if external:
            EasyDiff.extcompare(EasyDiffInput(lv, rv, external=True), ext_diff)
        else:
            EasyDiff.compare(EasyDiffInput(lv, rv))
    else:
        log("Can't compare")


###############################
# Helper Classes
###############################
class _EasyDiffSelection(object):
    """Handle selection diff."""

    def get_selections(self):
        """Get the selections."""

        bfr = ""
        length = len(self.view.sel())
        for s in self.view.sel():
            if s.size() == 0:
                continue
            bfr += self.view.substr(s)
            if length > 1:
                bfr += "\n"
            length -= 1
        return bfr

    def get_encoding(self):
        """Get view encoding."""

        return self.view.encoding()

    def has_selections(self):
        """Check if view has a valid selection."""

        selections = False
        if bool(load_settings().get("multi_select", False)):
            for s in self.view.sel():
                if s.size() > 0:
                    selections = True
                    break
        else:
            selections = len(self.view.sel()) == 1 and self.view.sel()[0].size() > 0
        return selections


###############################
# Set View
###############################
class EasyDiffSetLeftCommand(sublime_plugin.WindowCommand, _EasyDiffSelection):
    """Set left side command."""

    def run(self, external=False, paths=[], group=-1, index=-1):
        """Run command."""

        global LEFT
        self.external = external
        self.set_view(paths, group, index)
        if self.view is not None:
            if bool(load_settings().get("use_selections", True)) and self.has_selections():
                LEFT = {
                    "win_id": None, "view_id": None,
                    "clip": EasyDiffView("**selection**", self.get_selections(), self.get_encoding())
                }
                update_menu("**selection**")
            else:
                LEFT = {"win_id": self.view.window().id(), "view_id": self.view.id(), "clip": None}
                name = self.view.file_name()
                if name is None:
                    name = "Untitled"
                update_menu(basename(name))

    def set_view(self, paths, group=-1, index=-1, open_file=True):
        """Set view."""

        self.view = None
        if len(paths):
            file_path = get_target(paths)
            if file_path is None:
                return
            if open_file:
                self.view = self.window.open_file(file_path)
            else:
                self.view = self.window.find_open_file(file_path)
        elif index != -1:
            self.view = get_group_view(self.window, group, index)
        else:
            self.view = self.window.active_view()

    def is_enabled(self, external=False, paths=[], group=-1, index=-1):
        """Check if command is enabled."""

        return get_target(paths, group, index) is not None if len(paths) or index != -1 else True

    def description(self, external=False, paths=[], group=-1, index=-1, open_file=True):
        """Return menu description."""

        self.set_view(paths, group, index, False)
        if self.view is not None and self.has_selections():
            description = "%sDiff Set Left Side (Selections)" % ('' if external else 'Easy')
        else:
            description = "%sDiff Set Left Side" % ('' if external else 'Easy')
        return description


class EasyDiffCompareBothCommand(sublime_plugin.WindowCommand, _EasyDiffSelection):
    """Compare window command."""

    def run(self, external=False, clipboard=False, paths=[], group=-1, index=-1):
        """run command."""

        self.external = external
        self.clipboard = clipboard
        self.set_view(paths, group, index)
        if self.view is not None:
            self.diff()

    def diff(self):
        """Diff."""

        diff(self.get_left(), self.get_right(), external=self.external)

    def get_left(self):
        """Get left."""

        if self.clipboard:
            left = {
                "win_id": None, "view_id": None,
                "clip": EasyDiffView("**clipboard**", sublime.get_clipboard(), "UTF-8")
            }
        else:
            left = LEFT
        return left

    def get_right(self):
        """Get right."""
        if self.has_selections():
            right = {
                "win_id": None, "view_id": None,
                "clip": EasyDiffView("**selection**", self.get_selections(), self.get_encoding())
            }
        else:
            right = {"win_id": self.view.window().id(), "view_id": self.view.id(), "clip": None}
        return right

    def set_view(self, paths, group=-1, index=-1, open_file=True):
        """Set view."""

        self.view = None
        if len(paths):
            file_path = get_target(paths)
            if file_path is None:
                return
            if open_file:
                self.view = self.window.open_file(file_path)
            else:
                self.view = self.window.find_open_file(file_path)
        elif index != -1:
            self.view = get_group_view(self.window, group, index)
        else:
            self.view = self.window.active_view()

    def is_enabled(self, clipboard=False, external=False, paths=[], group=-1, index=-1):
        """Check if command is enabled."""

        if clipboard:
            enabled = (
                bool(load_settings().get("use_clipboard", True)) and
                (get_target(paths, group, index) is not None if len(paths) or index != -1 else True)
            )
        else:
            enabled = (
                LEFT is not None and
                (get_target(paths, group, index) is not None if len(paths) or index != -1 else True)
            )
        return enabled

    def get_left_name(self):
        """Get left name."""

        name = '...'
        if LEFT is not None:
            left = LEFT.get("clip")
            name = None
            if left is not None:
                name = left.file_name()
            else:
                win_id = LEFT.get("win_id")
                view_id = LEFT.get("view_id")
                window = None
                view = None
                for w in sublime.windows():
                    if w.id() == win_id:
                        window = w
                if window is not None:
                    for v in window.views():
                        if v.id() == view_id:
                            view = v
                if view is not None:
                    name = view.file_name()
                    if name is None:
                        name = "Untitled"
                    else:
                        name = basename(name)
        return name

    def description(self, external=False, clipboard=False, paths=[], group=-1, index=-1, open_file=True):
        """Return menu description."""

        self.set_view(paths, group, index, False)
        if clipboard:
            if self.view is not None and self.has_selections():
                description = "%sDiff Compare Selections with Clipboard" % ('' if external else 'Easy')
            else:
                description = "%sDiff Compare with Clipboard" % ('' if external else 'Easy')
        elif self.view is not None and self.has_selections():
            description = "%sDiff Compare Selections with \"%s\"" % (
                '' if external else 'Easy',
                self.get_left_name()
            )
        else:
            description = "%sDiff Compare with \"%s\"" % (
                '' if external else 'Easy',
                self.get_left_name()
            )
        return description


###############################
# MRU Tab Command
###############################
class EasyDiffMruPanelCompareCommand(sublime_plugin.WindowCommand):
    """Most recently used panel compare command."""

    def run(self, method="view", external=False):
        """Run command."""

        if method == "view":
            self.window.run_command(
                "easy_diff_set_left",
                {"group": EasyDiffListener.last[0], "index": EasyDiffListener.last[1]}
            )
            self.window.run_command(
                "easy_diff_compare_both_view",
                {"external": external}
            )
        elif method == "selection":
            self.window.run_command(
                "easy_diff_set_left_selection",
                {"group": EasyDiffListener.last[0], "index": EasyDiffListener.last[1]}
            )
            self.window.run_command(
                "easy_diff_compare_both_selection",
                {"external": external}
            )
        elif method == "clipboard":
            self.window.run_command(
                "easy_diff_set_left",
                {"group": EasyDiffListener.current[0], "index": EasyDiffListener.current[1]}
            )
            self.window.run_command(
                "easy_diff_compare_both_clipboard",
                {"external": external}
            )
        elif method == "clipboard_selection":
            self.window.run_command(
                "easy_diff_set_left_selection",
                {"group": EasyDiffListener.current[0], "index": EasyDiffListener.current[1]}
            )
            self.window.run_command(
                "easy_diff_compare_both_clipboard",
                {"external": external}
            )

    @staticmethod
    def enable_check(method="view", external=False):
        """Enable check."""

        allow = bool(load_settings().get("last_activated_commands", True))
        enabled = False
        if method == "view":
            enabled = (
                allow and
                bool(EasyDiffListener.current and EasyDiffListener.last)
            )
        elif method == "selection":
            enabled = (
                allow and
                bool(load_settings().get("use_selections", True)) and
                bool(EasyDiffListener.current and EasyDiffListener.last)
            )
        elif method == "clipboard":
            enabled = (
                allow and
                bool(load_settings().get("use_clipboard", True)) and
                bool(EasyDiffListener.last)
            )
        elif method == "clipboard_selection":
            enabled = (
                allow and
                bool(load_settings().get("use_clipboard", True)) and
                bool(load_settings().get("use_selections", True)) and
                bool(EasyDiffListener.last)
            )
        if external:
            enabled = (
                enabled and
                bool(load_settings().get("show_external", True)) and
                get_external_diff() is not None
            )
        else:
            enabled = (
                enabled and
                bool(load_settings().get("show_internal", True))
            )
        return enabled

    def is_enabled(self, method="view", external=False):
        """Check if command is enabled."""

        return self.enable_check(method, external)


###############################
# Quick Panel Diff
###############################
PANEL_ENTRIES = [
    {
        "caption": "Set Left Side",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_set_left"
        ),
        "condition": lambda self, external: bool(
            load_settings().get("quick_panel_left_right_commands", True)
        )
    },
    {
        "caption": "Compare with %(file)s ...",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_compare_both", {"external": external}
        ),
        "condition": lambda self, external: LEFT is not None and bool(
            load_settings().get("quick_panel_left_right_commands", True)
        )
    },
    # {
    #     "caption": "Compare Last Active with Current Tab",
    #     "cmd": lambda self, external: self.view.window().run_command(
    #         "easy_diff_mru_panel_compare", {"method": "view", "external": external}
    #     ),
    #     "condition": lambda self, external: EasyDiffMruPanelCompareCommand.enable_check(
    #         method="view", external=external
    #     )
    # },
    # {
    #     "caption": "Compare Last Active with Current Tab Selection(s)",
    #     "cmd": lambda self, external: self.view.window().run_command(
    #         "easy_diff_mru_panel_compare", {"method": "selection", "external": external}
    #     ),
    #     "condition": lambda self, external: EasyDiffMruPanelCompareCommand.enable_check(
    #         method="selection", external=external
    #     )
    # },
    # {
    #     "caption": "Compare Current Tab with Clipboard",
    #     "cmd": lambda self, external: self.view.window().run_command(
    #         "easy_diff_mru_panel_compare", {"method": "clipboard", "external": external}
    #     ),
    #     "condition": lambda self, external: EasyDiffMruPanelCompareCommand.enable_check(
    #         method="clipboard", external=external
    #     )
    # },
    # {
    #     "caption": "Compare Current Tab Selection(s) with Clipboard",
    #     "cmd": lambda self, external: self.view.window().run_command(
    #         "easy_diff_mru_panel_compare", {"method": "clipboard_selection", "external": external}
    #     ),
    #     "condition": lambda self, external: EasyDiffMruPanelCompareCommand.enable_check(
    #         method="clipboard_selection", external=external
    #     )
    # },
    {
        "caption": "SVN Diff",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_svn", {"external": external}
        ),
        "condition": lambda self, external: not bool(load_settings().get("svn_disabled", False))
    },
    {
        "caption": "SVN Diff with Previous Revision",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_svn", {"external": external, "last": True}
        ),
        "condition": lambda self, external: not bool(load_settings().get("svn_disabled", False))
    },
    {
        "caption": "SVN Revert",
        "cmd": lambda self, external: self.view.run_command(
            "easy_diff_svn", {"revert": True}
        ),
        "condition": lambda self, external: not bool(load_settings().get("svn_disabled", False))
    },
    {
        "caption": "GIT Diff",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_git", {"external": external}
        ),
        "condition": lambda self, external: not bool(load_settings().get("git_disabled", False))
    },
    {
        "caption": "GIT Diff with Previous Revision",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_git", {"external": external, "last": True}
        ),
        "condition": lambda self, external: not bool(load_settings().get("git_disabled", False))
    },
    {
        "caption": "GIT Revert",
        "cmd": lambda self, external: self.view.run_command(
            "easy_diff_git", {"revert": True}
        ),
        "condition": lambda self, external: not bool(load_settings().get("git_disabled", False))
    },
    {
        "caption": "Mercurial Diff",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_hg", {"external": external}
        ),
        "condition": lambda self, external: not bool(load_settings().get("hg_disabled", False))
    },
    {
        "caption": "Mercurial Diff with Previous Revision",
        "cmd": lambda self, external: self.view.window().run_command(
            "easy_diff_hg", {"external": external, "last": True}
        ),
        "condition": lambda self, external: not bool(load_settings().get("hg_disabled", False))
    },
    {
        "caption": "Mercurial Revert",
        "cmd": lambda self, external: self.view.run_command(
            "easy_diff_hg", {"revert": True}
        ),
        "condition": lambda self, external: not bool(load_settings().get("hg_disabled", False))
    },
]


class EasyDiffPanelCommand(sublime_plugin.TextCommand):
    """Diff panel command."""

    def run(self, edit, external=False):
        """Run command."""

        self.external = external
        self.menu_options = []
        self.menu_callback = []
        if (
            (not external and bool(load_settings().get("show_internal", True))) or
            (external and bool(load_settings().get("show_external", True)))
        ):
            left_name = self.get_left_name()
            for entry in PANEL_ENTRIES:
                if entry["condition"](self, external):
                    self.menu_options.append(entry["caption"] % {"file": left_name})
                    self.menu_callback.append(entry["cmd"])
        if len(self.menu_options) > 1:
            self.view.window().show_quick_panel(self.menu_options, self.check_selection)
        elif len(self.menu_options) == 1:
            self.check_selection(0)

    def get_left_name(self):
        """Get left name."""

        name = None
        if LEFT is not None:
            left = LEFT.get("clip")
            name = None
            if left is not None:
                name = left.file_name()
            else:
                win_id = LEFT.get("win_id")
                view_id = LEFT.get("view_id")
                window = None
                view = None
                for w in sublime.windows():
                    if w.id() == win_id:
                        window = w
                if window is not None:
                    for v in window.views():
                        if v.id() == view_id:
                            view = v
                if view is not None:
                    name = view.file_name()
                    if name is None:
                        name = "Untitled"
                    else:
                        name = basename(name)
        return name

    def check_selection(self, value):
        """Check user's selection."""

        if value != -1:
            callback = self.menu_callback[value]
            sublime.set_timeout(lambda: callback(self, self.external), 0)

    def is_enabled(self, external=False):
        """Check if command is enabled."""

        return (
            (not external and bool(load_settings().get("show_internal", True))) or
            (external and bool(load_settings().get("show_external", True)))
        ) and bool(load_settings().get("quick_panel_commands", True))


class EasyDiffPanelSetLeftCommand(sublime_plugin.TextCommand):
    """Panel set left command."""

    def run(self, edit, external):
        """Run command."""

        self.menu_options = ["View"]
        if bool(load_settings().get("use_selections", True)):
            self.menu_options.append("Selection(s)")
        if bool(load_settings().get("use_clipboard", True)):
            self.menu_options.append("Clipboard")
        if len(self.menu_options) > 1:
            self.view.window().show_quick_panel(self.menu_options, self.check_selection)
        else:
            self.check_selection(0)

    def check_selection(self, value):
        """Check user's selection."""

        if value != -1:
            option = self.menu_options[value]
            if option == "View":
                self.view.window().run_command("easy_diff_set_left")
            elif option == "Selection(s)":
                self.view.window().run_command("easy_diff_set_left_selection")
            elif option == "Clipboard":
                self.view.window().run_command("easy_diff_set_left_clipboard")

    def is_enabled(self, external):
        """Check if command is enabled."""

        enabled = False
        if not external and bool(load_settings().get("show_internal", True)):
            enabled = True
        elif external and bool(load_settings().get("show_external", True)):
            enabled = True
        return enabled


class EasyDiffPanelCompareCommand(sublime_plugin.TextCommand):
    """Manage panel compare commands."""

    def run(self, edit, external):
        """Run command."""

        self.external = external
        self.menu_options = ["View"]
        if bool(load_settings().get("use_selections", True)):
            self.menu_options.append("Selection(s)")
        if bool(load_settings().get("use_clipboard", True)):
            self.menu_options.append("Clipboard")
        if len(self.menu_options) > 1:
            self.view.window().show_quick_panel(self.menu_options, self.check_selection)
        else:
            self.check_selection(0)

    def check_selection(self, value):
        """Check user's selection."""

        if value != -1:
            option = self.menu_options[value]
            if option == "View":
                self.view.window().run_command("easy_diff_compare_both_view", {"external": self.external})
            elif option == "Selection(s)":
                self.view.window().run_command("easy_diff_compare_both_selection", {"external": self.external})
            elif option == "Clipboard":
                self.view.window().run_command("easy_diff_compare_both_clipboard", {"external": self.external})

    def is_enabled(self, external):
        """Check if command is enabled."""

        enabled = False
        if not external and bool(load_settings().get("show_internal", True)):
            enabled = True
        elif external and bool(load_settings().get("show_external", True)):
            enabled = True
        return LEFT is not None and enabled


###############################
# View Close Listener
###############################
class EasyDiffListener(sublime_plugin.EventListener):
    """Listener for EasyDiff."""

    current = None
    last = None

    def on_close(self, view):
        """Update menu on view close."""

        global LEFT
        vid = view.id()
        if LEFT is not None and vid == LEFT["view_id"]:
            LEFT = None
            update_menu()

    def on_activated(self, view):
        """Track last activated view."""

        cls = EasyDiffListener
        window = view.window()
        if window is not None:
            sheet = window.active_sheet()
            group, index = window.get_sheet_index(sheet)
            if group != -1:
                if (group, index) != cls.current:
                    cls.last = cls.current
                    cls.current = (group, index)


###############################
# Loaders
###############################
def basic_reload():
    """Reload on settings change."""

    global LEFT
    LEFT = None
    update_menu()
    settings = load_settings()
    settings.clear_on_change('reload_basic')
    settings.add_on_change('reload_basic', basic_reload)


def plugin_loaded():
    """Plugin reload."""

    basic_reload()
