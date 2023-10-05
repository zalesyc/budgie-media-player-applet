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

from urllib.parse import urlparse
import requests
from PIL import Image
from io import BytesIO

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf

from mprisWrapper import MprisWrapper


class SingleAppPlayer(Gtk.Box):
    def __init__(self, service_name: str):
        self.album_cover_height: int = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]

        Gtk.Box.__init__(self, spacing=0)
        self.service_name = service_name

        self.dbus_player = MprisWrapper(self.service_name)
        self.dbus_player.player_connect("PlaybackStatus", self.playing_changed)
        self.dbus_player.player_connect("Metadata", self.metadata_changed)

        start_song_metadata = self.dbus_player.get_player_property("Metadata")

        # album_cover
        self.album_cover = Gtk.Image.new_from_icon_name(
            "action-unavailable-symbolic", Gtk.IconSize.MENU
        )
        album_cover_event_box = Gtk.EventBox()
        album_cover_event_box.add(self.album_cover)
        album_cover_event_box.connect("button-press-event", self.song_clicked)
        self._set_album_cover(start_song_metadata.lookup_value("mpris:artUrl", None))

        # song_text
        self.song_text = Gtk.Label()
        self._set_song_label(
            start_song_metadata.lookup_value("xesam:artist", None),
            start_song_metadata.lookup_value("xesam:title", None),
        )
        song_text_event_box = Gtk.EventBox()
        song_text_event_box.add(self.song_text)
        song_text_event_box.connect("button-press-event", self.song_clicked)

        # control buttons
        play_pause_icon = Gtk.Image()
        if (
            self.dbus_player.get_player_property("PlaybackStatus").get_string()
            == "Playing"
        ):
            self.play_pause_button = self._init_button(
                "media-playback-pause-symbolic", self.play_paused_clicked
            )

        else:
            self.play_pause_button = self._init_button(
                "media-playback-start-symbolic", self.play_paused_clicked
            )

        self.backward_button = self._init_button(
            "media-skip-backward-symbolic", self.backward_clicked
        )
        self.forward_button = self._init_button(
            "media-skip-forward-symbolic", self.forward_clicked
        )

        # add all widgets
        self.pack_start(album_cover_event_box, False, False, 5)
        self.pack_start(song_text_event_box, True, True, 5)
        self.pack_end(self.forward_button, False, False, 0)
        self.pack_end(self.play_pause_button, False, False, 0)
        self.pack_end(self.backward_button, False, False, 0)

        self.show_all()

    def playing_changed(self, status: GLib.Variant):
        if status.get_string() == "Playing":
            play_pause_icon = Gtk.Image.new_from_icon_name(
                "media-playback-pause-symbolic", Gtk.IconSize.MENU
            )
        elif status.get_string() == "Paused":
            play_pause_icon = Gtk.Image.new_from_icon_name(
                "media-playback-start-symbolic", Gtk.IconSize.MENU
            )
        self.play_pause_button.set_image(play_pause_icon)

    def metadata_changed(self, metadata: GLib.Variant):
        self._set_song_label(
            metadata.lookup_value("xesam:artist", None),
            metadata.lookup_value("xesam:title", None),
        )
        self._set_album_cover(metadata.lookup_value("mpris:artUrl", None))

    def play_paused_clicked(self, *args):
        self.dbus_player.call_player_method("PlayPause")

    def forward_clicked(self, *args):
        self.dbus_player.call_player_method("Next")

    def backward_clicked(self, *args):
        self.dbus_player.call_player_method("Previous")

    def song_clicked(self, *args):
        self.dbus_player.call_app_method("Raise")

    def _init_button(self, icon_name: str, on_pressed: callable, icon_size: Gtk.IconSize = Gtk.IconSize.MENU) -> Gtk.Button:
        icon = Gtk.Image.new_from_icon_name(icon_name, icon_size)
        button = Gtk.Button()
        button.set_image(icon)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect("button-press-event", on_pressed)
        return button

    def _set_song_label(self, author, title):
        if author is None:
            author = ""
        else:
            author = author.unpack()
            if len(author) == 0:
                author = ""
            else:
                author = author[0]

        if title is None:
            title = ""
        else:
            title = title.unpack()

        if title == "":
            if author == "":
                song_text = "Unknown"
            else:
                song_text = f"{author} - Unknown"
        else:
            if author == "":
                song_text = f"{title}"
            else:
                song_text = f"{author} - {title}"

        self.song_text.set_label(song_text)

    def _set_album_cover(self, art_url):
        if art_url is None:
            self._set_album_cover_other()
            return

        url = art_url.get_string()
        parsed_url = urlparse(url)
        if parsed_url.scheme == "file":
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    parsed_url.path, -1, self.album_cover_height, True
                )
                self.album_cover.set_from_pixbuf(pixbuf)
            except gi.repository.GLib.GError:
                self._set_album_cover_other()

        elif parsed_url.scheme == "https":
            self._set_album_cover_https(url)

        else:
            self._set_album_cover_other()

    def _set_album_cover_other(self):
        desktop_file_name = self.dbus_player.get_app_property("DesktopEntry")
        if desktop_file_name is not None:
            desktop_file_name = desktop_file_name.get_string()
            try:
                desktop_app_info = Gio.DesktopAppInfo.new(
                    desktop_file_name + ".desktop"
                )
            except TypeError:
                pass
            else:
                self.album_cover.set_from_gicon(
                    desktop_app_info.get_icon(), Gtk.IconSize.MENU
                )
                return

        self.album_cover.set_from_icon_name(
            "applications-community-symbolic", Gtk.IconSize.MENU
        )

    def _set_album_cover_https(self, url):
        pixbuf = self._stream_image_to_gdkpixbuf(url)

        if pixbuf:
            self.album_cover.set_from_pixbuf(
                pixbuf.scale_simple(
                    int(
                        (self.album_cover_height / pixbuf.get_height())
                        * pixbuf.get_width()
                    ),  # calculating width based on height to have the same proportions
                    self.album_cover_height,
                    GdkPixbuf.InterpType.NEAREST,
                )
            )
        else:
            self._set_album_cover_other()

    def _stream_image_to_gdkpixbuf(self, url):
        try:
            # Send a GET request to the URL
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return None

            # Read the image data in chunks
            img_data = BytesIO()
            for chunk in response.iter_content(chunk_size=1024):
                img_data.write(chunk)

            # Rewind the buffer and open as an image with Pillow
            img_data.seek(0)
            pil_image = Image.open(img_data)

            # Convert the Pillow image to a GdkPixbuf
            gdkpixbuf = GdkPixbuf.Pixbuf.new_from_data(
                pil_image.tobytes(),  # Image data as bytes
                GdkPixbuf.Colorspace.RGB,
                False,
                8,  # Bits per sample
                pil_image.width,
                pil_image.height,
                pil_image.width * 3,  # Rowstride
            )

            return gdkpixbuf
        except Exception:
            return None
