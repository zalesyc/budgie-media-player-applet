# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional
import gi
from SettingsPage import SettingsPage
from PopupPlasmaControlView import PopupPlasmaControlView

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("Budgie", "1.0")
from gi.repository import Gtk, Gio, GLib, Budgie


class BudgieMediaPlayer(Budgie.Applet):
    DBUS_NAMESPACE_NAME: str = "org.mpris.MediaPlayer2"

    def __init__(self, uuid: str):
        Budgie.Applet.__init__(self)
        self.uuid: str = uuid

        self.album_cover_size = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL

        self.set_settings_prefix("/com/github/zalesyc/budgie-media-player-applet")
        self.set_settings_schema("com.github.zalesyc.budgie-media-player-applet")
        self.settings: Gio.Settings = self.get_applet_settings(self.uuid)
        self.settings.connect("changed", self.settings_changed)

        self.box: Gtk.Box = Gtk.Box(spacing=10)
        self.add(self.box)

        self.popup_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
            "budgie-media-player-applet-arrow-drop-down-symbolic", Gtk.IconSize.MENU
        )
        self.popup_icon.set_tooltip_text("Open the popup")
        self.popup_icon_event_box: Gtk.EventBox = Gtk.EventBox()
        self.popup_icon_event_box.add(self.popup_icon)
        self.popup_icon_event_box.connect("button-press-event", self.show_popup)
        self.box.pack_end(self.popup_icon_event_box, False, False, 0)

        self.popover: Budgie.Popover = Budgie.Popover.new(self)
        self.popover.set_size_request(
            width=self.settings.get_uint("popover-width"),
            height=self.settings.get_uint("popover-height"),
        )
        self.popover.connect("closed", self.on_popover_close)
        self.popover_manager: Budgie.PopoverManager = Budgie.PopoverManager()
        self.popover_manager.register_popover(self, self.popover)

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
        self.panel_player_service_name: Optional[str] = None
        self.popover_ntb: Gtk.Notebook = Gtk.Notebook(
            margin_start=5,
            margin_end=5,
            margin_bottom=5,
            show_border=False,
            scrollable=True,
        )
        self.popover.add(self.popover_ntb)

        for dbus_service_name in dbus_names:
            self._add_popup_plasma_control_view(dbus_service_name)

        self.show_all()

        if not self.settings.get_boolean("show-arrow"):
            self.popup_icon.hide()

    def show_popup(self, *_) -> None:
        self.popover_manager.show_popover(self)
        for player in self.players_list.values():
            player.popover_to_be_open()

    def on_popover_close(self, _) -> None:
        for player in self.players_list.values():
            player.popover_just_closed()

    def favorite_player_clicked(self, service_name: str) -> None:
        if len(self.players_list) <= 1:
            return

        if service_name == self.panel_player_service_name:
            for key, value in self.players_list.items():
                if key == service_name:
                    continue

                self.players_list[service_name].remove_panel_view()
                self._add_panel_view(value)
                return
            return

        self.players_list[self.panel_player_service_name].remove_panel_view()

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
            self._add_popup_plasma_control_view(changes[0])

        elif not changes[2]:  # player was removed
            player_to_get_del = self.players_list.pop(changes[0], None)
            if player_to_get_del is None:
                return

            self.popover_ntb.remove(player_to_get_del)

            if player_to_get_del.panel_view is None:
                return

            player_to_get_del.remove_panel_view()

            if len(self.players_list) > 0:
                for player in self.players_list.values():
                    self._add_panel_view(player)
                    break
            else:
                self.panel_player_service_name = None

    def settings_changed(self, _, changed_key_name: str) -> None:
        if changed_key_name == "show-arrow":
            if self.settings.get_boolean("show-arrow"):
                self.popup_icon.show()
            else:
                self.popup_icon.hide()
            return

        if changed_key_name in {"popover-width", "popover-height"}:
            self.popover.set_size_request(
                width=self.settings.get_uint("popover-width"),
                height=self.settings.get_uint("popover-height"),
            )
            return

    def _add_panel_view(self, player: PopupPlasmaControlView) -> None:
        player.add_panel_view(
            orientation=self.orientation,
        )
        self.box.pack_start(player.panel_view, False, False, 0)
        self.panel_player_service_name = player.service_name

    def _add_popup_plasma_control_view(self, service_name: str) -> None:
        new_view = PopupPlasmaControlView(
            service_name=service_name,
            open_popover_func=self.show_popup,
            on_pin_clicked=self.favorite_player_clicked,
            settings=self.settings,
        )

        self.popover_ntb.append_page(new_view, new_view.icon)
        self.popover_ntb.show_all()

        if len(self.players_list) < 1:
            self._add_panel_view(new_view)

        self.players_list.update({new_view.service_name: new_view})

    def do_panel_size_changed(
        self, panel_size: int, icon_size: int, small_icon_size: int
    ) -> None:
        if (
            player := self.players_list.get(self.panel_player_service_name, None)
        ) is not None:
            player.panel_size_changed(icon_size)

    def do_panel_position_changed(self, position: Budgie.PanelPosition) -> None:
        if position in {Budgie.PanelPosition.LEFT, Budgie.PanelPosition.RIGHT}:
            self.orientation = Gtk.Orientation.VERTICAL
        else:
            self.orientation = Gtk.Orientation.HORIZONTAL

        self.box.set_orientation(self.orientation)
        if (
            player := self.players_list.get(self.panel_player_service_name, None)
        ) is not None:
            player.panel_orientation_changed(self.orientation)

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return SettingsPage(self.settings)

    @staticmethod
    def do_supports_settings():
        """Return True if support setting through Budgie Setting,
        False otherwise."""
        return True
