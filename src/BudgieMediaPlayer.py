# Copyright 2023 - 2025, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass
from typing import Optional, Callable
import gi
from SettingsPage import SettingsPage
from PopupPlasmaControlView import PopupPlasmaControlView
from EnumsStructs import PanelLengthMode
from FixedSizeBin import FixedSizeBin
from Popover import Popover

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Budgie", "1.0")
from gi.repository import Gtk, Gio, GLib, Budgie


class NothingPlayingLabel(Gtk.EventBox):
    def __init__(
        self,
        settings: Gio.Settings,
        open_popover_func: Callable[[], None],
        orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.settings = settings
        self._box = Gtk.Box(spacing=5)
        self._image: Gtk.Image = Gtk.Image.new_from_icon_name(
            "emblem-music-symbolic", Gtk.IconSize.MENU
        )
        self._label = Gtk.Label.new(
            self.settings.get_string("panel-nothing-playing-text")
        )
        self._box.pack_start(self._image, False, False, 0)
        self._box.pack_start(self._label, False, False, 0)
        self.set_orientation(orientation)
        self.add(self._box)
        self.connect("button-press-event", lambda *args: open_popover_func())
        self.show_all()

    def set_orientation(self, orientation: Gtk.Orientation) -> None:
        if orientation == Gtk.Orientation.HORIZONTAL:
            self._label.set_angle(0)
            self.set_valign(Gtk.Align.CENTER)
            self.set_halign(Gtk.Align.FILL)
        else:
            self._label.set_angle(270)
            self.set_halign(Gtk.Align.CENTER)
            self.set_valign(Gtk.Align.FILL)
        self._box.set_orientation(orientation)

    def text_changed(self) -> None:
        self._label.set_text(self.settings.get_string("panel-nothing-playing-text"))


@dataclass
class PanelPlayer:
    """If service_name is None, there may be nothing_playing_label"""

    service_name: Optional[str] = None
    nothing_playing_label: Optional[NothingPlayingLabel] = None


class BudgieMediaPlayer(Budgie.Applet):
    DBUS_NAMESPACE_NAME: str = "org.mpris.MediaPlayer2"

    def __init__(self, uuid: str):
        Budgie.Applet.__init__(self)
        self.uuid: str = uuid

        self.panel_size = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL

        self.set_settings_prefix("/com/github/zalesyc/budgie-media-player-applet")
        self.set_settings_schema("com.github.zalesyc.budgie-media-player-applet")
        self.settings: Gio.Settings = self.get_applet_settings(self.uuid)
        self.settings.connect("changed", self.settings_changed)

        self.box: Gtk.Box = Gtk.Box(spacing=10)
        self.add(self.box)

        self.panel_view_size_bin: FixedSizeBin = FixedSizeBin(
            size=(
                self.settings.get_uint("panel-length-fixed")
                if self.settings.get_uint("panel-length-mode") == PanelLengthMode.Fixed
                else None
            ),
            orientation=self.orientation,
        )
        self.box.pack_start(self.panel_view_size_bin, False, False, 0)

        self.popup_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
            "budgie-media-player-applet-arrow-drop-down-symbolic", Gtk.IconSize.MENU
        )
        self.popup_icon.set_tooltip_text("Open the popup")
        self.popup_icon_event_box: Gtk.EventBox = Gtk.EventBox()
        self.popup_icon_event_box.add(self.popup_icon)
        self.popup_icon_event_box.connect("button-press-event", self.show_popup)
        self.box.pack_end(self.popup_icon_event_box, False, False, 0)

        self.popover: Popover = Popover(relative_to=self, settings=self.settings)
        self.popover_manager: Optional[Budgie.PopoverManager] = None

        self.session_bus: Gio.DBusConnection = Gio.bus_get_sync(
            Gio.BusType.SESSION, None
        )
        self.session_bus.signal_subscribe(
            None,  # Sender
            None,  # Interface
            "NameOwnerChanged",  # Member
            None,  # Object path
            "org.mpris.MediaPlayer2",  # Arg0 (sender name)
            Gio.DBusSignalFlags.MATCH_ARG0_NAMESPACE,  # Flags
            self.dbus_players_changed,  # Callback function
        )
        dbus_names = self.list_dbus_players()

        self.players_list: dict[str, PopupPlasmaControlView] = {}
        # service name of the player that has the panel view
        self.panel_player: PanelPlayer = PanelPlayer()

        if dbus_names:
            for dbus_service_name in dbus_names:
                self._add_popup_plasma_control_view(dbus_service_name)
        else:
            self._add_nothing_playing_label()

        self.show_all()

        if not self.settings.get_boolean("show-arrow"):
            self.popup_icon.hide()

    def show_popup(self, *_) -> None:
        if self.popover_manager is not None:
            self.popover_manager.show_popover(self)

    def favorite_player_clicked(self, service_name: str) -> None:
        if len(self.players_list) <= 1:
            return

        if service_name == self.panel_player.service_name:
            for key, value in self.players_list.items():
                if key == service_name:
                    continue

                self.players_list[service_name].remove_panel_view()
                self._add_panel_view(value)
                return
            return

        self.players_list[self.panel_player.service_name].remove_panel_view()

        self._add_panel_view(self.players_list[service_name])

    def list_dbus_players(self) -> list[str]:
        names = self.session_bus.call_sync(
            "org.freedesktop.DBus",  # Destination name
            "/org/freedesktop/DBus",  # Object path
            "org.freedesktop.DBus",  # Interface name
            "ListNames",  # Method name
            None,  # Input parameters
            GLib.VariantType.new("(as)"),  # Output type (array of strings)
            Gio.DBusCallFlags.NONE,  # Flags
            -1,  # Timeout (default)
            None,  # Cancellable (none)
        )
        return [x for x in names[0] if x.startswith(self.DBUS_NAMESPACE_NAME)]

    def dbus_players_changed(
        self, _, __, ___, ____, _____, changes: GLib.Variant
    ) -> None:
        if (changes[0] not in self.players_list) and changes[2]:  # player was added
            if self.panel_player.nothing_playing_label is not None:
                self.panel_player.nothing_playing_label.destroy()
                self.panel_player.nothing_playing_label = None
            self._add_popup_plasma_control_view(changes[0])

        elif not changes[2]:  # player was removed
            player_to_get_del = self.players_list.pop(changes[0], None)
            if player_to_get_del is None:
                return

            had_panel_view = player_to_get_del.panel_view is not None
            player_to_get_del.destroy()

            if had_panel_view:
                if len(self.players_list) > 0:
                    for player in self.players_list.values():
                        self._add_panel_view(player)
                        break
                else:
                    self.panel_player.service_name = None
                    self._add_nothing_playing_label()

    def settings_changed(self, _, changed_key_name: str) -> None:
        if changed_key_name == "show-arrow":
            if self.settings.get_boolean("show-arrow"):
                self.popup_icon.show()
            else:
                self.popup_icon.hide()
            return

        if changed_key_name in {"panel-length-mode", "panel-length-fixed"}:
            if self.settings.get_uint("panel-length-mode") == PanelLengthMode.Fixed:
                self.panel_view_size_bin.set_size(
                    self.settings.get_uint("panel-length-fixed")
                )
            else:
                self.panel_view_size_bin.set_size(None)
            return

        if changed_key_name == "panel-show-nothing-playing":
            if self.settings.get_boolean("panel-show-nothing-playing"):
                self._add_nothing_playing_label()
            elif self.panel_player.nothing_playing_label is not None:
                self.panel_player.nothing_playing_label.destroy()
                self.panel_player.nothing_playing_label = None
            return
        if changed_key_name == "panel-nothing-playing-text":
            if self.panel_player.nothing_playing_label is not None:
                self.panel_player.nothing_playing_label.text_changed()

    def _add_panel_view(self, player: PopupPlasmaControlView) -> None:
        player.add_panel_view(
            orientation=self.orientation,
            panel_size=self.panel_size,
        )
        self.panel_view_size_bin.add(player.panel_view)
        self.panel_player.service_name = player.service_name

    def _add_popup_plasma_control_view(self, service_name: str) -> None:
        new_view = PopupPlasmaControlView(
            service_name=service_name,
            open_popover_func=self.show_popup,
            on_pin_clicked=self.favorite_player_clicked,
            settings=self.settings,
        )

        self.popover.add_player(new_view)

        if len(self.players_list) < 1:
            self._add_panel_view(new_view)

        self.players_list.update({new_view.service_name: new_view})

    def _add_nothing_playing_label(self) -> None:
        if not self.settings.get_boolean("panel-show-nothing-playing"):
            return
        if self.panel_player.service_name is not None:
            return
        if self.panel_player.nothing_playing_label is not None:
            return

        self.panel_player.nothing_playing_label = NothingPlayingLabel(
            self.settings,
            open_popover_func=self.show_popup,
            orientation=self.orientation,
        )
        self.panel_view_size_bin.add(self.panel_player.nothing_playing_label)

    def do_panel_size_changed(
        self, panel_size: int, icon_size: int, small_icon_size: int
    ) -> None:
        self.panel_size = icon_size
        if (
            player := self.players_list.get(self.panel_player.service_name, None)
        ) is not None:
            player.panel_size_changed(self.panel_size)

    def do_panel_position_changed(self, position: Budgie.PanelPosition) -> None:
        if position in {Budgie.PanelPosition.LEFT, Budgie.PanelPosition.RIGHT}:
            self.orientation = Gtk.Orientation.VERTICAL
        else:
            self.orientation = Gtk.Orientation.HORIZONTAL

        self.box.set_orientation(self.orientation)
        if (
            player := self.players_list.get(self.panel_player.service_name, None)
        ) is not None:
            player.panel_orientation_changed(self.orientation)

        if self.panel_player.nothing_playing_label is not None:
            self.panel_player.nothing_playing_label.set_orientation(self.orientation)

        self.panel_view_size_bin.set_orientation(self.orientation)

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return SettingsPage(self.settings)

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise."""
        return True

    def do_update_popovers(self, manager: Budgie.PopoverManager) -> None:
        self.popover_manager = manager
        self.popover_manager.register_popover(self, self.popover)
