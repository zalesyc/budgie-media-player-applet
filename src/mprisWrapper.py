# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, Optional
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


class MprisWrapper:
    def __init__(self, service_name: str):
        object_path = "/org/mpris/MediaPlayer2"
        interface_name_player = "org.mpris.MediaPlayer2.Player"
        interface_name_app = "org.mpris.MediaPlayer2"
        interface_name_property = "org.freedesktop.DBus.Properties"

        self._connected_functions_player: dict[str, Callable] = {}
        self._connected_functions_app: dict[str, Callable] = {}

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

        self.properties_proxy: Gio.DBusProxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            service_name,
            object_path,
            interface_name_property,
            None,
        )

        self.player_proxy.connect("g-properties-changed", self._player_property_changed)
        self.app_proxy.connect("g-properties-changed", self._app_property_changed)

    def player_connect(
        self, property_name: str, func: Callable[[GLib.Variant], None]
    ) -> None:
        self._connected_functions_player.update({property_name: func})

    def app_connect(
        self, property_name: str, func: Callable[[GLib.Variant], None]
    ) -> None:
        self._connected_functions_app.update({property_name: func})

    def get_player_property(self, property_name: str) -> Optional[GLib.Variant]:
        return self.player_proxy.get_cached_property(property_name)

    def get_player_property_non_cached(
        self,
        property_name: str,
        callback: Callable[[Optional[GLib.Variant]], None],
    ) -> None:
        self.properties_proxy.call(
            "Get",
            GLib.Variant("(ss)", ("org.mpris.MediaPlayer2.Player", property_name)),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            self._get_player_property_callback,
            callback,
        )

    @staticmethod
    def _get_player_property_callback(
        source_object: Gio.DBusProxy,
        result: Gio.Task,
        data: Callable[[Optional[GLib.Variant]], None],
    ) -> None:
        try:
            content = source_object.call_finish(result)
        except GLib.GError:
            data(None)
        else:
            data(content)

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

    def _player_property_changed(
        self, _, changed_properties: GLib.Variant, *__
    ) -> None:
        for key, func in self._connected_functions_player.items():
            property_value = changed_properties.lookup_value(key, None)
            if property_value is None:
                continue
            if func is None:
                continue
            func(property_value)

    def _app_property_changed(self, _, changed_properties: GLib.Variant, *__) -> None:
        for key, func in self._connected_functions_app.items():
            property_value = changed_properties.lookup_value(key, None)
            if property_value is None:
                continue
            if func is None:
                continue
            func(property_value)
