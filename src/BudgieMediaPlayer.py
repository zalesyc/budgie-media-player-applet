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

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("Budgie", "1.0")
from gi.repository import Gtk, Gio, GLib, Budgie

from SingleAppPlayer import SingleAppPlayer
from SettingsPage import SettingsPage


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
        self.popover_manager: Budgie.PopoverManager = Budgie.PopoverManager()
        self.popover_manager.register_popover(self, self.popover)

        self.popover_box: Gtk.Box = Gtk.Box.new(
            Gtk.Orientation(not self.orientation), 10
        )
        self.popover_box.set_margin_bottom(5)
        self.popover_box.set_margin_top(5)
        self.popover_box.set_margin_start(5)
        self.popover_box.set_margin_end(5)
        self.popover.add(self.popover_box)

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

        self.players_list: list[SingleAppPlayer] = []
        for dbus_name in dbus_names:
            self.players_list.append(
                SingleAppPlayer(
                    service_name=dbus_name,
                    orientation=self.orientation,
                    author_max_len=self.author_max_len,
                    name_max_len=self.name_max_len,
                    element_order=self.element_order,
                    separator_text=self.separator_text,
                )
            )
            if len(self.players_list) < 2:
                self.box.pack_start(self.players_list[-1], False, False, 0)
            else:
                self.popover_box.add(self.players_list[-1])

        self.popover.get_child().show_all()
        self.show_all()

        if len(self.players_list) < 2:
            self.popup_icon.hide()

    def show_popup(self, *args) -> None:
        self.popover_manager.show_popover(self)

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

    def dbus_players_changed(self, a, b, c, d, e, changes: GLib.Variant) -> None:
        # args a-e are arguments i dont need, but get sent by gtk
        if (changes[0] not in self.players_list) and changes[2]:  # player was added
            self.players_list.append(
                SingleAppPlayer(
                    service_name=changes[0],
                    orientation=self.orientation,
                    author_max_len=self.author_max_len,
                    name_max_len=self.name_max_len,
                    element_order=self.element_order,
                    separator_text=self.separator_text,
                ),
            )
            if len(self.players_list) < 2:
                self.box.pack_start(self.players_list[-1], False, False, 0)
                self.players_list[-1].set_album_cover_size(self.album_cover_size)

            else:
                self.popover_box.add(self.players_list[-1])
                self.popup_icon.show()

        elif not changes[2]:  # player was removed
            for index, player in enumerate(self.players_list):
                if player.service_name == changes[0]:
                    if index == 0:
                        self.box.remove(player)
                        del self.players_list[index]

                        if len(self.players_list) > 0:
                            self.popover_box.remove(self.players_list[0])
                            self.box.pack_start(self.players_list[0], False, False, 0)
                            self.players_list[0].set_album_cover_size(
                                self.album_cover_size
                            )

                    else:
                        self.popover_box.remove(player)
                        del self.players_list[index]

            if len(self.players_list) < 2:
                self.popup_icon.hide()

    def settings_changed(self, settings, changed_key_name: str) -> None:
        if changed_key_name == "author-name-max-length":
            self.author_max_len = self.settings.get_int(changed_key_name)
            for app_player in self.players_list:
                app_player.author_max_len = self.author_max_len
                app_player.reset_song_label()
            return

        if changed_key_name == "media-title-max-length":
            self.name_max_len = self.settings.get_int(changed_key_name)
            for app_player in self.players_list:
                app_player.name_max_len = self.name_max_len
                app_player.reset_song_label()
            return

        if changed_key_name == "element-order":
            self.element_order = self.settings.get_strv(changed_key_name)
            for app_player in self.players_list:
                app_player.set_element_order(self.element_order)
            return

        if changed_key_name == "separator-text":
            self.separator_text = self.settings.get_string("separator-text")
            for app_player in self.players_list:
                app_player.set_separator_text(self.separator_text)

    def do_panel_size_changed(
        self, panel_size: int, icon_size: int, small_icon_size: int
    ) -> None:
        if len(self.players_list) > 0:
            self.players_list[0].set_album_cover_size(icon_size)

    def do_panel_position_changed(self, position: Budgie.PanelPosition) -> None:
        if position in {Budgie.PanelPosition.LEFT, Budgie.PanelPosition.RIGHT}:
            self.orientation = Gtk.Orientation.VERTICAL
        else:
            self.orientation = Gtk.Orientation.HORIZONTAL

        self.box.set_orientation(self.orientation)
        self.popover_box.set_orientation(Gtk.Orientation(not self.orientation))
        for player in self.players_list:
            player.set_orientation(self.orientation)

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return SettingsPage(self.settings)

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise."""
        return True
