# Copyright 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
from typing import Optional
from SingleAppPlayer import SingleAppPlayer

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
gi.require_version("Budgie", "1.0")
from gi.repository import Gtk, Gio, Budgie


class Popover(Budgie.Popover):
    def __init__(self, relative_to: Gtk.Widget, settings: Gio.Settings):
        super().__init__(relative_to=relative_to)
        self._nothing_is_playing_label: Optional[Gtk.Widget] = None

        self.connect("closed", self._on_closed)
        self.connect("show", self._on_showed)
        self.set_size_request(
            width=settings.get_uint("popover-width"),
            height=settings.get_uint("popover-height"),
        )
        settings.connect("changed", self._settings_changed)

        self._players_ntb = Gtk.Notebook(
            margin_start=5,
            margin_end=5,
            margin_bottom=5,
            show_border=False,
            scrollable=True,
        )
        self._players_ntb.connect("page-removed", self._on_page_removed)
        self._players_ntb.connect("page-added", self._on_page_added)
        self.add(self._players_ntb)
        self._on_page_removed()

    def add_player(self, player: SingleAppPlayer) -> None:
        self._players_ntb.append_page(child=player, tab_label=player.icon)
        self._players_ntb.show_all()

    def _on_showed(self, _) -> None:
        if self._nothing_is_playing_label is None:
            self._players_ntb.foreach(lambda player: player.popover_to_be_open())

    def _on_closed(self, _) -> None:
        if self._nothing_is_playing_label is None:
            self._players_ntb.foreach(lambda player: player.popover_just_closed())

    def _settings_changed(self, settings: Gio.Settings, changed_key: str) -> None:
        if changed_key in {"popover-width", "popover-height"}:
            self.set_size_request(
                width=settings.get_uint("popover-width"),
                height=settings.get_uint("popover-height"),
            )
            return

    def _on_page_removed(self, *_) -> None:
        if self._players_ntb.get_n_pages() < 1:
            self._nothing_is_playing_label = Gtk.Label(
                label='<span weight="bold">No apps are currently playing audio</span>',
                use_markup=True,
                wrap=True,
                max_width_chars=1,
                hexpand=True,
                vexpand=True,
            )
            self._players_ntb.append_page(
                self._nothing_is_playing_label,
                Gtk.Label(label=""),
            )
            self._players_ntb.show_all()

    def _on_page_added(self, *_) -> None:
        if (
            self._players_ntb.get_n_pages() > 1
            and self._nothing_is_playing_label is not None
        ):
            self._nothing_is_playing_label.destroy()
            self._nothing_is_playing_label = None
