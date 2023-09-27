import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
from typing import Callable


class MprisWrapper:
    def __init__(self, service_name: str):
        self._object_path = "/org/mpris/MediaPlayer2"
        self._interface_name_player = "org.mpris.MediaPlayer2.Player"
        self._interface_name_app = "org.mpris.MediaPlayer2"
        self._connected_functions: dict[str:Callable] = {}
        self.service_name: str = service_name

        self.player_proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            self.service_name,
            self._object_path,
            self._interface_name_player,
            None,
        )

        self.app_proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.NONE,
            None,
            self.service_name,
            self._object_path,
            self._interface_name_app,
            None,
        )

        self.player_proxy.connect("g-properties-changed", self._property_changed)

    def player_connect(
        self, property_name: str, func: Callable[[GLib.Variant], None]
    ) -> None:
        self._connected_functions.update({property_name: func})

    def get_player_property(self, property_name: str) -> GLib.Variant:
        return self.player_proxy.get_cached_property(property_name)

    def get_app_property(self, property_name: str) -> GLib.Variant:
        return self.app_proxy.get_cached_property(property_name)

    def call_player_method(self, method_name: str, callback: Callable = None) -> None:
        self.player_proxy.call(
            method_name=method_name,
            parameters=None,
            flags=0,
            timeout_msec=-1,
            cancellable=None,
            callback=callback,
            user_data=None,
        )

    def call_app_method(self, method_name: str, callback: Callable = None) -> None:
        self.app_proxy.call(
            method_name=method_name,
            parameters=None,
            flags=0,
            timeout_msec=-1,
            cancellable=None,
            callback=callback,
            user_data=None,
        )

    def _property_changed(self, proxy, parameters, *args):
        for key in self._connected_functions.keys():
            property_value = parameters.lookup_value(key, None)
            if property_value is not None:
                func = self._connected_functions.get(key)
                func(property_value)
