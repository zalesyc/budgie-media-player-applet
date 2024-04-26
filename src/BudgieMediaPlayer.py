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
from PopupStyle import PopupStyle


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
        self.popup_style: PopupStyle = PopupStyle(self.settings.get_uint("popup-style"))

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
        self.panel_player_index = 0
        self.popover_ntb: Optional[Gtk.Notebook] = None
        self.popover_ntb = Gtk.Notebook.new()
        self.popover_ntb.set_margin_bottom(5)
        self.popover_ntb.set_margin_start(5)
        self.popover_ntb.set_margin_end(5)
        self.popover_ntb.set_show_border(False)

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
                self.players_list[-1].add_panel_view()
                self.box.pack_start(self.players_list[-1].panel_view, False, False, 0)
                self.panel_player_index = index

            self.popover_ntb.append_page(self.players_list[-1])

        self.popover.get_child().show_all()
        self.show_all()

        if len(self.players_list) < 2:
            self.popup_icon.hide()

    def show_popup(self, *_) -> None:
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

    def dbus_players_changed(
        self, _, __, ___, ____, _____, changes: GLib.Variant
    ) -> None:
        pass

    #     if (changes[0] not in self.players_list) and changes[2]:  # player was added
    #         if self.popup_style == PopupStyle.Old:
    #             self._player_added_old(changes[0])
    #
    #         elif self.popup_style == PopupStyle.Plasma:
    #             self._player_added_plasma(changes[0])
    #
    #     elif not changes[2]:  # player was removed
    #         for index, player in enumerate(self.players_list):
    #             if player.service_name == changes[0]:
    #                 if self.popup_style == PopupStyle.Old:
    #                     if index == 0:
    #                         self.box.remove(player)
    #                         del self.players_list[0]
    #
    #                         if len(self.players_list) > 0:
    #                             self.popover_box.remove(self.players_list[0])
    #                             self.box.pack_start(
    #                                 self.players_list[0], False, False, 0
    #                             )
    #                             self.players_list[0].panel_size_changed(
    #                                 self.album_cover_size
    #                             )
    #
    #                     else:
    #                         self.popover_box.remove(player)
    #                         del self.players_list[index]
    #
    #                 elif self.popup_style == PopupStyle.Plasma:
    #                     if index == 0:
    #                         if player.panel_view is not None:
    #                             self.box.remove(player.panel_view)
    #
    #                         if len(self.players_list) > 0:
    #                             self.players_list[1].panel_view = (
    #                                 PanelControlView(
    #                                     service_name=self.players_list[1].service_name,
    #                                     orientation=self.orientation,
    #                                     author_max_len=self.author_max_len,
    #                                     name_max_len=self.name_max_len,
    #                                     element_order=self.element_order,
    #                                     separator_text=self.separator_text,
    #                                     style=self.popup_style,
    #                                     open_popover_func=self.show_popup,
    #                                 ),
    #                             )
    #                             self.box.pack_start(
    #                                 self.players_list[1], False, False, 0
    #                             )
    #                             self.players_list[0].panel_view.panel_size_changed(
    #                                 self.album_cover_size
    #                             )
    #                     self.popover_ntb.remove(player.panel_view)
    #                     del self.players_list[index]
    #
    #                 break
    #
    #         if len(self.players_list) < 2:
    #             self.popup_icon.hide()
    #
    # def _player_added_old(self, service_name):
    #     self.players_list.append(
    #         PanelControlView(
    #             service_name=service_name,
    #             orientation=self.orientation,
    #             author_max_len=self.author_max_len,
    #             name_max_len=self.name_max_len,
    #             element_order=self.element_order,
    #             separator_text=self.separator_text,
    #             style=self.popup_style,
    #             open_popover_func=self.show_popup,
    #         ),
    #     )
    #     if len(self.players_list) < 2:
    #         self.box.pack_start(self.players_list[-1], False, False, 0)
    #         self.players_list[-1].panel_size_changed(self.album_cover_size)
    #
    #     else:
    #         self.popover_box.add(self.players_list[-1])
    #         self.popup_icon.show()
    #
    # def _player_added_plasma(self, service_name):
    #     self.players_list.append(
    #         PopupPlasmaControlView(
    #             service_name=service_name,
    #             style=self.popup_style,
    #             open_popover_func=self.show_popup,
    #         )
    #     )
    #     self.popover_ntb.append_page(self.players_list[-1])
    #
    #     if len(self.players_list) == 1:
    #         self.players_list[-1].panel_view = PanelControlView(
    #             service_name=service_name,
    #             orientation=self.orientation,
    #             author_max_len=self.author_max_len,
    #             name_max_len=self.name_max_len,
    #             element_order=self.element_order,
    #             separator_text=self.separator_text,
    #             style=self.popup_style,
    #             open_popover_func=self.show_popup,
    #         )
    #
    #         self.box.pack_start(self.players_list[-1], False, False, 0)
    #         self.players_list[-1].panel_size_changed(self.album_cover_size)

    def settings_changed(self, settings, changed_key_name: str) -> None:
        if changed_key_name == "author-name-max-length":
            self.author_max_len = self.settings.get_int(changed_key_name)
            for app_player in self.players_list:
                app_player.author_max_len = self.author_max_len
                app_player.metadata_changed()
            return

        if changed_key_name == "media-title-max-length":
            self.name_max_len = self.settings.get_int(changed_key_name)
            for app_player in self.players_list:
                app_player.name_max_len = self.name_max_len
                app_player.metadata_changed()

        if changed_key_name == "element-order":
            self.element_order = self.settings.get_strv(changed_key_name)
            for app_player in self.players_list:
                pass
                # if app_player is PanelControlView:
                #     app_player.set_element_order(self.element_order)
            return

        if changed_key_name == "separator-text":
            self.separator_text = self.settings.get_string("separator-text")
            for app_player in self.players_list:
                pass
                # app_player.set_separator_text(self.separator_text)

    def do_panel_size_changed(
        self, panel_size: int, icon_size: int, small_icon_size: int
    ) -> None:
        if len(self.players_list) > 0:
            self.players_list[0].panel_size_changed(icon_size)

    def do_panel_position_changed(self, position: Budgie.PanelPosition) -> None:
        if position in {Budgie.PanelPosition.LEFT, Budgie.PanelPosition.RIGHT}:
            self.orientation = Gtk.Orientation.VERTICAL
        else:
            self.orientation = Gtk.Orientation.HORIZONTAL

        self.box.set_orientation(self.orientation)
        if self.popup_style == PopupStyle.Old:
            self.popover_box.set_orientation(Gtk.Orientation(not self.orientation))
            for player in self.players_list:
                player.panel_orientation_changed(self.orientation)

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return SettingsPage(self.settings)

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise."""
        return True
