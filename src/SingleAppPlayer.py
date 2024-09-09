# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
from typing import Optional, Union, Callable
from io import BytesIO
from dataclasses import dataclass
from urllib.parse import urlparse, ParseResult
import requests
from PIL import Image
from PanelControlView import PanelControlView
from EnumsStructs import AlbumCoverType, AlbumCoverData
from mprisWrapper import MprisWrapper

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf


@dataclass
class DownloadThreadData:
    thread: threading.Thread
    stop_event: threading.Event


class SingleAppPlayer(Gtk.Bin):
    ICON_SIZE = Gtk.IconSize.MENU

    def __init__(
        self,
        service_name: str,
        open_popover_func: Callable[[], None],
        on_pin_clicked: Callable[[str], None],
        settings: Gio.Settings,
    ):
        super().__init__()

        self.settings: Gio.Settings = settings

        self.panel_view: Optional[PanelControlView] = None

        self.open_popover_func: Callable = open_popover_func
        self.on_pin_clicked: Callable = on_pin_clicked
        self.service_name: str = service_name
        self.dbus_player: MprisWrapper = MprisWrapper(self.service_name)
        self.current_download_thread: Optional[DownloadThreadData] = None

        self.playing: bool = False
        self.artist: Optional[list[str]] = []
        self.title: Optional[str] = ""
        self.song_length: int = 0
        """ song's length in seconds"""
        self.album_cover_data: AlbumCoverData = AlbumCoverData(
            cover_type=AlbumCoverType.Null,
            image_url_http=None,
            song_cover_pixbuf=None,
            song_cover_other=None,
        )
        self.can_play: bool = False
        self.can_pause: bool = False
        self.can_go_previous: bool = False
        self.can_go_next: bool = False
        self.rate: float = 1.0

        if (
            playing := self.dbus_player.get_player_property("PlaybackStatus")
        ) is not None:
            if playing.get_string() == "Playing":
                self.playing = True
            elif playing.get_string() == "Paused":
                self.playing = False

        start_song_metadata = self.dbus_player.get_player_property("Metadata")
        if start_song_metadata is not None:
            new_artist = start_song_metadata.lookup_value(
                "xesam:artist", GLib.VariantType.new("as")
            )
            if new_artist is not None:
                self.artist = new_artist.get_strv()

            new_title = start_song_metadata.lookup_value(
                "xesam:title", GLib.VariantType.new("s")
            )
            if new_title is not None:
                self.title = new_title.get_string()

            self._set_album_cover(
                start_song_metadata.lookup_value("mpris:artUrl", None)
            )

            new_len = start_song_metadata.lookup_value("mpris:length", None)
            if new_len is not None:
                new_len_int = 0
                if new_len.is_of_type(GLib.VariantType.new("x")):
                    new_len_int = new_len.get_int64()
                elif new_len.is_of_type(GLib.VariantType.new("t")):
                    new_len_int = new_len.get_uint64()
                self.song_length = round(new_len_int / 1_000_000)
        else:
            self._set_album_cover_other()

        if (can_play := self.dbus_player.get_player_property("CanPlay")) is not None:
            self.can_play = can_play.get_boolean()

        if (can_pause := self.dbus_player.get_player_property("CanPause")) is not None:
            self.can_pause = can_pause.get_boolean()

        if (
            can_go_previous := self.dbus_player.get_player_property("CanGoPrevious")
        ) is not None:
            self.can_go_previous = can_go_previous.get_boolean()

        if (
            can_go_next := self.dbus_player.get_player_property("CanGoNext")
        ) is not None:
            self.can_go_next = can_go_next.get_boolean()

        rate = self.dbus_player.get_player_property("Rate")
        self.rate = 1.0 if rate is None else rate.get_double()

        app_name = ""
        if (app_name_var := self.dbus_player.get_app_property("Identity")) is not None:
            app_name = GLib.markup_escape_text(app_name_var.get_string())

        self.icon: Gtk.Image = Gtk.Image(
            tooltip_markup=f"<b>{app_name}</b>"
            f" - {GLib.markup_escape_text(self.service_name)}"
        )
        self._set_icon(self.dbus_player.get_app_property("DesktopEntry"))

        self.dbus_player.player_connect("PlaybackStatus", self._playing_changed)
        self.dbus_player.player_connect("Metadata", self._metadata_changed)
        self.dbus_player.player_connect("CanPlay", self._can_play_changed)
        self.dbus_player.player_connect("CanPause", self._can_pause_changed)
        self.dbus_player.player_connect("CanGoPrevious", self._can_go_previous_changed)
        self.dbus_player.player_connect("CanGoNext", self._can_go_next_changed)
        self.dbus_player.player_connect("Rate", self._rate_changed)
        self.dbus_player.app_connect("DesktopEntry", self._set_icon)

    def add_panel_view(
        self,
        orientation: Gtk.Orientation,
    ) -> None:
        self.panel_view = PanelControlView(
            dbus_player=self.dbus_player,
            title=self.title,
            artist=self.artist,
            album_cover=self.album_cover_data,
            playing=self.playing,
            can_play_or_pause=(self.can_play or self.can_pause),
            can_go_previous=self.can_go_previous,
            can_go_next=self.can_go_next,
            open_popover_func=self.open_popover_func,
            orientation=orientation,
            settings=self.settings,
        )

        self.pinned_changed()

    def remove_panel_view(self) -> None:
        if self.panel_view is None:
            print(
                "budgie-media-player-applet: trying to remove panel_view, "
                f"which is already None, player id: {self.service_name}"
            )
            return
        self.panel_view.destroy()
        self.panel_view = None
        self.pinned_changed()

    def panel_size_changed(self, new_size: int) -> None:
        if self.panel_view is not None:
            self.panel_view.panel_size_changed(new_size, self.album_cover_data)

    def panel_orientation_changed(self, new_orientation: Gtk.Orientation) -> None:
        if self.panel_view is not None:
            self.panel_view.set_orientation(new_orientation)

    def popover_to_be_open(self) -> None:
        pass

    def popover_just_closed(self) -> None:
        pass

    def playing_changed(self) -> None:
        pass

    def metadata_changed(self) -> None:
        pass

    def can_play_changed(self) -> None:
        pass

    def can_pause_changed(self) -> None:
        pass

    def can_go_previous_changed(self) -> None:
        pass

    def can_go_next_changed(self) -> None:
        pass

    def album_cover_changed(self) -> None:
        pass

    def pinned_changed(self) -> None:
        pass

    def _playing_changed(self, status: GLib.Variant) -> None:
        new_playing = None
        if status.get_string() == "Playing":
            new_playing = True

        elif status.get_string() == "Paused":
            new_playing = False

        if new_playing is not None and new_playing != self.playing:
            self.playing = new_playing
            if self.panel_view is not None:
                self.panel_view.set_playing(self.playing)
            self.playing_changed()

    def _metadata_changed(self, metadata: GLib.Variant) -> None:
        new_artist = metadata.lookup_value("xesam:artist", GLib.VariantType.new("as"))
        new_title = metadata.lookup_value("xesam:title", GLib.VariantType.new("s"))
        new_length = metadata.lookup_value("mpris:length", None)
        changed_art_title = False
        changed_len = False

        if new_artist is not None and new_artist.get_strv() != self.artist:
            self.artist = new_artist.get_strv()
            changed_art_title = True

        if new_title is not None and new_title.get_string() != self.title:
            self.title = new_title.get_string()
            changed_art_title = True

        if new_length is not None:
            new_len_int = 0
            if new_length.is_of_type(GLib.VariantType.new("x")):
                new_len_int = new_length.get_int64()
            elif new_length.is_of_type(GLib.VariantType.new("t")):
                new_len_int = new_length.get_uint64()

            new_length_secs = round(new_len_int / 1_000_000)

            if new_length_secs != self.song_length:
                self.song_length = new_length_secs
                changed_len = True

        if changed_len or changed_art_title:
            if changed_art_title and self.panel_view is not None:
                self.panel_view.set_metadata(self.artist, self.title)
            self.metadata_changed()

        if changed_art_title:
            self._set_album_cover(metadata.lookup_value("mpris:artUrl", None))

    def _can_play_changed(self, metadata: GLib.Variant) -> None:
        new_can_play = metadata.get_boolean()
        if new_can_play is not None and new_can_play != self.can_play:
            self.can_play = new_can_play
            if self.panel_view is not None:
                self.panel_view.set_can_play_or_pause(self.can_play or self.can_pause)
            self.can_play_changed()

    def _can_pause_changed(self, metadata: GLib.Variant) -> None:
        new_can_pause = metadata.get_boolean()
        if new_can_pause is not None and new_can_pause != self.can_pause:
            self.can_pause = new_can_pause
            if self.panel_view is not None:
                self.panel_view.set_can_play_or_pause(self.can_play or self.can_pause)
            self.can_pause_changed()

    def _can_go_previous_changed(self, metadata: GLib.Variant) -> None:
        new_can_go_previous = metadata.get_boolean()
        if (
            new_can_go_previous is not None
            and new_can_go_previous != self.can_go_previous
        ):
            self.can_go_previous = new_can_go_previous
            if self.panel_view is not None:
                self.panel_view.set_can_go_previous(self.can_go_previous)
            self.can_go_previous_changed()

    def _can_go_next_changed(self, metadata: GLib.Variant) -> None:
        new_can_go_next = metadata.get_boolean()
        if new_can_go_next is not None and new_can_go_next != self.can_go_next:
            self.can_go_next = new_can_go_next
            if self.panel_view is not None:
                self.panel_view.set_can_go_next(self.can_go_previous)
            self.can_go_next_changed()

    def _album_cover_changed(
        self, cover: Union[GdkPixbuf.Pixbuf, Gio.Icon, str], cover_type: AlbumCoverType
    ) -> bool:
        if cover_type == AlbumCoverType.Pixbuf:
            self.album_cover_data.song_cover_pixbuf = cover
            self.album_cover_data.cover_type = AlbumCoverType.Pixbuf
            if self.panel_view is not None:
                self.panel_view.set_album_cover(self.album_cover_data)
            self.album_cover_changed()

        else:
            if cover != self.album_cover_data.song_cover_other:
                self.album_cover_data.song_cover_other = cover
                self.album_cover_data.cover_type = cover_type
                if self.panel_view is not None:
                    self.panel_view.set_album_cover(self.album_cover_data)
                self.album_cover_changed()

        return False

    def _rate_changed(self, new_rate: GLib.Variant) -> None:
        self.rate = new_rate.get_double()

    def _set_album_cover(self, art_url_variant: GLib.Variant) -> None:
        if art_url_variant is None:
            self._set_album_cover_other()
            return

        url = art_url_variant.get_string()

        if self.album_cover_data.image_url_http == url:
            return

        self.album_cover_data.image_url_http = url

        parsed_url = urlparse(url)

        if parsed_url.scheme == "file":
            self._set_album_cover_file(parsed_url)
            return

        if parsed_url.scheme == "https":
            self._set_album_cover_https(url)
            return

        self._set_album_cover_other()

    def _set_album_cover_other(self) -> None:
        desktop_file_name_variant = self.dbus_player.get_app_property("DesktopEntry")
        if desktop_file_name_variant is not None:
            desktop_file_name = desktop_file_name_variant.get_string()
            try:
                desktop_app_info = Gio.DesktopAppInfo.new(
                    desktop_file_name + ".desktop"
                )
            except TypeError:
                pass
            else:
                if desktop_app_info is not None:
                    desktop_icon = desktop_app_info.get_icon()
                    if desktop_icon is not None:
                        self._album_cover_changed(desktop_icon, AlbumCoverType.Gicon)
                    return

        self._album_cover_changed("emblem-music-symbolic", AlbumCoverType.IconName)

    def _set_album_cover_file(self, parsed_url: ParseResult) -> None:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(parsed_url.path)
            if pixbuf is not None:
                self._album_cover_changed(pixbuf, AlbumCoverType.Pixbuf)
                return
        except gi.repository.GLib.GError:
            self._set_album_cover_other()
        else:
            self._set_album_cover_other()

    def _set_album_cover_https(self, url: str) -> None:
        if self.current_download_thread is not None and (
            self.current_download_thread.thread.is_alive()
        ):
            self.current_download_thread.stop_event.set()

        event = threading.Event()
        self.current_download_thread = DownloadThreadData(
            thread=threading.Thread(
                target=self._get_album_cover_image_to_gdkpixbuf,
                args=(url, event),
                daemon=True,
            ),
            stop_event=event,
        )
        self.current_download_thread.thread.start()

    def _get_album_cover_image_to_gdkpixbuf(
        self, url: str, stop_event: threading.Event
    ) -> None:
        pixbuf = self._download_album_cover_image_to_gdkpixbuf(url, stop_event)
        if pixbuf is None:
            GLib.idle_add(self._set_album_cover_other)
            return

        GLib.idle_add(self._album_cover_changed, pixbuf, AlbumCoverType.Pixbuf)

    @staticmethod
    def _download_album_cover_image_to_gdkpixbuf(
        url: str, stop_event: threading.Event
    ) -> Optional[GdkPixbuf.Pixbuf]:
        try:
            # Send a GET request to the URL
            response = requests.get(url, stream=True, timeout=4)
            if response.status_code != 200:
                return None

            # Read the image data in chunks
            img_data = BytesIO()
            for chunk in response.iter_content(chunk_size=1024):
                if stop_event.is_set():
                    response.close()
                    return None
                img_data.write(chunk)

            # Rewind the buffer and open as an image with Pillow
            img_data.seek(0)
            pil_image = Image.open(img_data)

            # Convert the Pillow image to a GdkPixbuf
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                pil_image.tobytes(),  # Image data as bytes
                GdkPixbuf.Colorspace.RGB,
                False,
                8,  # Bits per sample
                pil_image.width,
                pil_image.height,
                pil_image.width * 3,
                None,
            )

        except Exception:
            return None

        if stop_event.is_set():
            return None

        return pixbuf

    def _set_icon(self, desktop_file_name_var: GLib.Variant) -> None:
        if desktop_file_name_var is not None:
            desktop_file_name = desktop_file_name_var.get_string()

            try:
                desktop_app_info = Gio.DesktopAppInfo.new(
                    desktop_file_name + ".desktop"
                )
            except TypeError:
                pass
            else:
                if desktop_app_info is not None:
                    desktop_icon = desktop_app_info.get_icon()
                    if desktop_icon is not None:
                        self.icon.set_from_gicon(desktop_icon, self.ICON_SIZE)
                        return

        self.icon.set_from_icon_name("emblem-music-symbolic", self.ICON_SIZE)

    def _get_resized_pixbuf(
        self, available_height: int, available_width: int, portion_to_fill: float
    ) -> GdkPixbuf:
        square_size = min(
            available_height,
            round(available_width * portion_to_fill),
        )
        if (
            self.album_cover_data.song_cover_pixbuf.get_width()
            < self.album_cover_data.song_cover_pixbuf.get_height()
        ):
            resized_pixbuf = self.album_cover_data.song_cover_pixbuf.scale_simple(
                int(
                    (square_size / self.album_cover_data.song_cover_pixbuf.get_height())
                    * self.album_cover_data.song_cover_pixbuf.get_width()
                ),
                square_size,
                GdkPixbuf.InterpType.BILINEAR,
            )
        else:
            resized_pixbuf = self.album_cover_data.song_cover_pixbuf.scale_simple(
                square_size,
                int(
                    (square_size / self.album_cover_data.song_cover_pixbuf.get_width())
                    * self.album_cover_data.song_cover_pixbuf.get_height()
                ),
                GdkPixbuf.InterpType.BILINEAR,
            )
        return resized_pixbuf
