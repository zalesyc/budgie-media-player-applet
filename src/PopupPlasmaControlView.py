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


from SingleAppPlayer import SingleAppPlayer, AlbumCoverType
from PopupStyle import PopupStyle
from typing import Callable, Optional
from PanelControlView import PanelControlView
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf


class PopupPlasmaControlView(SingleAppPlayer):
    ALBUM_COVER_SIZE = 96

    def __init__(
        self,
        service_name: str,
        orientation: Gtk.Orientation,
        author_max_len: int,
        name_max_len: int,
        element_order: list[str],
        separator_text: str,
        style: PopupStyle,
        open_popover_func: Callable,
    ):
        self.album_cover_size: int = Gtk.IconSize.lookup(Gtk.IconSize.DND)[2]
        self.orientation: Gtk.Orientation = orientation
        self.author_max_len: int = author_max_len
        self.name_max_len: int = name_max_len
        self.separator_text: str = separator_text
        self.service_name: str = service_name

        self.orientation = Gtk.Orientation.HORIZONTAL  # TODO: get from appplet
        self._panel_view: Optional[PanelControlView] = None

        self.main_layout_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.info_layout_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.info_layout_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.controls_layout_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.album_cover: Gtk.Image = Gtk.Image.new_from_icon_name(
            "action-unavailable-symbolic", Gtk.IconSize.DIALOG
        )
        self.song_name_label: Gtk.Label = Gtk.Label()
        self.song_author_label: Gtk.Label = Gtk.Label()
        self.song_author_label: Gtk.Label = Gtk.Label()
        self.song_separator: Gtk.Label = Gtk.Label()
        self.play_pause_button: Gtk.Button = Gtk.Button()
        self.go_previous_button: Gtk.Button = Gtk.Button()
        self.go_next_button: Gtk.Button = Gtk.Button()

        SingleAppPlayer.__init__(
            self,
            service_name,
            style,
            open_popover_func,
        )

        # album cover
        self.info_layout_hbox.pack_start(self.album_cover, False, False, 0)

        # song name label
        self.song_name_label.set_markup(f"<b>{self.title}</b>")
        self.info_layout_vbox.pack_start(self.song_name_label, False, False, 0)

        # song author label
        self.song_author_label.set_label(", ".join(self.artist))
        self.info_layout_vbox.pack_start(self.song_author_label, False, False, 0)

        # go previous btn
        self.go_previous_button.set_image(
            Gtk.Image.new_from_icon_name(
                "media-skip-backward-symbolic", Gtk.IconSize.MENU
            )
        )
        self.go_previous_button.set_relief(Gtk.ReliefStyle.NONE)
        self.go_previous_button.set_sensitive(self.can_go_previous)
        self.go_previous_button.connect("pressed", self.previous_clicked)
        self.controls_layout_box.pack_start(self.go_previous_button, False, False, 0)

        # play pause btn
        self.play_pause_button.set_image(
            Gtk.Image.new_from_icon_name(
                (
                    "media-playback-pause-symbolic"
                    if self.playing
                    else "media-playback-start-symbolic"
                ),
                Gtk.IconSize.MENU,
            )
        )
        self.play_pause_button.set_relief(Gtk.ReliefStyle.NONE)
        self.play_pause_button.set_sensitive(self.can_pause or self.can_play)
        self.play_pause_button.connect("pressed", self.on_play_pause_pressed)
        self.controls_layout_box.pack_start(self.play_pause_button, False, False, 0)

        # go next btn
        self.go_next_button.set_image(
            Gtk.Image.new_from_icon_name(
                "media-skip-forward-symbolic", Gtk.IconSize.MENU
            )
        )
        self.go_next_button.set_relief(Gtk.ReliefStyle.NONE)
        self.go_next_button.set_sensitive(self.can_go_next)
        self.go_next_button.connect("pressed", self.next_clicked)
        self.controls_layout_box.pack_start(self.go_next_button, False, False, 0)

        info_layout_event_box = Gtk.EventBox()
        info_layout_event_box.connect("button-press-event", self.song_info_clicked)
        self.main_layout_box.set_halign(Gtk.Align.CENTER)
        self.info_layout_hbox.set_spacing(10)
        self.info_layout_vbox.set_halign(Gtk.Align.START)
        self.info_layout_vbox.set_valign(Gtk.Align.CENTER)
        self.info_layout_hbox.pack_start(self.info_layout_vbox, False, False, 0)
        info_layout_event_box.add(self.info_layout_hbox)
        self.main_layout_box.pack_start(info_layout_event_box, True, True, 10)
        self.controls_layout_box.set_halign(Gtk.Align.CENTER)
        self.controls_layout_box.set_spacing(5)
        self.main_layout_box.pack_start(self.controls_layout_box, False, False, 0)
        self.add(self.main_layout_box)

    def add_panel_view(self) -> None:
        self._panel_view = PanelControlView(
            self.service_name,
            self.orientation,
            self.author_max_len,
            self.name_max_len,
            [],
            self.separator_text,
            self.open_popover_func,
        )

    def get_panel_view(self) -> Optional[PanelControlView]:
        return self._panel_view

    def on_play_pause_pressed(self, *_):
        self.dbus_player.call_player_method("PlayPause")

    def previous_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Previous")

    def next_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Next")

    def song_info_clicked(self, *_) -> None:
        self.dbus_player.call_app_method("Raise")

    # overridden parent method
    def metadata_changed(self) -> None:
        self.song_name_label.set_markup(f"<b>{self.title}</b>")
        self.song_author_label.set_label(", ".join(self.artist))

    # overridden parent method
    def can_play_changed(self) -> None:
        if self.can_play or self.can_pause:
            self.play_pause_button.set_sensitive(True)
        else:
            self.play_pause_button.set_sensitive(False)

    # overridden parent method
    def can_pause_changed(self) -> None:
        if self.can_play or self.can_pause:
            self.play_pause_button.set_sensitive(True)
        else:
            self.play_pause_button.set_sensitive(False)

    # overridden parent method
    def can_go_previous_changed(self) -> None:
        self.go_previous_button.set_sensitive(self.can_go_previous)

    # overridden parent method
    def can_go_next_changed(self) -> None:
        self.go_next_button.set_sensitive(self.can_go_next)

    # overridden parent method
    def playing_changed(self) -> None:
        self.play_pause_button.set_image(
            Gtk.Image.new_from_icon_name(
                (
                    "media-playback-pause-symbolic"
                    if self.playing
                    else "media-playback-start-symbolic"
                ),
                Gtk.IconSize.MENU,
            )
        )

    # overridden parent method
    def album_cover_changed(self) -> None:
        if self.album_cover_data.cover_type == AlbumCoverType.Pixbuf:
            if (
                self.album_cover_data.song_cover_pixbuf.get_width()
                < self.album_cover_data.song_cover_pixbuf.get_height()
            ):
                resized_pixbuf = self.album_cover_data.song_cover_pixbuf.scale_simple(
                    int(
                        (
                            self.ALBUM_COVER_SIZE
                            / self.album_cover_data.song_cover_pixbuf.get_height()
                        )
                        * self.album_cover_data.song_cover_pixbuf.get_width()
                    ),
                    self.ALBUM_COVER_SIZE,
                    GdkPixbuf.InterpType.BILINEAR,
                )
            else:
                resized_pixbuf = self.album_cover_data.song_cover_pixbuf.scale_simple(
                    self.ALBUM_COVER_SIZE,
                    int(
                        (
                            self.ALBUM_COVER_SIZE
                            / self.album_cover_data.song_cover_pixbuf.get_width()
                        )
                        * self.album_cover_data.song_cover_pixbuf.get_height()
                    ),
                    GdkPixbuf.InterpType.BILINEAR,
                )
            self.album_cover.set_from_pixbuf(resized_pixbuf)

        elif self.album_cover_data.cover_type == AlbumCoverType.Gicon:
            self.album_cover.set_from_gicon(
                self.album_cover_data.song_cover_other, self.ALBUM_COVER_SIZE
            )

        elif self.album_cover_data.cover_type == AlbumCoverType.IconName:
            self.album_cover.set_from_icon_name(
                self.album_cover_data.song_cover_other,
                self.ALBUM_COVER_SIZE,
            )
