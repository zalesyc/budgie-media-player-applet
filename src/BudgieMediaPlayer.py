#    budgie-media-player-applet
#    Copyright (C) 2023 Alex Cizinsky
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("Budgie", "1.0")
from gi.repository import Gtk, Gio, GLib, Budgie

# from PanelControlView import PanelControlView
from SettingsPage import SettingsPage

# from SingleAppPlayer import SingleAppPlayer
from PopupPlasmaControlView import PopupPlasmaControlView


class BudgieMediaPlayer(Budgie.Applet):
    def __init__(self, uuid: str):
        Budgie.Applet.__init__(self)
        self.uuid: str = uuid

        self.default_album_cover_size = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.album_cover_size = self.default_album_cover_size
        self.orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL

        self.set_settings_prefix("/com/github/zalesyc/budgie-media-player-applet")
        self.set_settings_schema("com.github.zalesyc.budgie-media-player-applet")
        self.settings: Gio.Settings = self.get_applet_settings(self.uuid)
        self.settings.connect("changed", self.settings_changed)

        self.author_max_len: int = self.settings.get_int("author-name-max-length")
        self.name_max_len: int = self.settings.get_int("media-title-max-length")
        self.element_order: list[str] = self.settings.get_strv("element-order")
        self.separator_text: str = self.settings.get_string("separator-text")

        self.box: Gtk.Box = Gtk.Box(spacing=10)
        self.add(self.box)

        self.popup_icon: Gtk.Image = Gtk.Image.new_from_icon_name(
            "arrow-down", Gtk.IconSize.MENU
        )
        self.popup_icon_event_box: Gtk.EventBox = Gtk.EventBox()
        self.popup_icon_event_box.add(self.popup_icon)
        self.popup_icon_event_box.connect("button-press-event", self.show_popup)
        self.box.pack_end(self.popup_icon_event_box, False, False, 0)

        self.popover: Budgie.Popover = Budgie.Popover.new(self)
        self.popover.connect("closed", self.on_popover_close)
        self.popover_manager: Budgie.PopoverManager = Budgie.PopoverManager()
        self.popover_manager.register_popover(self, self.popover)

        self.dbus_namespace_name: str = "org.mpris.MediaPlayer2"
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

        self.players_list: list[PopupPlasmaControlView] = []
        # index in players_list of the player that has the panel view
        self.panel_player_index: Optional[int] = 0
        self.popover_ntb: Optional[Gtk.Notebook] = None
        self.popover_ntb = Gtk.Notebook.new()
        self.popover_ntb.set_margin_bottom(5)
        self.popover_ntb.set_margin_start(5)
        self.popover_ntb.set_margin_end(5)
        self.popover_ntb.set_show_border(False)
        self.popover_ntb.set_scrollable(True)
        self.popover.add(self.popover_ntb)

        for index, dbus_name in enumerate(dbus_names):
            self.players_list.append(
                PopupPlasmaControlView(
                    service_name=dbus_name,
                    orientation=self.orientation,
                    author_max_len=self.author_max_len,
                    name_max_len=self.name_max_len,
                    separator_text=self.separator_text,
                    open_popover_func=self.show_popup,
                )
            )
            if len(self.players_list) < 2:
                self.players_list[-1].add_panel_view(
                    self.author_max_len,
                    self.name_max_len,
                    self.separator_text,
                    self.element_order,
                )
                self.box.pack_start(self.players_list[-1].panel_view, False, False, 0)
                self.panel_player_index = index

            self.popover_ntb.append_page(
                self.players_list[-1],
                self.players_list[-1].get_icon(Gtk.IconSize.MENU),
            )

        self.popover.get_child().show_all()
        self.show_all()

        if not self.settings.get_boolean("show-arrow"):
            self.popup_icon.hide()

    def show_popup(self, *_) -> None:
        self.popover_manager.show_popover(self)
        for player in self.players_list:
            player.popover_to_be_open()

    def on_popover_close(self, _):
        for player in self.players_list:
            player.popover_just_closed()

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
        return [x for x in names[0] if x.startswith(self.dbus_namespace_name)]

    def dbus_players_changed(
        self, _, __, ___, ____, _____, changes: GLib.Variant
    ) -> None:
        if (changes[0] not in self.players_list) and changes[2]:  # player was added
            self.players_list.append(
                PopupPlasmaControlView(
                    service_name=changes[0],
                    orientation=self.orientation,
                    author_max_len=self.author_max_len,
                    name_max_len=self.name_max_len,
                    separator_text=self.separator_text,
                    open_popover_func=self.show_popup,
                ),
            )
            self.popover_ntb.append_page(
                self.players_list[-1],
                self.players_list[-1].get_icon(Gtk.IconSize.MENU),
            )
            self.popover_ntb.show_all()

            if len(self.players_list) <= 1:
                self.panel_player_index = 0
                self.players_list[-1].add_panel_view(
                    self.author_max_len,
                    self.name_max_len,
                    self.separator_text,
                    self.element_order,
                )
                self.box.pack_start(self.players_list[-1].panel_view, False, False, 0)

        elif not changes[2]:  # player was removed
            for index, player in enumerate(self.players_list):
                if player.service_name == changes[0]:
                    if self.panel_player_index == index:
                        self.box.remove(player.panel_view)
                        if len(self.players_list) > 1:
                            self.panel_player_index = 1
                            self.players_list[1].add_panel_view(
                                self.author_max_len,
                                self.name_max_len,
                                self.separator_text,
                                self.element_order,
                            )
                            self.box.pack_start(
                                self.players_list[1].panel_view, False, False, 0
                            )
                        else:
                            self.panel_player_index = None

                    self.popover_ntb.remove(player)
                    del self.players_list[index]
                    break

    def settings_changed(self, _, changed_key_name: str) -> None:
        if changed_key_name == "author-name-max-length":
            self.author_max_len = self.settings.get_int(changed_key_name)
            if len(self.players_list) > self.panel_player_index:
                if self.players_list[self.panel_player_index].panel_view is not None:
                    self.players_list[self.panel_player_index].set_author_max_len(
                        self.author_max_len
                    )
            return

        if changed_key_name == "media-title-max-length":
            self.name_max_len = self.settings.get_int(changed_key_name)
            if len(self.players_list) > self.panel_player_index:
                if self.players_list[self.panel_player_index].panel_view is not None:
                    self.players_list[self.panel_player_index].set_title_max_len(
                        self.name_max_len
                    )

        if changed_key_name == "element-order":
            self.element_order = self.settings.get_strv(changed_key_name)
            if len(self.players_list) > self.panel_player_index:
                if self.players_list[self.panel_player_index].panel_view is not None:
                    self.players_list[self.panel_player_index].set_element_order(
                        self.element_order
                    )
            return

        if changed_key_name == "separator-text":
            self.separator_text = self.settings.get_string("separator-text")
            if len(self.players_list) > self.panel_player_index:
                if self.players_list[self.panel_player_index].panel_view is not None:
                    self.players_list[self.panel_player_index].set_separator_text(
                        self.separator_text
                    )
            return

        if changed_key_name == "show-arrow":
            if self.settings.get_boolean("show-arrow"):
                self.popup_icon.show()
            else:
                self.popup_icon.hide()

    def do_panel_size_changed(
        self, panel_size: int, icon_size: int, small_icon_size: int
    ) -> None:
        if len(self.players_list) > self.panel_player_index:
            self.players_list[self.panel_player_index].panel_size_changed(icon_size)

    def do_panel_position_changed(self, position: Budgie.PanelPosition) -> None:
        if position in {Budgie.PanelPosition.LEFT, Budgie.PanelPosition.RIGHT}:
            self.orientation = Gtk.Orientation.VERTICAL
        else:
            self.orientation = Gtk.Orientation.HORIZONTAL

        self.box.set_orientation(self.orientation)
        if len(self.players_list) > self.panel_player_index:
            self.players_list[self.panel_player_index].panel_orientation_changed(
                self.orientation
            )

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return SettingsPage(self.settings)

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise."""
        return True
