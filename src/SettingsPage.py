# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Gio


class SettingsPage(Gtk.Box):
    def __init__(self, settings: Gio.Settings):
        self.settings: Gio.Settings = settings
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=15)

        self.stack: Gtk.Stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_halign(Gtk.Align.CENTER)
        self.stack.set_transition_duration(100)

        self.stack.add_titled(MainPage(settings), "main_page", "General")
        self.stack.add_titled(
            OrderWidget(
                settings=settings,
                available_elements={
                    "album_cover",
                    "song_name",
                    "song_separator",
                    "song_author",
                    "backward_button",
                    "play_pause_button",
                    "forward_button",
                },
            ),
            "order_page",
            "Element Order",
        )

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_halign(Gtk.Align.CENTER)
        stack_switcher.set_stack(self.stack)

        self.pack_start(stack_switcher, False, False, 0)
        self.pack_start(self.stack, True, True, 0)

        self.show_all()


class MainPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.set_column_homogeneous(False)
        self.set_column_spacing(10)
        self.set_row_spacing(10)

        self.settings: Gio.Settings = settings
        self.settings.connect("changed", self.settings_changed)

        max_len_title: Gtk.Label = Gtk.Label()
        max_len_title.set_markup("<b>Maximum Length of:</b>")
        max_len_title.set_halign(Gtk.Align.START)

        self.name_max_len_label, self.name_max_len_spin_button = (
            self._combobox_label_init(
                "Media's title:",
                "Maximum length of the playing media's title (in characters)",
                "media-title-max-length",
            )
        )

        self.author_max_len_label, self.author_max_len_spin_button = (
            self._combobox_label_init(
                "Author's name:",
                "Maximum length of author's name (in characters)",
                "author-name-max-length",
            )
        )

        separator_text_label = Gtk.Label.new("Separator:")
        separator_text_label.set_hexpand(True)
        separator_text_label.set_halign(Gtk.Align.START)
        self.separator_combobox: Gtk.ComboBoxText = Gtk.ComboBoxText.new()
        available_separators = ("-", ":", "·")
        for separator in available_separators:
            self.separator_combobox.append(separator, separator)

        separator_text = self.settings.get_string("separator-text")
        if separator_text in available_separators:
            self.separator_combobox.set_active_id(separator_text)

        self.separator_combobox.connect("changed", self.separator_combobox_changed)

        show_arrow_label: Gtk.Label = Gtk.Label(label="Show Arrow:")
        show_arrow_label.set_halign(Gtk.Align.START)
        self.show_arrow_switch: Gtk.Switch = Gtk.Switch()
        self.show_arrow_switch.set_state(settings.get_boolean("show-arrow"))
        self.show_arrow_switch.set_halign(Gtk.Align.END)
        self.show_arrow_switch.connect("state_set", self.show_arrow_changed)

        popover_width_label, self.popover_width_combobox = self._combobox_label_init(
            "Popup Width:",
            "Width of the popup in px",
            "popover-width",
            80,
            2000,
            use_uint=True,
        )

        popover_height_label, self.popover_height_combobox = self._combobox_label_init(
            "Popup Height:",
            "Height of the popup in px",
            "popover-height",
            80,
            2000,
            use_uint=True,
        )

        popover_album_cover_size_label, self.popover_album_cover_size_combobox = (
            self._combobox_label_init(
                "Popup album cover size: ",
                "Size of the album cover's bigger side in px.",
                "popover-album-cover-size",
                20,
                1000,
                use_uint=True,
            )
        )

        size_info_label = Gtk.Label(
            label="Note: if the selected album cover size is larger than "
            "the popup dimensions the popup will be automatically expanded",
            wrap=True,
        )
        size_info_label.set_max_width_chars(1)

        popover_text_style_label = Gtk.Label(
            label="Popup text style:",
            tooltip_text="Style of the name and author text in the popup",
            halign=Gtk.Align.START,
        )

        self.popover_text_style_combobox = Gtk.ComboBoxText.new()
        self.popover_text_style_combobox.append("0", "Ellipt (Cut)")
        self.popover_text_style_combobox.append("1", "Scroll")
        self.popover_text_style_combobox.set_active_id(
            str(self.settings.get_uint("plasma-popover-text-style"))
        )
        self.popover_text_style_combobox.connect(
            "changed", self.popover_text_style_combobox_changed
        )

        popover_text_size_label = Gtk.Label(halign=Gtk.Align.START)
        popover_text_size_label.set_markup("<b>Size of the text in popup:</b>")

        popover_text_size_name_label, popover_text_size_name_spinbox = (
            self._combobox_label_init(
                "   - Name:",
                "Size of the name text in the popup, -1 is default",
                "plasma-popover-media-name-size",
                -1,
                200,
            )
        )
        popover_text_size_author_label, popover_text_size_author_spinbox = (
            self._combobox_label_init(
                "   - Author:",
                "Size of the author text in the popup, -1 is default",
                "plasma-popover-media-author-size",
                -1,
                200,
            )
        )

        popover_scrolling_speed_label = Gtk.Label(halign=Gtk.Align.START)
        popover_scrolling_speed_label.set_markup(
            "<b>Text scrolling speed in popup:</b>"
        )

        popover_scrolling_speed_name_label = Gtk.Label(
            label="   - Name:",
            tooltip_text="Speed of the scrolling of the name text in the popup, "
            "if text style set to scrolling",
            halign=Gtk.Align.START,
        )

        popover_scrolling_speed_name_spinbox = Gtk.SpinButton.new_with_range(1, 200, 1)
        popover_scrolling_speed_name_spinbox.set_value(
            round(
                self.settings.get_double("plasma-popover-media-name-scrolling-speed")
                * 4
            )
        )
        popover_scrolling_speed_name_spinbox.connect(
            "value-changed",
            lambda *_: self.settings.set_double(
                "plasma-popover-media-name-scrolling-speed",
                popover_scrolling_speed_name_spinbox.get_value_as_int() / 4,
            ),
        )

        popover_scrolling_speed_author_label = Gtk.Label(
            label="   - Author:",
            tooltip_text="Speed of the scrolling of the author text in the popup, "
            "if text style set to scrolling",
            halign=Gtk.Align.START,
        )

        popover_scrolling_speed_author_spinbox = Gtk.SpinButton.new_with_range(
            1, 200, 1
        )
        popover_scrolling_speed_author_spinbox.set_value(
            round(
                self.settings.get_double("plasma-popover-media-author-scrolling-speed")
                * 4
            )
        )
        popover_scrolling_speed_author_spinbox.connect(
            "value-changed",
            lambda *_: self.settings.set_double(
                "plasma-popover-media-author-scrolling-speed",
                popover_scrolling_speed_author_spinbox.get_value_as_int() / 4,
            ),
        )

        self.attach(max_len_title, 0, 0, 2, 1)
        self.attach(self.name_max_len_label, 0, 1, 1, 1)
        self.attach(self.name_max_len_spin_button, 1, 1, 1, 1)
        self.attach(self.author_max_len_label, 0, 2, 1, 1)
        self.attach(self.author_max_len_spin_button, 1, 2, 1, 1)
        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 3, 2, 1)
        self.attach(separator_text_label, 0, 4, 1, 1)
        self.attach(self.separator_combobox, 1, 4, 1, 1)
        self.attach(show_arrow_label, 0, 5, 1, 1)
        self.attach(self.show_arrow_switch, 1, 5, 1, 1)
        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 6, 2, 1)
        self.attach(popover_width_label, 0, 7, 1, 1)
        self.attach(self.popover_width_combobox, 1, 7, 1, 1)
        self.attach(popover_height_label, 0, 8, 1, 1)
        self.attach(self.popover_height_combobox, 1, 8, 1, 1)
        self.attach(popover_album_cover_size_label, 0, 9, 1, 1)
        self.attach(self.popover_album_cover_size_combobox, 1, 9, 1, 1)
        self.attach(size_info_label, 0, 10, 2, 1)
        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 11, 2, 1)
        self.attach(popover_text_style_label, 0, 12, 1, 1)
        self.attach(self.popover_text_style_combobox, 1, 12, 1, 1)
        self.attach(popover_text_size_label, 0, 13, 2, 1)
        self.attach(popover_text_size_name_label, 0, 14, 1, 1)
        self.attach(popover_text_size_name_spinbox, 1, 14, 1, 1)
        self.attach(popover_text_size_author_label, 0, 15, 1, 1)
        self.attach(popover_text_size_author_spinbox, 1, 15, 1, 1)
        self.attach(popover_scrolling_speed_label, 0, 16, 2, 1)
        self.attach(popover_scrolling_speed_name_label, 0, 17, 1, 1)
        self.attach(popover_scrolling_speed_name_spinbox, 1, 17, 1, 1)
        self.attach(popover_scrolling_speed_author_label, 0, 18, 1, 1)
        self.attach(popover_scrolling_speed_author_spinbox, 1, 18, 1, 1)

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

    def show_arrow_changed(self, _, state: bool) -> bool:
        self.settings.set_boolean("show-arrow", state)
        return False

    def popover_text_style_combobox_changed(self, *_) -> None:
        new_val = self.popover_text_style_combobox.get_active_id()
        if not new_val.isdigit():
            return
        num_val = int(new_val)
        if num_val < 0:
            return
        self.settings.set_uint("plasma-popover-text-style", num_val)

    def _combobox_label_init(
        self,
        label_text,
        tooltip_text,
        spin_button_settings_property,
        range_start=5,
        range_end=100,
        use_uint=False,
    ):
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        label.set_tooltip_text(tooltip_text)
        spin_button = Gtk.SpinButton.new_with_range(range_start, range_end, 1)
        spin_button.set_value(
            self.settings.get_uint(spin_button_settings_property)
            if use_uint
            else self.settings.get_int(spin_button_settings_property)
        )
        spin_button.connect(
            "value_changed",
            lambda widget: (
                self.settings.set_uint(
                    spin_button_settings_property, widget.get_value_as_int()
                )
                if use_uint
                else self.settings.set_int(
                    spin_button_settings_property, widget.get_value_as_int()
                )
            ),
        )
        return label, spin_button


