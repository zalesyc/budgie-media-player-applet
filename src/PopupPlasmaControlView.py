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


from SingleAppPlayer import SingleAppPlayer
from AlbumCoverData import AlbumCoverType
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk, GdkPixbuf, GLib
from gi.repository.Pango import EllipsizeMode


class PopupPlasmaControlView(SingleAppPlayer):
    def __init__(
        self,
        service_name: str,
        orientation: Gtk.Orientation,
        author_max_len: int,
        name_max_len: int,
        separator_text: str,
        album_cover_size: int,
        open_popover_func: Callable,
    ):
        self.album_cover_size: int = album_cover_size

        self.timers_running: dict[int, bool] = {}
        self.main_layout_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.info_layout_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.info_layout_hbox.set_homogeneous(True)
        self.info_layout_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.controls_layout_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        progress_bar_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

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
        self.progress_label: Gtk.Label = Gtk.Label()
        self.progress_bar: Gtk.ProgressBar = Gtk.ProgressBar()

        self.position: int = 0
        """position of the media's playback in seconds"""

        SingleAppPlayer.__init__(
            self,
            service_name,
            open_popover_func,
            orientation,
            author_max_len,
            name_max_len,
            separator_text,
        )

        # album cover
        self.info_layout_hbox.pack_start(self.album_cover, False, False, 0)

        # song name label
        self.song_name_label.set_max_width_chars(1)
        self.song_name_label.set_hexpand(True)
        self.song_name_label.set_ellipsize(EllipsizeMode.END)
        self._set_title(self.title)
        self.info_layout_vbox.pack_start(self.song_name_label, False, False, 0)

        # song progress label
        progress_bar_layout.pack_start(self.progress_label, False, False, 4)

        # song progress bar
        self.progress_bar.set_valign(Gtk.Align.CENTER)
        self.progress_bar.set_show_text(False)
        progress_bar_layout.pack_start(self.progress_bar, True, True, 4)

        self._set_progress_label_and_bar()

        # song author label
        self.song_author_label.set_max_width_chars(1)
        self.song_author_label.set_hexpand(True)
        self.song_author_label.set_ellipsize(EllipsizeMode.END)
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

        self.set_hexpand(True)

        info_layout_event_box = Gtk.EventBox()
        info_layout_event_box.connect("button-press-event", self.song_info_clicked)
        info_layout_event_box.add(self.info_layout_hbox)

        self.info_layout_hbox.set_spacing(10)
        self.controls_layout_box.set_halign(Gtk.Align.CENTER)
        self.controls_layout_box.set_spacing(5)
        self.info_layout_vbox.set_valign(Gtk.Align.CENTER)

        self.info_layout_hbox.pack_start(self.info_layout_vbox, True, True, 0)
        self.main_layout_box.pack_start(info_layout_event_box, True, True, 10)
        self.main_layout_box.pack_start(progress_bar_layout, False, False, 5)
        self.main_layout_box.pack_start(self.controls_layout_box, False, False, 0)

        self.add(self.main_layout_box)

    def on_play_pause_pressed(self, *_):
        self.dbus_player.call_player_method("PlayPause")

    def previous_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Previous")

    def next_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Next")

    def song_info_clicked(self, *_) -> None:
        self.dbus_player.call_app_method("Raise")

    def set_popover_album_cover_size(self, new_size: int) -> None:
        self.album_cover_size = new_size
        self.album_cover_changed()

    # overridden parent method
    def popover_to_be_open(self):
        self._create_timer()

    def popover_just_closed(self):
        for key in self.timers_running:
            self.timers_running[key] = False

    # overridden parent method
    def metadata_changed(self) -> None:
        self._set_title(self.title)
        self.song_author_label.set_label(", ".join(self.artist))
        self._create_timer()

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
        if self.playing:
            self._create_timer()
        else:
            for key in self.timers_running:
                self.timers_running[key] = False

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
                            self.album_cover_size
                            / self.album_cover_data.song_cover_pixbuf.get_height()
                        )
                        * self.album_cover_data.song_cover_pixbuf.get_width()
                    ),
                    self.album_cover_size,
                    GdkPixbuf.InterpType.BILINEAR,
                )
            else:
                resized_pixbuf = self.album_cover_data.song_cover_pixbuf.scale_simple(
                    self.album_cover_size,
                    int(
                        (
                            self.album_cover_size
                            / self.album_cover_data.song_cover_pixbuf.get_width()
                        )
                        * self.album_cover_data.song_cover_pixbuf.get_height()
                    ),
                    GdkPixbuf.InterpType.BILINEAR,
                )
            self.album_cover.set_from_pixbuf(resized_pixbuf)

        elif self.album_cover_data.cover_type == AlbumCoverType.Gicon:
            self.album_cover.set_from_gicon(
                self.album_cover_data.song_cover_other,
                Gtk.IconSize.DIALOG,
            )

        elif self.album_cover_data.cover_type == AlbumCoverType.IconName:
            self.album_cover.set_from_icon_name(
                self.album_cover_data.song_cover_other,
                Gtk.IconSize.DIALOG,
            )

    def _create_timer(self):
        for key in self.timers_running:
            self.timers_running[key] = False

        self.dbus_player.get_player_property_non_cached(
            "Position", self._on_ready_callback
        )

    def _on_ready_callback(self, result: Optional[GLib.Variant]) -> None:
        if result is None:
            self.position = 0
            return

        data = result[0]
        self.position = round(data / 1_000_000)

        timer_id = 0
        while True:
            if timer_id not in self.timers_running:
                break
            elif timer_id > 50:
                # TODO: make tis log in logging framework
                print(
                    f"budgie-media-player: There are too many running timers, playerId: {self.service_name}, timers: {self.timers_running}"
                )
                return
            timer_id += 1

        self.timers_running.update({timer_id: True})
        GLib.timeout_add(
            round(1000 / self.rate), self._timer_updating_progress, timer_id
        )
        self._set_progress_label_and_bar()

    def _timer_updating_progress(self, identifier: int):
        if self.playing:
            self.position += 1
            self._set_progress_label_and_bar()

        status = self.timers_running[identifier]

        if not status:
            del self.timers_running[identifier]
            return False

        return True

    def _set_title(self, new_text: str):
        esc_text = GLib.markup_escape_text(new_text)
        self.song_name_label.set_markup(f"<b>{esc_text}</b>")

    def _set_progress_label_and_bar(self):
        len_mins, len_secs = divmod(self.song_length, 60)
        pos_mins, pos_secs = divmod(self.position, 60)
        self.progress_label.set_label(
            f"{pos_mins:02}:{pos_secs:02}/{len_mins:02}:{len_secs:02}"
        )
        self.progress_bar.set_fraction(
            self.position / self.song_length if self.song_length > 0 else 0
        )