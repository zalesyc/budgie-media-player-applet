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
        self.stack.set_halign(Gtk.Align.CENTER)
        self.stack.set_transition_duration(100)

        self.stack.add_titled(MainPage(settings), "main_page", "General")
        self.stack.add_titled(OrderPage(settings), "order_page", "Element Order")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_halign(Gtk.Align.CENTER)
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

        separator_text_label = Gtk.Label.new("Separator:")
        separator_text_label.set_halign(Gtk.Align.START)
        self.separator_combobox = Gtk.ComboBoxText.new()
        available_separators = ("-", ":", "·")
        for separator in available_separators:
            self.separator_combobox.append(separator, separator)

        if settings is not None:
            separator_text = settings.get_string("separator-text")
            if separator_text in available_separators:
                self.separator_combobox.set_active_id(separator_text)

        self.separator_combobox.connect("changed", self.separator_combobox_changed)

        self.attach(self.max_len_title, 0, 0, 2, 1)
        self.attach(self.name_max_len_label, 0, 1, 1, 1)
        self.attach(self.name_max_len_spin_button, 1, 1, 1, 1)
        self.attach(self.author_max_len_label, 0, 2, 1, 1)
        self.attach(self.author_max_len_spin_button, 1, 2, 1, 1)
        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 3, 2, 1)
        self.attach(separator_text_label, 0, 4, 1, 1)
        self.attach(self.separator_combobox, 1, 4, 1, 1)

        self.show_all()

    def name_max_len_spin_box_changed(self, widget):
        self.settings.set_int("media-title-max-length", widget.get_value_as_int())

    def author_max_len_spin_box_changed(self, widget):
        self.settings.set_int("author-name-max-length", widget.get_value_as_int())

    def separator_combobox_changed(self, combo_box):
        self.settings.set_string(
            "separator-text",
            self.separator_combobox.get_active_text(),
        )

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


class OrderPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.set_column_spacing(6)
        self.set_row_spacing(6)

        self.settings = settings
        # TODO: make this a parameter
        self.available_elements: {str} = {
            "album_cover",
            "song_name",
            "song_separator",
            "song_author",
            "backward_button",
            "play_pause_button",
            "forward_button",
        }

        left_description = Gtk.Label.new("Available elements")
        right_description = Gtk.Label.new("Enabled elements")

        self.left_list_box = Gtk.ListBox()
        self.left_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)

        middle_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        middle_buttons_box.set_valign(Gtk.Align.CENTER)

        self.right_list_box = Gtk.ListBox()
        self.right_list_box.set_property("selection-mode", Gtk.SelectionMode.SINGLE)

        left_frame = Gtk.Frame()
        left_frame.add(self.left_list_box)

        right_frame = Gtk.Frame()
        right_frame.add(self.right_list_box)

        self.add_button = Gtk.Button.new_from_icon_name(
            "arrow-right", Gtk.IconSize.BUTTON
        )
        self.remove_button = Gtk.Button.new_from_icon_name(
            "arrow-left", Gtk.IconSize.BUTTON
        )
        self.move_up_button = Gtk.Button.new_from_icon_name(
            "arrow-up", Gtk.IconSize.BUTTON
        )
        self.move_down_button = Gtk.Button.new_from_icon_name(
            "arrow-down", Gtk.IconSize.BUTTON
        )
        self.move_down_button = Gtk.Button.new_from_icon_name(
            "arrow-down", Gtk.IconSize.BUTTON
        )

        self.add_button.connect("clicked", self._on_add_clicked)
        self.remove_button.connect("clicked", self._on_remove_clicked)
        self.move_up_button.connect("clicked", self._on_move_up_clicked)
        self.move_down_button.connect("clicked", self._on_move_down_clicked)
        self.left_list_box.connect("row-selected", self._on_left_box_selected)
        self.right_list_box.connect("row-selected", self._on_right_box_selected)

        middle_buttons_box.pack_start(self.add_button, False, False, 0)
        middle_buttons_box.pack_start(self.remove_button, False, False, 0)
        middle_buttons_box.pack_start(self.move_up_button, False, False, 0)
        middle_buttons_box.pack_start(self.move_down_button, False, False, 0)

        self.attach(left_description, 0, 0, 1, 1)
        self.attach(right_description, 2, 0, 1, 1)
        self.attach(left_frame, 0, 1, 1, 1)
        self.attach(middle_buttons_box, 1, 1, 1, 1)
        self.attach(right_frame, 2, 1, 1, 1)

        if settings is None:
            self.enabled_elements_order = ["song_author", "song_separator", "song_name"]
        else:
            self.enabled_elements_order = settings.get_strv("element-order")

        self.widget_to_element_name_dict: {Gtk.ListBoxRow: str} = {}

        for element_name in self.enabled_elements_order:
            if element_name not in self.available_elements:
                print(
                    f"'{element_name}' not in available elements - probably wrong settings -> skipping"
                )  # TODO: make this error in log framework
                continue
            self.right_list_box.insert(self._make_row(element_name), -1)

        for element_name in self.available_elements:
            if element_name in self.enabled_elements_order:
                continue
            self.left_list_box.insert(self._make_row(element_name), -1)

        self.show_all()

    def _make_row(self, element_name: str) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow.new()
        row.add(Gtk.Label(label=element_name.replace("_", " ")))
        self.widget_to_element_name_dict.update({row: element_name})
        return row

    def _on_add_clicked(self, *args):
        selected_rows = self.left_list_box.get_selected_rows()
        if len(selected_rows) == 0:
            return

        self.left_list_box.remove(selected_rows[0])
        self.right_list_box.unselect_all()
        self.right_list_box.insert(selected_rows[0], -1)
        self._enabled_changed()

    def _on_remove_clicked(self, *args):
        selected_rows = self.right_list_box.get_selected_rows()
        if len(selected_rows) == 0:
            return

        self.right_list_box.remove(selected_rows[0])
        self.left_list_box.unselect_all()
        self.left_list_box.insert(selected_rows[0], -1)
        self._enabled_changed()

    def _on_move_up_clicked(self, *args):
        selected_rows = self.right_list_box.get_selected_rows()
        box = self.right_list_box
        if len(selected_rows) == 0:
            return

        old_index = selected_rows[0].get_index()
        if old_index <= 0:
            return

        self.right_list_box.remove(selected_rows[0])
        self.right_list_box.insert(selected_rows[0], old_index - 1)
        self._enabled_changed()

    def _on_move_down_clicked(self, button):
        selected_rows = self.right_list_box.get_selected_rows()
        if len(selected_rows) == 0:
            return

        old_index = selected_rows[0].get_index()
        self.right_list_box.remove(selected_rows[0])
        self.right_list_box.insert(selected_rows[0], old_index + 1)
        self._enabled_changed()

    def _enabled_changed(self):
        children = self.right_list_box.get_children()
        new_element_order = [None] * len(children)

        for widget in children:
            new_element_order[
                widget.get_index()
            ] = self.widget_to_element_name_dict.get(widget)

        self.settings.set_strv("element-order", new_element_order)

    def _on_left_box_selected(self, list_box, selected_list_row):
        if selected_list_row is not None:
            self.right_list_box.unselect_all()

    def _on_right_box_selected(self, list_box, selected_list_row):
        if selected_list_row is not None:
            self.left_list_box.unselect_all()
