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

import threading
from typing import Optional, Union, Callable
from enum import IntEnum
from io import BytesIO
from dataclasses import dataclass
from urllib.parse import urlparse, ParseResult
import requests
from PIL import Image
from PanelControlView import PanelControlView
from AlbumCoverData import AlbumCoverType, AlbumCoverData

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf

from mprisWrapper import MprisWrapper
from PopupStyle import PopupStyle


@dataclass
class DownloadThreadData:
    thread: threading.Thread
    stop_event: threading.Event


class SingleAppPlayer(Gtk.Bin):
    def __init__(
        self,
        service_name: str,
        open_popover_func: callable,
        orientation: Gtk.Orientation,
        author_max_len: int,
        name_max_len: int,
        separator_text: str,
    ):
        super().__init__()
        self.panel_view: Optional[PanelControlView] = None

        self.open_popover_func = open_popover_func
        self.service_name: str = service_name
        self.dbus_player: MprisWrapper = MprisWrapper(self.service_name)
        self.current_download_thread: Optional[DownloadThreadData] = None
        self.album_cover_size: int = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.orientation: Gtk.Orientation = orientation
        self.author_max_len: int = author_max_len
        self.name_max_len: int = name_max_len
        self.separator_text: str = separator_text
        self.service_name: str = service_name

        self.playing: bool = False
        self.artist: Optional[list[str]] = []
        self.title: Optional[str] = ""
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

        playing = self.dbus_player.get_player_property("PlaybackStatus").get_string()
        if playing == "Playing":
            self.playing = True
        elif playing == "Paused":
            self.playing = False

        start_song_metadata = self.dbus_player.get_player_property("Metadata")
        if start_song_metadata is not None:
            new_artist = start_song_metadata.lookup_value("xesam:artist", None)
            if new_artist is not None:
                self.artist = new_artist.get_strv()
            new_title = start_song_metadata.lookup_value("xesam:title", None)
            if new_title is not None:
                self.title = new_title.get_string()
            self._set_album_cover(
                start_song_metadata.lookup_value("mpris:artUrl", None)
            )
        else:
            self._set_album_cover_other()

        self.can_play = self.dbus_player.get_player_property("CanPlay").get_boolean()
        self.can_pause = self.dbus_player.get_player_property("CanPlay").get_boolean()
        self.can_go_previous = self.dbus_player.get_player_property(
            "CanGoPrevious"
        ).get_boolean()
        self.can_go_next = self.dbus_player.get_player_property(
            "CanGoNext"
        ).get_boolean()

        self.dbus_player.player_connect("PlaybackStatus", self._playing_changed)
        self.dbus_player.player_connect("Metadata", self._metadata_changed)
        self.dbus_player.player_connect("CanPlay", self._can_play_changed)
        self.dbus_player.player_connect("CanPause", self._can_pause_changed)
        self.dbus_player.player_connect("CanGoPrevious", self._can_go_previous_changed)
        self.dbus_player.player_connect("CanGoNext", self._can_go_next_changed)

    def add_panel_view(self) -> None:
        self.panel_view = PanelControlView(
            dbus_player=self.dbus_player,
            title=self.title,
            artist=self.artist,
            playing=self.playing,
            can_play_or_pause=(self.can_play or self.can_pause),
            can_go_previous=self.can_go_previous,
            can_go_next=self.can_go_next,
            open_popover_func=self.open_popover_func,
        )

    def remove_panel_view(self) -> None:
        self.panel_view = None

    def panel_size_changed(self, new_size: int):
        pass

    def panel_orientation_changed(self, new_orientation: Gtk.Orientation):
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

    def _playing_changed(self, status: GLib.Variant) -> None:
        new_playing = None
        if status.get_string() == "Playing":
            new_playing = True

        elif status.get_string() == "Paused":
            new_playing = False

        if new_playing is not None and new_playing != self.playing:
            self.playing = new_playing
            self.playing_changed()
            if self.panel_view is not None:
                self.panel_view.set_playing(self.playing)

    def _metadata_changed(self, metadata: GLib.Variant) -> None:
        new_artist = metadata.lookup_value("xesam:artist", GLib.VariantType.new("as"))
        new_title = metadata.lookup_value("xesam:title", GLib.VariantType.new("s"))
        changed = False

        if new_artist is not None and new_artist.get_strv() != self.artist:
            self.artist = new_artist.get_strv()
            changed = True

        if new_title is not None and new_title.get_string() != self.title:
            self.title = new_title.get_string()
            changed = True

        if changed:
            self.metadata_changed()
            if self.panel_view is not None:
                self.panel_view.set_metadata(self.artist, self.title)

        self._set_album_cover(metadata.lookup_value("mpris:artUrl", None))

    def _can_play_changed(self, metadata: GLib.Variant) -> None:
        new_can_play = metadata.get_boolean()
        if new_can_play is not None and new_can_play != self.can_play:
            self.can_play = new_can_play
            self.can_play_changed()

    def _can_pause_changed(self, metadata: GLib.Variant) -> None:
        new_can_pause = metadata.get_boolean()
        if new_can_pause is not None and new_can_pause != self.can_pause:
            self.can_pause = new_can_pause
            self.can_pause_changed()

    def _can_go_previous_changed(self, metadata: GLib.Variant) -> None:
        new_can_go_previous = metadata.get_boolean()
        if (
            new_can_go_previous is not None
            and new_can_go_previous != self.can_go_previous
        ):
            self.can_go_previous = new_can_go_previous
            self.can_go_previous_changed()

    def _can_go_next_changed(self, metadata: GLib.Variant) -> None:
        new_can_go_next = metadata.get_boolean()
        if new_can_go_next is not None and new_can_go_next != self.can_go_next:
            self.can_go_next = new_can_go_next
            self.can_go_next_changed()

    def _album_cover_changed(
        self, cover: Union[GdkPixbuf.Pixbuf, Gio.Icon, str], cover_type: AlbumCoverType
    ):
        if cover_type == AlbumCoverType.Pixbuf:
            self.album_cover_data.song_cover_pixbuf = cover
            self.album_cover_data.cover_type = AlbumCoverType.Pixbuf
            self.album_cover_changed()

        else:
            if cover != self.album_cover_data.song_cover_other:
                self.album_cover_data.song_cover_other = cover
                self.album_cover_data.cover_type = cover_type
                self.album_cover_changed()

        return False

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

        self._album_cover_changed("multimedia-player-symbolic", AlbumCoverType.IconName)

    def _set_album_cover_file(self, parsed_url: ParseResult) -> None:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(parsed_url.path)
            self._album_cover_changed(pixbuf, AlbumCoverType.Pixbuf)
        except gi.repository.GLib.GError:
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
