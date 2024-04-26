#    budgie-media-player-applet
#    Copyright (C) 2024 Alex Cizinsky
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


from AlbumCoverData import AlbumCoverType, AlbumCoverData
from mprisWrapper import MprisWrapper
from dataclasses import dataclass
from typing import Optional, Callable
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf


@dataclass
class Element:
    widget: Gtk.Widget
    spacing: int


class PanelControlView(Gtk.Box):
    def __init__(
        self,
        dbus_player: MprisWrapper,
        title: str,
        artist: list[str],
        playing: bool,
        can_play_or_pause: bool,
        can_go_previous: bool,
        can_go_next: bool,
        open_popover_func: Callable,
    ):
        # TO BE FROM CONSTRUCTOR
        element_order = [
            "album_cover",
            "song_author",
            "song_separator",
            "song_name",
            "backward_button",
            "play_pause_button",
            "forward_button",
        ]

        Gtk.Box.__init__(self)
        self.dbus_player = dbus_player
        self.album_cover_size: int = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.open_popover_func = open_popover_func
        self.orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL
        self.author_max_len: int = 20
        self.name_max_len: int = 20
        self.separator_text: str = "-"

        self.album_cover: Gtk.Image = Gtk.Image.new_from_icon_name(
            "action-unavailable-symbolic", Gtk.IconSize.MENU
        )
        self.song_name_label: Gtk.Label = Gtk.Label()
        self.song_author_label: Gtk.Label = Gtk.Label()
        self.song_separator: Gtk.Label = Gtk.Label()
        self.play_pause_button: Gtk.Button = Gtk.Button()
        self.go_previous_button: Gtk.Button = Gtk.Button()
        self.go_next_button: Gtk.Button = Gtk.Button()

        self.available_elements: dict[str, Element] = {}

        # albumCover
        album_cover_event_box = Gtk.EventBox()
        album_cover_event_box.add(self.album_cover)
        album_cover_event_box.connect("button-press-event", self.song_clicked)
        self.available_elements.update(
            {"album_cover": Element(album_cover_event_box, 5)}
        )

        # song_name
        song_name_event_box = Gtk.EventBox()
        song_name_event_box.add(self.song_name_label)
        song_name_event_box.connect("button-press-event", self.song_clicked)
        self.available_elements.update({"song_name": Element(song_name_event_box, 4)})

        # song_author
        song_author_event_box = Gtk.EventBox()
        song_author_event_box.add(self.song_author_label)
        song_author_event_box.connect("button-press-event", self.song_clicked)
        self.available_elements.update(
            {"song_author": Element(song_author_event_box, 4)}
        )

        # song_separator
        self.song_separator.set_label(self.separator_text)
        self.available_elements.update(
            {"song_separator": Element(self.song_separator, 4)}
        )

        self._set_song_label(title=title, author=artist)

        # play pause button
        self.play_pause_button.set_image(
            Gtk.Image.new_from_icon_name(
                (
                    "media-playback-pause-symbolic"
                    if playing
                    else "media-playback-start-symbolic"
                ),
                Gtk.IconSize.MENU,
            )
        )
        self.play_pause_button.set_relief(Gtk.ReliefStyle.NONE)
        self.play_pause_button.set_sensitive(can_play_or_pause)
        self.play_pause_button.connect("button-press-event", self.play_paused_clicked)
        self.available_elements.update(
            {"play_pause_button": Element(self.play_pause_button, 0)}
        )

        # backward_button
        self.go_previous_button.set_image(
            Gtk.Image.new_from_icon_name(
                "media-skip-backward-symbolic", Gtk.IconSize.MENU
            )
        )
        self.go_previous_button.set_relief(Gtk.ReliefStyle.NONE)
        self.go_previous_button.set_sensitive(can_go_previous)
        self.go_previous_button.connect("button-press-event", self.forward_clicked)
        self.available_elements.update(
            {"backward_button": Element(self.go_previous_button, 0)}
        )

        # forward_button
        self.go_next_button.set_image(
            Gtk.Image.new_from_icon_name(
                "media-skip-forward-symbolic", Gtk.IconSize.MENU
            )
        )
        self.go_next_button.set_relief(Gtk.ReliefStyle.NONE)
        self.go_next_button.set_sensitive(can_go_next)
        self.go_next_button.connect("button-press-event", self.forward_clicked)
        self.available_elements.update(
            {"forward_button": Element(self.go_next_button, 0)}
        )

        self.set_element_order(element_order, remove_previous=False)
        self.show_all()

    # overridden parent method
    def set_orientation(self, new_orientation: Gtk.Orientation) -> None:
        self.orientation = new_orientation
        angle = 0 if new_orientation == Gtk.Orientation.HORIZONTAL else 270
        self.song_name_label.set_angle(angle)
        self.song_author_label.set_angle(angle)
        self.song_separator.set_angle(angle)
        super().set_orientation(new_orientation)

    def set_separator_text(self, new_text: str, override_set_text: bool = True) -> None:
        if override_set_text:
            self.separator_text = new_text
        self.song_separator.set_label(new_text)

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

    # overridden parent method
    def panel_size_changed(
        self, new_size: int, album_cover_data: AlbumCoverData
    ) -> None:
        self.album_cover_size = new_size
        self.set_album_cover(album_cover_data)

    def play_paused_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("PlayPause")

    def forward_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Next")

    def backward_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Previous")

    def song_clicked(self, *_) -> None:
        self.open_popover_func()

    # overridden parent method
    def set_playing(self, playing: bool) -> None:
        self.play_pause_button.set_image(
            Gtk.Image.new_from_icon_name(
                (
                    "media-playback-pause-symbolic"
                    if playing
                    else "media-playback-start-symbolic"
                ),
                Gtk.IconSize.MENU,
            )
        )

    def set_metadata(self, artist: list[str], title: str) -> None:
        self._set_song_label(artist, title)

    def set_can_play_or_pause(self, can_play_or_pause: bool) -> None:
        self.play_pause_button.set_sensitive(can_play_or_pause)

    # overridden parent method
    def set_can_go_previous(self, can_go_previous: bool) -> None:
        self.go_previous_button.set_sensitive(can_go_previous)

    # overridden parent method
    def set_can_go_next_changed(self, can_go_next: bool) -> None:
        self.go_next_button.set_sensitive(can_go_next)

    # overridden parent method
    def set_album_cover(self, data: AlbumCoverData) -> None:
        if data.cover_type == AlbumCoverType.Pixbuf:
            if self.orientation == Gtk.Orientation.HORIZONTAL:
                resized_pixbuf = data.song_cover_pixbuf.scale_simple(
                    int(
                        (self.album_cover_size / data.song_cover_pixbuf.get_height())
                        * data.song_cover_pixbuf.get_width()
                    ),
                    self.album_cover_size,
                    GdkPixbuf.InterpType.BILINEAR,
                )
            else:
                resized_pixbuf = data.song_cover_pixbuf.scale_simple(
                    self.album_cover_size,
                    int(
                        (self.album_cover_size / data.song_cover_pixbuf.get_width())
                        * data.song_cover_pixbuf.get_height()
                    ),
                    GdkPixbuf.InterpType.BILINEAR,
                )
            self.album_cover.set_from_pixbuf(resized_pixbuf)

        elif data.cover_type == AlbumCoverType.Gicon:
            self.album_cover.set_from_gicon(
                data.song_cover_other, self.album_cover_size
            )

        elif data.cover_type == AlbumCoverType.IconName:
            self.album_cover.set_from_icon_name(
                data.song_cover_other,
                min(Gtk.IconSize.lookup(Gtk.IconSize.DND)[2], self.album_cover_size),
            )

    def _set_song_label(
        self, author: Optional[list[str]], title: Optional[str]
    ) -> None:

        if title is None:
            str_title = "Unknown"
            if author is None or "".join(author).isspace() or "".join(author) == "":
                str_author = ""
                self.set_separator_text("", override_set_text=False)

            else:
                str_author = ", ".join(author)
                self.set_separator_text(self.separator_text)

        else:
            str_title = title
            if author is None or "".join(author).isspace() or "".join(author) == "":
                str_author = ""
                self.set_separator_text("", override_set_text=False)

            else:
                str_author = ", ".join(author)
                self.set_separator_text(self.separator_text)

        self.song_author_label.set_label(
            (str_author[: self.author_max_len - 3] + "...")
            if len(str_author) > self.author_max_len
            else str_author
        )

        self.song_name_label.set_label(
            (str_title[: self.name_max_len - 3] + "...")
            if len(str_title) > self.name_max_len
            else str_title
        )
