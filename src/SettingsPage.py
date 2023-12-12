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

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Gio


class SettingsPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.set_column_spacing(10)
        self.set_row_spacing(10)

        self.settings: Gio.Settings = settings
        self.settings.connect("changed", self.settings_changed)

        self.max_len_title = Gtk.Label()
        self.max_len_title.set_markup("<b>Maximum Length of:</b>")
        self.max_len_title.set_halign(Gtk.Align.START)

        (
            self.name_max_len_label,
            self.name_max_len_spin_button,
        ) = self._combobox_label_init(
            "Media's title:",
            "Maximum length of the playing media's title (in characters)",
            "media-title-max-length",
        )
        self.name_max_len_spin_button.connect(
            "value_changed", self.name_max_len_spin_box_changed
        )

        (
            self.author_max_len_label,
            self.author_max_len_spin_button,
        ) = self._combobox_label_init(
            "Author's name:",
            "Maximum length of author's name (in characters)",
            "author-name-max-length",
        )
        self.author_max_len_spin_button.connect(
            "value_changed", self.author_max_len_spin_box_changed
        )

        self.attach(self.max_len_title, 0, 0, 2, 1)
        self.attach(self.name_max_len_label, 0, 1, 1, 1)
        self.attach(self.name_max_len_spin_button, 1, 1, 1, 1)
        self.attach(self.author_max_len_label, 0, 2, 1, 1)
        self.attach(self.author_max_len_spin_button, 1, 2, 1, 1)

        self.show_all()

    def name_max_len_spin_box_changed(self, widget):
        self.settings.set_int("media-title-max-length", widget.get_value_as_int())

    def author_max_len_spin_box_changed(self, widget):
        self.settings.set_int("author-name-max-length", widget.get_value_as_int())

    def settings_changed(self, settings, key):
        if key == "author-name-max-length":
            self.author_max_len_spin_button.set_value(self.settings.get_int(key))
            return

        if key == "media-title-max-length":
            self.name_max_len_spin_button.set_value(self.settings.get_int(key))
            return

    def _combobox_label_init(
        self, label_text, tooltip_text, spin_button_settings_property
    ):
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        label.set_tooltip_text(tooltip_text)
        spin_button = Gtk.SpinButton.new_with_range(5, 100, 1)
        spin_button.set_value(self.settings.get_int(spin_button_settings_property))
        return label, spin_button
