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


class SettingsPage(Gtk.Box):
    def __init__(self, settings: Gio.Settings):
        self.settings = settings
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=15)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(100)

        self.stack.add_titled(MainPage(settings), "main_page", "Main")
        self.stack.add_titled(OrderPage(settings), "order_page", "Order")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(self.stack)

        self.pack_start(stack_switcher, False, False, 0)
        self.pack_start(self.stack, True, True, 0)

        self.show_all()


class MainPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.set_column_spacing(10)
        self.set_row_spacing(10)

        self.settings: Gio.Settings = settings
        if settings is not None:
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
        if self.settings is None:
            spin_button.set_value(3)
        else:
            spin_button.set_value(self.settings.get_int(spin_button_settings_property))

        return label, spin_button


class OrderPage(Gtk.Box):
    def __init__(self, settings: Gio.Settings):
        self.settings = settings
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.left_box = Gtk.ListBox()
        self.left_box.set_selection_mode(Gtk.SelectionMode.SINGLE)

        middle_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.right_box = Gtk.ListBox()
        self.right_box.set_property("selection-mode", Gtk.SelectionMode.SINGLE)

        self.add_button = Gtk.Button.new_from_icon_name(
            "arrow-right", Gtk.IconSize.BUTTON
        )
        self.add_button.connect("clicked", self._on_add_clicked)

        self.remove_button = Gtk.Button.new_from_icon_name(
            "arrow-left", Gtk.IconSize.BUTTON
        )
        self.remove_button.connect("clicked", self._on_remove_clicked)

        self.move_up_button = Gtk.Button.new_from_icon_name(
            "arrow-up", Gtk.IconSize.BUTTON
        )
        self.move_up_button.connect("clicked", self._on_move_up_clicked)

        self.move_down_button = Gtk.Button.new_from_icon_name(
            "arrow-down", Gtk.IconSize.BUTTON
        )
        self.move_down_button.connect("clicked", self._on_move_down_clicked)

        self.left_box.connect("row-selected", self._on_left_box_selected)
        self.right_box.connect("row-selected", self._on_right_box_selected)

        middle_buttons_box.pack_start(self.add_button, False, False, 0)
        middle_buttons_box.pack_start(self.remove_button, False, False, 0)
        middle_buttons_box.pack_start(self.move_up_button, False, False, 0)
        middle_buttons_box.pack_start(self.move_down_button, False, False, 0)

        left_frame = Gtk.Frame()
        left_frame.add(self.left_box)

        right_frame = Gtk.Frame()
        right_frame.add(self.right_box)

        self.pack_start(left_frame, True, True, 0)
        self.pack_start(middle_buttons_box, False, False, 0)
        self.pack_start(right_frame, True, True, 0)

        self.left_box.add(Gtk.Label(label="left Box"))
        self.left_box.add(Gtk.Label(label="left Box2"))
        self.right_box.add(Gtk.Label(label="rightt Box"))

        self.show_all()

    def _on_add_clicked(self, *args):
        selected_rows = self.left_box.get_selected_rows()
        if len(selected_rows) == 0:
            return

        self.left_box.remove(selected_rows[0])
        self.right_box.unselect_all()
        self.right_box.insert(selected_rows[0], -1)

    def _on_remove_clicked(self, *args):
        selected_rows = self.right_box.get_selected_rows()
        if len(selected_rows) == 0:
            return

        self.right_box.remove(selected_rows[0])
        self.left_box.unselect_all()
        self.left_box.insert(selected_rows[0], -1)

    def _on_left_box_selected(self, object, list_row):
        if list_row is not None:
            self.right_box.unselect_all()

    def _on_right_box_selected(self, object, list_row):
        if list_row is not None:
            self.left_box.unselect_all()

    def _on_move_up_clicked(self, *args):
        selected_rows = self.right_box.get_selected_rows()
        box = self.right_box
        if len(selected_rows) == 0:
            return

        old_index = selected_rows[0].get_index()
        if old_index <= 0:
            return

        self.right_box.remove(selected_rows[0])
        self.right_box.insert(selected_rows[0], old_index - 1)

    def _on_move_down_clicked(self, button):
        selected_rows = self.right_box.get_selected_rows()
        if len(selected_rows) == 0:
            return

        old_index = selected_rows[0].get_index()
        self.right_box.remove(selected_rows[0])
        self.right_box.insert(selected_rows[0], old_index + 1)
