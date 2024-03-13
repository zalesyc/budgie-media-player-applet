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
from typing import Optional, Callable
from io import BytesIO
from dataclasses import dataclass
from urllib.parse import urlparse, ParseResult
import requests
from PIL import Image

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf

from mprisWrapper import MprisWrapper


@dataclass
class AlbumCoverData:
    image_url: Optional[str]
    song_cover: Optional[GdkPixbuf.Pixbuf]


@dataclass
class Element:
    widget: Gtk.Widget
    spacing: int


@dataclass
class DownloadThreadData:
    thread: threading.Thread
    stop_event: threading.Event


class SingleAppPlayer(Gtk.Box):
    def __init__(
        self,
        service_name: str,
        orientation: Gtk.Orientation,
        author_max_len: int,
        name_max_len: int,
        element_order: list[str],
        separator_text: str,
    ):
        self.album_cover_size: int = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.orientation: Gtk.Orientation = orientation
        self.author_max_len: int = author_max_len
        self.name_max_len: int = name_max_len
        self.separator_text: str = separator_text

        Gtk.Box.__init__(self, spacing=0)
        self.service_name: str = service_name

        self.dbus_player: MprisWrapper = MprisWrapper(self.service_name)
        self.dbus_player.player_connect("PlaybackStatus", self.playing_changed)
        self.dbus_player.player_connect("Metadata", self.metadata_changed)

        start_song_metadata = self.dbus_player.get_player_property("Metadata")

        self.available_elements: dict[str, Element] = {}

        # album_cover
        self.current_download_thread: Optional[DownloadThreadData] = None

        self.album_cover_data: AlbumCoverData = AlbumCoverData(None, None)
        self.album_cover: Gtk.Image = Gtk.Image.new_from_icon_name(
            "action-unavailable-symbolic", Gtk.IconSize.MENU
        )
        album_cover_event_box = Gtk.EventBox()
        album_cover_event_box.add(self.album_cover)
        album_cover_event_box.connect("button-press-event", self.song_clicked)
        if start_song_metadata is None:
            self._set_album_cover_other()
        else:
            self._set_album_cover(
                start_song_metadata.lookup_value("mpris:artUrl", None)
            )
        self.available_elements.update(
            {"album_cover": Element(album_cover_event_box, 5)}
        )

        # song_name
        self.song_name: Gtk.Label = Gtk.Label()
        song_name_event_box = Gtk.EventBox()
        song_name_event_box.add(self.song_name)
        song_name_event_box.connect("button-press-event", self.song_clicked)
        self.available_elements.update({"song_name": Element(song_name_event_box, 4)})

        # song_author
        self.song_author: Gtk.Label = Gtk.Label()
        song_author_event_box = Gtk.EventBox()
        song_author_event_box.add(self.song_author)
        song_author_event_box.connect("button-press-event", self.song_clicked)
        self.available_elements.update(
            {"song_author": Element(song_author_event_box, 4)}
        )

        # song_separator
        self.song_separator: Gtk.Label = Gtk.Label(label=self.separator_text)
        self.available_elements.update(
            {"song_separator": Element(self.song_separator, 4)}
        )

        # play_pause_button
        can_play = self.dbus_player.get_player_property("CanPlay")
        self.can_play: bool = can_play.get_boolean() if can_play is not None else False
        can_pause = self.dbus_player.get_player_property("CanPause")
        self.can_pause: bool = (
            can_pause.get_boolean() if can_pause is not None else False
        )

        playback_status = self.dbus_player.get_player_property("PlaybackStatus")
        if playback_status is not None and playback_status.get_string() == "Playing":
            self.play_pause_button: Gtk.Button = self._init_button(
                "media-playback-pause-symbolic",
                self.play_paused_clicked,
                enabled=(self.can_pause or self.can_play),
            )

        else:
            self.play_pause_button = self._init_button(
                "media-playback-start-symbolic",
                self.play_paused_clicked,
                enabled=(self.can_pause or self.can_play),
            )
        self.dbus_player.player_connect("CanPlay", self.can_play_changed)
        self.dbus_player.player_connect("CanPause", self.can_pause_changed)
        self.available_elements.update(
            {"play_pause_button": Element(self.play_pause_button, 0)}
        )

        # backward_button
        can_go_previous = self.dbus_player.get_player_property("CanGoPrevious")
        self.backward_button: Gtk.Button = self._init_button(
            "media-skip-backward-symbolic",
            self.backward_clicked,
            enabled=(
                can_go_previous.get_boolean() if can_go_previous is not None else False
            ),
        )
        self.dbus_player.player_connect("CanGoPrevious", self.can_go_previous_changed)
        self.available_elements.update(
            {"backward_button": Element(self.backward_button, 0)}
        )

        # forward_button
        can_go_next = self.dbus_player.get_player_property("CanGoNext")
        self.forward_button: Gtk.Button = self._init_button(
            "media-skip-forward-symbolic",
            self.forward_clicked,
            enabled=can_go_next.get_boolean() if can_go_next is not None else False,
        )
        self.dbus_player.player_connect("CanGoNext", self.can_go_next_changed)
        self.available_elements.update(
            {"forward_button": Element(self.forward_button, 0)}
        )

        if start_song_metadata is None:
            self._set_song_label(None, None)
        else:
            self._set_song_label(
                start_song_metadata.lookup_value("xesam:artist", None),
                start_song_metadata.lookup_value("xesam:title", None),
            )
        self.set_orientation(orientation)
        self.set_element_order(element_order, remove_previous=False)
        self.show_all()

    def set_orientation(self, orientation: Gtk.Orientation) -> None:
        self.orientation = orientation
        angle = 0 if orientation == Gtk.Orientation.HORIZONTAL else 270
        self.song_name.set_angle(angle)
        self.song_author.set_angle(angle)
        self.song_separator.set_angle(angle)

        metadata_property = self.dbus_player.get_player_property("Metadata")

        if metadata_property is not None:
            self._set_album_cover(metadata_property.lookup_value("mpris:artUrl", None))
        super().set_orientation(orientation)

    def reset_song_label(self) -> None:
        metadata = self.dbus_player.get_player_property("Metadata")
        if metadata is None:
            self._set_song_label(None, None)
        else:
            self._set_song_label(
                metadata.lookup_value("xesam:artist", None),
                metadata.lookup_value("xesam:title", None),
            )

    def set_album_cover_size(self, size: int) -> None:
        self.album_cover_size = size
        if self.album_cover_data.song_cover is not None:
            pixbuf = self.album_cover_data.song_cover

            if self.orientation == Gtk.Orientation.HORIZONTAL:
                self.album_cover.set_from_pixbuf(
                    pixbuf.scale_simple(
                        int(
                            (self.album_cover_size / pixbuf.get_height())
                            * pixbuf.get_width()
                        ),
                        self.album_cover_size,
                        GdkPixbuf.InterpType.NEAREST,
                    )
                )
                return

            self.album_cover.set_from_pixbuf(
                pixbuf.scale_simple(
                    self.album_cover_size,
                    int(
                        (self.album_cover_size / pixbuf.get_width())
                        * pixbuf.get_height()
                    ),
                    GdkPixbuf.InterpType.NEAREST,
                )
            )

    def set_element_order(self, order: list[str], remove_previous: bool = True) -> None:
        if remove_previous:
            self.foreach(self.remove)

        for element_name in order:
            element = self.available_elements.get(element_name)
            if element is None:
                print(
                    f"'{element_name}' not in available elements - probably wrong settings -> skipping"
                )  # TODO: make this error in log framework
                continue
            self.pack_start(element.widget, False, False, element.spacing)

        self.show_all()

    def set_separator_text(self, new_text: str, override_set_text: bool = True) -> None:
        if override_set_text:
            self.separator_text = new_text
        self.song_separator.set_label(new_text)

    def playing_changed(self, status: GLib.Variant) -> None:
        if status.get_string() == "Playing":
            play_pause_icon = Gtk.Image.new_from_icon_name(
                "media-playback-pause-symbolic", Gtk.IconSize.MENU
            )
            self.play_pause_button.set_image(play_pause_icon)

        elif status.get_string() == "Paused":
            play_pause_icon = Gtk.Image.new_from_icon_name(
                "media-playback-start-symbolic", Gtk.IconSize.MENU
            )
            self.play_pause_button.set_image(play_pause_icon)

    def metadata_changed(self, metadata: GLib.Variant) -> None:
        self._set_song_label(
            metadata.lookup_value("xesam:artist", None),
            metadata.lookup_value("xesam:title", None),
        )
        self._set_album_cover(metadata.lookup_value("mpris:artUrl", None))

    def can_play_changed(self, metadata: GLib.Variant) -> None:
        self.can_play = metadata.get_boolean()
        self.play_pause_button.set_sensitive(self.can_play or self.can_pause)

    def can_pause_changed(self, metadata: GLib.Variant) -> None:
        self.can_pause = metadata.get_boolean()
        self.play_pause_button.set_sensitive(self.can_play or self.can_pause)

    def can_go_previous_changed(self, metadata: GLib.Variant) -> None:
        self.backward_button.set_sensitive(metadata.get_boolean())

    def can_go_next_changed(self, metadata: GLib.Variant) -> None:
        self.forward_button.set_sensitive(metadata.get_boolean())

    def play_paused_clicked(self, *args) -> None:
        self.dbus_player.call_player_method("PlayPause")

    def forward_clicked(self, *args) -> None:
        self.dbus_player.call_player_method("Next")

    def backward_clicked(self, *args) -> None:
        self.dbus_player.call_player_method("Previous")

    def song_clicked(self, *args) -> None:
        self.dbus_player.call_app_method("Raise")

    @staticmethod
    def _init_button(
        icon_name: str,
        on_pressed: Callable,
        icon_size: Gtk.IconSize = Gtk.IconSize.MENU,
        enabled: bool = True,
    ) -> Gtk.Button:
        icon = Gtk.Image.new_from_icon_name(icon_name, icon_size)
        button = Gtk.Button()
        button.set_image(icon)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_sensitive(enabled)
        button.connect("button-press-event", on_pressed)
        return button

    def _set_song_label(
        self, author: Optional[GLib.Variant], title: Optional[GLib.Variant]
    ) -> None:
        if title is None or (not title.get_string()):
            str_title = "Unknown"
            if (
                author is None
                or "".join(author.get_strv()).isspace()
                or "".join(author.get_strv()) == ""
            ):
                str_author = ""
                self.set_separator_text("", override_set_text=False)

            else:
                str_author = ", ".join(author.get_strv())
                self.set_separator_text(self.separator_text)

        else:
            str_title = title.unpack()
            if (
                author is None
                or "".join(author.get_strv()).isspace()
                or "".join(author.get_strv()) == ""
            ):
                str_author = ""
                self.set_separator_text("", override_set_text=False)

            else:
                str_author = ", ".join(author.get_strv())
                self.set_separator_text(self.separator_text)

        self.song_author.set_label(
            (str_author[: self.author_max_len - 3] + "...")
            if len(str_author) > self.author_max_len
            else str_author
        )

        self.song_name.set_label(
            (str_title[: self.name_max_len - 3] + "...")
            if len(str_title) > self.name_max_len
            else str_title
        )

    def _set_album_cover(self, art_url_variant: GLib.Variant) -> None:
        if art_url_variant is None:
            self._set_album_cover_other()
            return

        url = art_url_variant.get_string()

        if self.album_cover_data.image_url == url:
            return

        self.album_cover_data.image_url = url

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
        self.album_cover_data.song_cover = None
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
                    destop_icon = desktop_app_info.get_icon()
                    if destop_icon is not None:
                        self.album_cover.set_from_gicon(destop_icon, Gtk.IconSize.MENU)
                return

        self.album_cover.set_from_icon_name(
            "multimedia-player-symbolic", Gtk.IconSize.MENU
        )

    def _set_album_cover_file(self, parsed_url: ParseResult) -> None:
        try:
            if self.orientation == Gtk.Orientation.HORIZONTAL:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    parsed_url.path, -1, self.album_cover_size, True
                )
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    parsed_url.path, self.album_cover_size, -1, True
                )
            self.album_cover.set_from_pixbuf(pixbuf)
            self.album_cover_data.song_cover = pixbuf
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

        GLib.idle_add(self._set_album_cover_from_pixbuf, pixbuf)

    def _download_album_cover_image_to_gdkpixbuf(
        self, url: str, stop_event: threading.Event
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

        # calculating width/height based on height/width to have the same proportions
        if self.orientation == Gtk.Orientation.HORIZONTAL:
            resized_pixbuf = pixbuf.scale_simple(
                int((self.album_cover_size / pixbuf.get_height()) * pixbuf.get_width()),
                self.album_cover_size,
                GdkPixbuf.InterpType.NEAREST,
            )
        else:
            resized_pixbuf = pixbuf.scale_simple(
                self.album_cover_size,
                int((self.album_cover_size / pixbuf.get_width()) * pixbuf.get_height()),
                GdkPixbuf.InterpType.NEAREST,
            )

        if stop_event.is_set():
            return None

        return resized_pixbuf

    def _set_album_cover_from_pixbuf(self, pixbuf):
        self.album_cover.set_from_pixbuf(pixbuf)
        self.album_cover_data.song_cover = pixbuf
        return False
