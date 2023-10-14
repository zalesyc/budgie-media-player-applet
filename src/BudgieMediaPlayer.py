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


class BudgieMediaPlayer(Budgie.Applet):
    def __init__(self, uuid):
        Budgie.Applet.__init__(self)
        self.box = Gtk.Box(spacing=10)
        self.add(self.box)

        self.popup_icon = Gtk.Image.new_from_icon_name("arrow-down", Gtk.IconSize.MENU)
        self.popup_icon_event_box = Gtk.EventBox()
        self.popup_icon_event_box.add(self.popup_icon)
        self.popup_icon_event_box.connect("button-press-event", self.show_popup)
        self.box.pack_end(self.popup_icon_event_box, False, False, 0)

        self.popover = Budgie.Popover.new(self)
        self.popover_manager = Budgie.PopoverManager()
        self.popover_manager.register_popover(self, self.popover)

        self.popover_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 10)
        self.popover_box.set_margin_bottom(5)
        self.popover_box.set_margin_top(5)
        self.popover_box.set_margin_start(5)
        self.popover_box.set_margin_end(5)
        self.popover.add(self.popover_box)

        self.settings = Gio.Settings.new(
            "com.github.zalesyc.budgie-media-player-applet"
        )
        SingleAppPlayer.author_max_len = self.settings.get_int("author-name-max-length")
        SingleAppPlayer.name_max_len = self.settings.get_int("media-title-max-length")
        self.settings.connect("changed", self.settings_changed)

        self.dbus_namespace_name = "org.mpris.MediaPlayer2"
        self.session_bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
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

        self.players_list: [SingleAppPlayer] = []
        for dbus_name in dbus_names:
            self.players_list.append(SingleAppPlayer(dbus_name))
            if len(self.players_list) < 2:
                self.box.pack_start(self.players_list[-1], False, False, 0)
            else:
                self.popover_box.add(self.players_list[-1])

        self.popover.get_child().show_all()
        self.show_all()

        if len(self.players_list) < 2:
            self.popup_icon.hide()

    def show_popup(self, *args):
        self.popover_manager.show_popover(self)

    def list_dbus_players(self):
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
        self, a, b, c, d, e, changes
    ):  # args a-e are arguments i dont need, but get sent by gtk
        if (changes[0] not in self.players_list) and changes[2]:  # player was added
            self.players_list.append(SingleAppPlayer(changes[0]))
            if len(self.players_list) < 2:
                self.box.pack_start(self.players_list[-1], False, False, 0)

            else:
                self.popover_box.add(self.players_list[-1])
                self.popup_icon.show()

        elif not changes[2]:  # player was removed
            for player in enumerate(self.players_list):
                if player[1].service_name == changes[0]:
                    if player[0] == 0:
                        self.box.remove(player[1])
                        del self.players_list[player[0]]

                        if len(self.players_list) > 0:
                            self.popover_box.remove(self.players_list[0])
                            self.box.pack_start(self.players_list[0], False, False, 0)

                    else:
                        self.popover_box.remove(player[1])
                        del self.players_list[player[0]]

            if len(self.players_list) < 2:
                self.popup_icon.hide()

    def settings_changed(self, settings, key):
        if key == "author-name-max-length" or key == "media-title-max-length":
            if key == "author-name-max-length":
                SingleAppPlayer.author_max_len = self.settings.get_int(key)
            else:
                SingleAppPlayer.name_max_len = self.settings.get_int(key)

            for appPlayer in self.players_list:
                appPlayer.reset_song_label()
            return
