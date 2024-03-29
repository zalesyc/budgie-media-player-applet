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

from typing import Callable, Optional
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


class MprisWrapper:
    def __init__(self, service_name: str):
        object_path = "/org/mpris/MediaPlayer2"
        interface_name_player = "org.mpris.MediaPlayer2.Player"
        interface_name_app = "org.mpris.MediaPlayer2"

        self._connected_functions: dict[str, Callable] = {}

        self.player_proxy: Gio.DBusProxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            service_name,
            object_path,
            interface_name_player,
            None,
        )

        self.app_proxy: Gio.DBusProxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            service_name,
            object_path,
            interface_name_app,
            None,
        )

        self.player_proxy.connect("g-properties-changed", self._property_changed)

    def player_connect(
        self, property_name: str, func: Callable[[GLib.Variant], None]
    ) -> None:
        self._connected_functions.update({property_name: func})

    def get_player_property(self, property_name: str) -> Optional[GLib.Variant]:
        return self.player_proxy.get_cached_property(property_name)

    def get_app_property(self, property_name: str) -> Optional[GLib.Variant]:
        return self.app_proxy.get_cached_property(property_name)

    def call_player_method(
        self, method_name: str, callback: Optional[Callable] = None
    ) -> None:
        self.player_proxy.call(
            method_name=method_name,
            parameters=None,
            flags=Gio.DBusCallFlags.NONE,
            timeout_msec=-1,
            cancellable=None,
            callback=callback,
        )

    def call_app_method(
        self, method_name: str, callback: Optional[Callable] = None
    ) -> None:
        self.app_proxy.call(
            method_name=method_name,
            parameters=None,
            flags=Gio.DBusCallFlags.NONE,
            timeout_msec=-1,
            cancellable=None,
            callback=callback,
        )

    def _property_changed(
        self, proxy: Gio.DBusProxy, changed_properties: GLib.Variant, *args
    ) -> None:
        for key in self._connected_functions:
            property_value = changed_properties.lookup_value(key, None)
            if property_value is None:
                continue
            func = self._connected_functions.get(key)
            if func is None:
                continue
            func(property_value)
