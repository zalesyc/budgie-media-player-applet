# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Gio, Pango

from Labels import LabelWSubtitle
from math import ceil


class SettingsPage(Gtk.Box):
    def __init__(self, settings: Gio.Settings):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=15)

        self.stack: Gtk.Stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_halign(Gtk.Align.CENTER)
        self.stack.set_transition_duration(100)

        self.stack.add_titled(PanelSettingsPage(settings), "panel", "Panel")
        self.stack.add_titled(PopoverSettingsPage(settings), "popover", "Popup")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_halign(Gtk.Align.CENTER)
        stack_switcher.set_stack(self.stack)

        self.pack_start(stack_switcher, False, False, 0)
        self.pack_start(self.stack, True, True, 0)

        self.show_all()


class PanelSettingsPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.settings = settings
        self.set_column_homogeneous(False)
        self.set_column_spacing(12)
        self.set_row_spacing(12)

        order_label = LabelWSubtitle(
            title="Element order:",
            subtitle="The order of the individual elements in the panel",
            halign=Gtk.Align.START,
        )
        order_widget = OrderWidget(
            self.settings,
            available_elements={
                "album_cover",
                "song_name",
                "song_separator",
                "song_author",
                "backward_button",
                "play_pause_button",
                "forward_button",
            },
            hexpand=True,
        )

        max_len_title = LabelWSubtitle(
            title="Maximum length of:",
            subtitle="Maximum length, in characters, if set to 0 size will be unlimited",
            halign=Gtk.Align.START,
        )

        max_len_author_label = Gtk.Label(
            label="Author:",
            halign=Gtk.Align.START,
            margin_left=50,
        )

        max_len_author_value_spin = Gtk.SpinButton.new_with_range(
            min=0,
            max=100,
            step=1,
        )
        max_len_author_value_spin.set_value(
            self.settings.get_int("author-name-max-length")
        )
        max_len_author_value_spin.connect(
            "value-changed",
            lambda spin: self.settings.set_int(
                "author-name-max-length", spin.get_value_as_int()
            ),
        )

        max_len_name_label = Gtk.Label(
            label="Name:",
            halign=Gtk.Align.START,
            margin_left=50,
        )

        max_len_name_value_spin = Gtk.SpinButton.new_with_range(
            min=0,
            max=100,
            step=1,
        )
        max_len_name_value_spin.set_value(
            self.settings.get_int("media-title-max-length")
        )
        max_len_name_value_spin.connect(
            "value-changed",
            lambda spin: self.settings.set_int(
                "media-title-max-length", spin.get_value_as_int()
            ),
        )

        separator_label = LabelWSubtitle(
            title="Separator:",
            subtitle="Symbol to use as the separator",
        )
        separator_combo = Gtk.ComboBoxText()
        available_separators = ("-", ":", "·")
        for separator in available_separators:
            separator_combo.append(separator, separator)

        if (sep := self.settings.get_string("separator-text")) in available_separators:
            separator_combo.set_active_id(sep)

        separator_combo.connect(
            "changed",
            lambda combo: self.settings.set_string(
                "separator-text", combo.get_active_id()
            ),
        )

        show_arrow_label = LabelWSubtitle(
            title="Show arrow:",
            subtitle="The arrow opens the popup",
        )
        show_arrow_switch = Gtk.Switch(
            halign=Gtk.Align.START,
            valign=Gtk.Align.CENTER,
            active=self.settings.get_boolean("show-arrow"),
        )
        show_arrow_switch.connect("state_set", self.show_arrow_changed)

        self.attach(order_label, 0, 0, 2, 1)
        self.attach(order_widget, 0, 1, 2, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 2, 2, 1)

        self.attach(max_len_title, 0, 3, 2, 1)
        self.attach(max_len_author_label, 0, 4, 1, 1)
        self.attach(max_len_author_value_spin, 1, 4, 1, 1)
        self.attach(max_len_name_label, 0, 5, 1, 1)
        self.attach(max_len_name_value_spin, 1, 5, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 6, 2, 1)

        self.attach(separator_label, 0, 7, 1, 1)
        self.attach(separator_combo, 1, 7, 1, 1)
        self.attach(show_arrow_label, 0, 8, 1, 1)
        self.attach(show_arrow_switch, 1, 8, 1, 1)

    def show_arrow_changed(self, _, new_state: bool) -> bool:
        self.settings.set_boolean("show-arrow", new_state)
        return False


class PopoverSettingsPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.settings = settings
        self.set_column_homogeneous(False)
        self.set_column_spacing(12)
        self.set_row_spacing(12)
        self.set_hexpand(True)

        width_label = LabelWSubtitle(
            title="Width:",
            subtitle="Width of the popup in px",
        )
        width_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=80,
            max=1000,
            step=1,
        )
        width_scale.set_hexpand(True)
        width_scale.set_value(self.settings.get_uint("popover-width"))
        width_scale.connect(
            "value-changed",
            lambda slider: self.settings.set_uint(
                "popover-width", round(slider.get_value())
            ),
        )

        height_label = LabelWSubtitle(
            title="Height:",
            subtitle="Height of the popup in px",
        )
        height_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=80,
            max=1000,
            step=1,
        )
        height_scale.set_hexpand(True)
        height_scale.set_value(self.settings.get_uint("popover-height"))
        height_scale.connect(
            "value-changed",
            lambda slider: self.settings.set_uint(
                "popover-height", round(slider.get_value())
            ),
        )

        cover_size_label = LabelWSubtitle(
            title="Album cover size:",
            subtitle="Size of the album cover",
        )
        cover_size_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=40,
            max=500,
            step=1,
        )
        cover_size_scale.set_hexpand(True)
        cover_size_scale.set_value(self.settings.get_uint("popover-album-cover-size"))
        cover_size_scale.connect(
            "value-changed",
            lambda slider: self.settings.set_uint(
                "popover-album-cover-size", round(slider.get_value())
            ),
        )

        cover_size_note = Gtk.Label(
            label='Note: <span weight="light">'
            "If the selected album cover size is larger than "
            "the popup dimensions the popup will be automatically expanded</span>",
            use_markup=True,
            wrap=True,
            max_width_chars=1,
            xalign=0.0,
        )

        text_style_label = LabelWSubtitle(
            title="Popup text style:",
            subtitle="Style of the text in the popup",
        )

        text_style_combobox = Gtk.ComboBoxText()
        text_style_combobox.append("0", "Ellipt (Cut)")
        text_style_combobox.append("1", "Scroll")
        text_style_combobox.set_active_id(
            str(self.settings.get_uint("plasma-popover-text-style"))
        )
        text_style_combobox.connect("changed", self.text_style_combo_changed)

        text_size_label = LabelWSubtitle(
            title="Custom text size:",
            subtitle="Whether to set a custom text size",
            halign=Gtk.Align.START,
        )

        author_text_size_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=False,
            margin_left=10,
        )
        author_text_size_label = Gtk.Label(label="Author: ")
        author_text_size_value = self.settings.get_int(
            "plasma-popover-media-author-size"
        )
        author_text_size_check = Gtk.CheckButton(active=author_text_size_value >= 0)
        author_text_size_box.pack_start(author_text_size_check, False, False, 15)
        author_text_size_box.pack_start(author_text_size_label, False, False, 0)
        author_text_size_spin = Gtk.SpinButton.new_with_range(
            min=3,
            max=1000,
            step=1,
        )
        author_text_size_spin.set_value(max(abs(author_text_size_value), 3))
        author_text_size_spin.set_sensitive(author_text_size_value >= 0)
        author_text_size_check.connect(
            "toggled",
            lambda check: self._enabled_spin_check_changed(
                check, author_text_size_spin, "plasma-popover-media-author-size"
            ),
        )
        author_text_size_spin.connect(
            "value-changed",
            lambda spin: self.settings.set_int(
                "plasma-popover-media-author-size", spin.get_value_as_int()
            ),
        )

        name_text_size_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=False,
            margin_left=10,
        )
        name_text_size_label = Gtk.Label(label="Name:")
        name_text_size_value = self.settings.get_int("plasma-popover-media-name-size")
        name_text_size_check = Gtk.CheckButton(
            active=author_text_size_value >= 0,
        )
        name_text_size_box.pack_start(name_text_size_check, False, False, 15)
        name_text_size_box.pack_start(name_text_size_label, False, False, 0)
        name_text_size_spin = Gtk.SpinButton.new_with_range(
            min=3,
            max=1000,
            step=1,
        )
        name_text_size_spin.set_value(max(name_text_size_value, 3))
        name_text_size_spin.set_sensitive(name_text_size_value >= 0)
        name_text_size_check.connect(
            "toggled",
            lambda check: self._enabled_spin_check_changed(
                check, name_text_size_spin, "plasma-popover-media-name-size"
            ),
        )
        name_text_size_spin.connect(
            "value-changed",
            lambda spin: self.settings.set_int(
                "plasma-popover-media-name-size", spin.get_value_as_int()
            ),
        )

        scrolling_speed_label = LabelWSubtitle(
            title="Scrolling speed:",
            subtitle="Speed the text is scrolled when style set to scrolling",
        )

        scrolling_speed_author_label = Gtk.Label(
            label="Author:",
            halign=Gtk.Align.START,
            margin_left=50,
        )
        self.scrolling_speed_author_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=1,
            max=200,
            step=1,
        )
        self.scrolling_speed_author_scale.set_value(
            ceil(
                self.settings.get_double("plasma-popover-media-author-scrolling-speed")
                * 4
            )
        )
        self.scrolling_speed_author_scale.set_sensitive(
            settings.get_uint("plasma-popover-text-style") == 1
        )
        self.scrolling_speed_author_scale.connect(
            "value-changed",
            lambda scale: self.settings.set_double(
                "plasma-popover-media-author-scrolling-speed", scale.get_value() / 4
            ),
        )

        scrolling_speed_name_label = Gtk.Label(
            label="Name:",
            halign=Gtk.Align.START,
            margin_left=50,
        )
        self.scrolling_speed_name_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=1,
            max=200,
            step=1,
        )
        self.scrolling_speed_name_scale.set_value(
            ceil(
                self.settings.get_double("plasma-popover-media-name-scrolling-speed")
                * 4
            )
        )
        self.scrolling_speed_name_scale.set_sensitive(
            settings.get_uint("plasma-popover-text-style") == 1
        )
        self.scrolling_speed_name_scale.connect(
            "value-changed",
            lambda scale: self.settings.set_double(
                "plasma-popover-media-name-scrolling-speed", scale.get_value() / 4
            ),
        )

        self.attach(width_label, 0, 0, 1, 1)
        self.attach(width_scale, 1, 0, 1, 1)
        self.attach(height_label, 0, 1, 1, 1)
        self.attach(height_scale, 1, 1, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 2, 2, 1)

        self.attach(cover_size_label, 0, 3, 1, 1)
        self.attach(cover_size_scale, 1, 3, 1, 1)
        self.attach(cover_size_note, 0, 4, 2, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 5, 2, 1)

        self.attach(text_style_label, 0, 6, 1, 1)
        self.attach(text_style_combobox, 1, 6, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 7, 2, 1)

        self.attach(text_size_label, 0, 8, 2, 1)
        self.attach(author_text_size_box, 0, 9, 1, 1)
        self.attach(author_text_size_spin, 1, 9, 1, 1)
        self.attach(name_text_size_box, 0, 10, 1, 1)
        self.attach(name_text_size_spin, 1, 10, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 11, 2, 1)

        self.attach(scrolling_speed_label, 0, 12, 2, 1)
        self.attach(scrolling_speed_author_label, 0, 13, 1, 1)
        self.attach(self.scrolling_speed_author_scale, 1, 13, 1, 1)
        self.attach(scrolling_speed_name_label, 0, 14, 1, 1)
        self.attach(self.scrolling_speed_name_scale, 1, 14, 1, 1)

    def text_style_combo_changed(self, combo: Gtk.ComboBox) -> None:
        value = 0
        try:
            value = int(combo.get_active_id())
        except ValueError:
            pass

        self.settings.set_uint("plasma-popover-text-style", value)

        self.scrolling_speed_name_scale.set_sensitive(value == 1)
        self.scrolling_speed_author_scale.set_sensitive(value == 1)

    def _enabled_spin_check_changed(
        self, check: Gtk.ToggleButton, spin: Gtk.SpinButton, settings_key: str
    ) -> None:
        """
        This a general callback func for when you have a spin button
        that is enabled by a checkbox
        """
        new_state = check.get_active()
        old_value = self.settings.get_int(settings_key)
        print(f"{old_value=}")
        if new_state:
            new_value = max(abs(old_value), 3)
            spin.set_value(new_value)
            spin.set_sensitive(True)
        else:
            new_value = -max(abs(old_value), 3)
            spin.set_value(-new_value)
            spin.set_sensitive(False)

        self.settings.set_int(settings_key, new_value)


class MainPage(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.set_column_homogeneous(False)
        self.set_column_spacing(10)
        self.set_row_spacing(10)

        self.settings: Gio.Settings = settings

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
    def __init__(self, settings: Gio.Settings, available_elements: set[str], **kwargs):
        Gtk.Grid.__init__(self, **kwargs)
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

        left_frame = Gtk.Frame(hexpand=True)
        left_frame.add(self.left_list_box)

        right_frame = Gtk.Frame(hexpand=True)
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
