# Copyright 2024 - 2025, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from SingleAppPlayer import SingleAppPlayer
from EnumsStructs import AlbumCoverType
from Labels import ScrollingLabel, ElliptedLabel
from typing import Callable, Optional, Union
from enum import IntEnum
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, GLib, Gio, Gdk


class TextStyle(IntEnum):
    ellipsis = 0
    scroll = 1

    @classmethod
    def insert(cls, value: int, default: Optional[int] = None):
        values = list(map(int, cls))
        if value in values:
            return cls(value)

        if default in values:
            return cls(default)

        return cls(values[0])


class PopupPlasmaControlView(SingleAppPlayer):
    def __init__(
        self,
        service_name: str,
        open_popover_func: Callable[[], None],
        on_pin_clicked: Callable[[str], None],
        settings: Gio.Settings,
    ):
        self.album_cover_size: float = settings.get_double(
            "popover-album-cover-size"
        )  # this is a portion of the available space
        self.text_style: TextStyle = TextStyle.insert(
            settings.get_uint("plasma-popover-text-style"),
            default=TextStyle.ellipsis,
        )
        settings.connect("changed", self.settings_changed)

        self.timers_running: dict[int, bool] = {}
        self.popover_open: bool = False
        self.scrolling_text_value: float = 0.0
        self.main_layout_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.info_layout_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.info_layout_hbox.set_homogeneous(True)
        self.info_layout_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.controls_layout_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        progress_bar_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.album_cover: Gtk.Image = Gtk.Image.new_from_icon_name(
            "emblem-music-symbolic", Gtk.IconSize.DIALOG
        )
        self.song_name_label: Union[ScrollingLabel, ElliptedLabel] = (
            ScrollingLabel() if self.text_style == TextStyle.scroll else ElliptedLabel()
        )
        self.song_author_label: Union[ScrollingLabel, ElliptedLabel] = (
            ScrollingLabel() if self.text_style == TextStyle.scroll else ElliptedLabel()
        )
        self.song_separator: Gtk.Label = Gtk.Label()
        self.play_pause_button: Gtk.Button = Gtk.Button()
        self.go_previous_button: Gtk.Button = Gtk.Button()
        self.go_next_button: Gtk.Button = Gtk.Button()
        self.pin_button: Gtk.Button = Gtk.Button()
        self.progress_label: Gtk.Label = Gtk.Label()
        self.progress_bar: Gtk.ProgressBar = Gtk.ProgressBar()

        self.position: int = 0
        """position of the media's playback in seconds"""

        SingleAppPlayer.__init__(
            self,
            service_name=service_name,
            open_popover_func=open_popover_func,
            on_pin_clicked=on_pin_clicked,
            settings=settings,
        )

        # album cover
        self._should_set_album_cover = False
        self.album_cover.connect("size-allocate", self._on_album_cover_size_allocate)
        self.info_layout_hbox.pack_start(self.album_cover, True, True, 0)

        # song name label
        song_name_size = settings.get_int("plasma-popover-media-name-size")
        self.song_name_label.set_text_size(
            None if song_name_size < 0 else song_name_size
        )
        if self.text_style == TextStyle.scroll:
            speed = settings.get_double("plasma-popover-media-name-scrolling-speed")
            self.song_name_label.set_speed(speed)

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
        author_name_size = settings.get_int("plasma-popover-media-author-size")
        self.song_author_label.set_text_size(
            None if author_name_size < 0 else author_name_size
        )
        if self.text_style == TextStyle.scroll:
            speed = settings.get_double("plasma-popover-media-author-scrolling-speed")
            self.song_author_label.set_speed(speed)
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
        self.go_previous_button.set_tooltip_text("Go to the previous song / media")
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
        self.play_pause_button.set_tooltip_text("Play / Pause")
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
        self.go_next_button.set_tooltip_text("Go to the next song / media")
        self.controls_layout_box.pack_start(self.go_next_button, False, False, 0)

        # pin button
        self.pin_button.set_image(
            Gtk.Image.new_from_icon_name(
                "budgie-media-player-applet-unpinned-symbolic",
                Gtk.IconSize.MENU,
            )
        )
        self.pin_button.set_relief(Gtk.ReliefStyle.NONE)
        self.pin_button.connect("pressed", self.pin_clicked)
        self.pin_button.set_tooltip_markup(
            "<b>Pin / unpin the player</b>, the pinned player is shown in the panel"
        )
        self.controls_layout_box.pack_start(self.pin_button, False, False, 0)

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

    def on_play_pause_pressed(self, *_) -> None:
        self.dbus_player.call_player_method("PlayPause")

    def previous_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Previous")

    def next_clicked(self, *_) -> None:
        self.dbus_player.call_player_method("Next")

    def song_info_clicked(self, *_) -> None:
        self.dbus_player.call_app_method("Raise")

    def pin_clicked(self, *_) -> None:
        self.on_pin_clicked(self.service_name)

    # overridden parent method
    def popover_to_be_open(self) -> None:
        self.popover_open = True
        if self.text_style == TextStyle.scroll:
            self.song_name_label.to_get_visible()
            self.song_author_label.to_get_visible()
        self._create_timer()

    def popover_just_closed(self) -> None:
        self.popover_open = False
        if self.text_style == TextStyle.scroll:
            self.song_name_label.to_get_invisible()
            self.song_author_label.to_get_invisible()
        for key in self.timers_running:
            self.timers_running[key] = False

    def pinned_changed(self) -> None:
        self.pin_button.set_image(
            Gtk.Image.new_from_icon_name(
                (
                    "budgie-media-player-applet-unpinned-symbolic"
                    if self.panel_view is None
                    else "budgie-media-player-applet-pinned-symbolic"
                ),
                Gtk.IconSize.MENU,
            )
        )

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
    def album_cover_changed(self, wait_for_allocation: bool = False) -> None:
        """
        wait_for_allocation is used when the popover size changes from settings,
        it adjusts the album_cover size within the size-allocate signal. This is
        necessary because if the popover size is reduced, the album cover would still be
        expanding the popover, leading to larger get_allocated_width() and height
        values thus setting the album cover size larger, again expanding the popover.
        """
        if self.album_cover_data.cover_type == AlbumCoverType.Pixbuf:
            allocated_width = self.album_cover.get_allocated_width()
            allocated_height = self.album_cover.get_allocated_height()
            if allocated_width <= 1 or allocated_height <= 1 or wait_for_allocation:
                # wait for allocation in the size-allocate signal
                self._should_set_album_cover = True

                if wait_for_allocation:
                    self.album_cover.clear()
            else:
                self.album_cover.set_from_pixbuf(
                    self._get_resized_pixbuf(
                        allocated_height,
                        allocated_width,
                        self.album_cover_size,
                    )
                )

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

    def settings_changed(self, settings: Gio.Settings, changed_key: str) -> None:
        if changed_key == "popover-album-cover-size":
            self.album_cover_size = self.settings.get_double("popover-album-cover-size")
            self.album_cover_changed()
            return

        if changed_key in {"popover-width", "popover-height"}:
            self.album_cover_changed(wait_for_allocation=True)
            return

        if changed_key == "plasma-popover-text-style":
            style = TextStyle.insert(settings.get_uint("plasma-popover-text-style"))
            if style == self.text_style:
                return
            self.text_style = style
            self.song_name_label.destroy()
            self.song_author_label.destroy()
            if self.text_style == TextStyle.scroll:
                self.song_name_label = ScrollingLabel()
                self.song_author_label = ScrollingLabel()
            else:
                self.song_name_label = ElliptedLabel()
                self.song_author_label = ElliptedLabel()

            self.info_layout_vbox.pack_start(self.song_name_label, False, False, 0)
            self.info_layout_vbox.pack_start(self.song_author_label, False, False, 0)
            self.info_layout_vbox.show_all()

            name_size = settings.get_int("plasma-popover-media-name-size")
            author_size = settings.get_int("plasma-popover-media-author-size")
            self.song_name_label.set_text_size(None if name_size < 0 else name_size)
            self.song_author_label.set_text_size(
                None if author_size < 0 else author_size
            )

            self._set_title(self.title)
            self.song_author_label.set_label(", ".join(self.artist))
            return

        if changed_key == "plasma-popover-media-name-size":
            size = settings.get_int("plasma-popover-media-name-size")
            self.song_name_label.set_text_size(None if size < 0 else size)
            return

        if changed_key == "plasma-popover-media-author-size":
            size = settings.get_int("plasma-popover-media-author-size")
            self.song_author_label.set_text_size(None if size < 0 else size)
            return

        if changed_key == "plasma-popover-media-name-scrolling-speed":
            if self.text_style != TextStyle.scroll:
                return
            speed = settings.get_double("plasma-popover-media-name-scrolling-speed")
            self.song_name_label.set_speed(speed)
            return

        if changed_key == "plasma-popover-media-author-scrolling-speed":
            if self.text_style != TextStyle.scroll:
                return
            speed = settings.get_double("plasma-popover-media-author-scrolling-speed")
            self.song_author_label.set_speed(speed)
            return

    def _on_album_cover_size_allocate(self, _, rect: Gdk.Rectangle) -> None:
        if not self._should_set_album_cover:
            return
        self._should_set_album_cover = False

        self.album_cover.set_from_pixbuf(
            self._get_resized_pixbuf(rect.height, rect.width, self.album_cover_size)
        )

    def _create_timer(self) -> None:
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
                print(
                    "budgie-media-player-applet: There are too many running timers, "
                    f"playerId: {self.service_name}, timers: {self.timers_running}"
                )
                return
            timer_id += 1

        self.timers_running.update({timer_id: True})
        if self.rate > 0:
            GLib.timeout_add(
                round(1000 / self.rate), self._timer_updating_progress, timer_id
            )
        self._set_progress_label_and_bar()

    def _timer_updating_progress(self, identifier: int) -> bool:
        if self.playing:
            self.position += 1
            self._set_progress_label_and_bar()

        status = self.timers_running[identifier]

        if not status:
            del self.timers_running[identifier]
            return False

        return True

    def _set_title(self, new_text: str) -> None:
        esc_text = GLib.markup_escape_text(new_text)
        self.song_name_label.set_markup(f"<b>{esc_text}</b>")

    def _set_progress_label_and_bar(self) -> None:
        len_mins, len_secs = divmod(self.song_length, 60)
        pos_mins, pos_secs = divmod(self.position, 60)
        self.progress_label.set_label(
            f"{pos_mins:02}:{pos_secs:02}/{len_mins:02}:{len_secs:02}"
        )
        self.progress_bar.set_fraction(
            self.position / self.song_length if self.song_length > 0 else 0
        )