class OrderWidget(Gtk.Grid):
    def __init__(self, settings: Gio.Settings, available_elements: set[str]):
        Gtk.Grid.__init__(self)
        self.set_column_spacing(6)
        self.set_row_spacing(6)

        self.settings: Gio.Settings = settings
        self.available_elements: set[str] = available_elements

        left_description = Gtk.Label.new("Available elements")
        right_description = Gtk.Label.new("Enabled elements")

        self.left_list_box: Gtk.ListBox = Gtk.ListBox()
        self.left_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)

        middle_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        middle_buttons_box.set_valign(Gtk.Align.CENTER)

        self.right_list_box: Gtk.ListBox = Gtk.ListBox()
        self.right_list_box.set_property("selection-mode", Gtk.SelectionMode.SINGLE)

        left_frame = Gtk.Frame()
        left_frame.add(self.left_list_box)

        right_frame = Gtk.Frame()
        right_frame.add(self.right_list_box)

        self.add_button: Gtk.Button = Gtk.Button.new_from_icon_name(
            "go-next-symbolic", Gtk.IconSize.BUTTON
        )
        self.remove_button: Gtk.Button = Gtk.Button.new_from_icon_name(
            "go-previous-symbolic", Gtk.IconSize.BUTTON
        )
        self.move_up_button: Gtk.Button = Gtk.Button.new_from_icon_name(
            "go-up-symbolic", Gtk.IconSize.BUTTON
        )
        self.move_down_button: Gtk.Button = Gtk.Button.new_from_icon_name(
            "go-down-symbolic", Gtk.IconSize.BUTTON
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

        self.enabled_elements_order: list[str] = settings.get_strv("element-order")

        self.widget_to_element_name_dict: dict[Gtk.ListBoxRow, str] = {}

        for element_name in self.enabled_elements_order:
            if element_name not in self.available_elements:
                print(
                    f"budgie-media-player-applet: '{element_name}' not in available elements - probably wrong settings -> skipping"
                )
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
            new_element_order[widget.get_index()] = (
                self.widget_to_element_name_dict.get(widget)
            )

        self.settings.set_strv("element-order", new_element_order)

    def _on_left_box_selected(self, list_box, selected_list_row):
        if selected_list_row is not None:
            self.right_list_box.unselect_all()

    def _on_right_box_selected(self, list_box, selected_list_row):
        if selected_list_row is not None:
            self.left_list_box.unselect_all()
