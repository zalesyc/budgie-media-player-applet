# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Gio

from Labels import LabelWSubtitle
from EnumsStructs import PanelLengthMode
from math import ceil
from typing import Union


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


class _SettingsPageBase(Gtk.Grid):
    def __init__(self, settings: Gio.Settings):
        Gtk.Grid.__init__(self)
        self.settings = settings
        self.set_column_homogeneous(False)
        self.set_column_spacing(12)
        self.set_row_spacing(12)

    def _enabled_spin_check_changed(
        self,
        check: Gtk.ToggleButton,
        spin: Union[Gtk.SpinButton, Gtk.Range],
        settings_key: str,
        min_value: int = 3,
    ) -> None:
        """
        This a general callback func for when you have a spin button / scale
        that is enabled by a checkbox
        """
        new_state = check.get_active()
        old_value = self.settings.get_int(settings_key)
        if new_state:
            new_value = max(abs(old_value), min_value)
            spin.set_value(new_value)
            spin.set_sensitive(True)
        else:
            new_value = -max(abs(old_value), min_value)
            spin.set_value(-new_value)
            spin.set_sensitive(False)

        self.settings.set_int(settings_key, new_value)


class PanelSettingsPage(_SettingsPageBase):
    def __init__(self, settings: Gio.Settings):
        super().__init__(settings)

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
        max_len_type: PanelLengthMode = PanelLengthMode(
            settings.get_uint("panel-length-mode")
        )
        max_len_title = LabelWSubtitle(
            title="Length:",
            subtitle="Length of the applet in the panel, there are multiple modes",
            halign=Gtk.Align.START,
        )

        max_len_no_limit_radio = Gtk.RadioButton(
            active=max_len_type == PanelLengthMode.NoLimit,
        )
        max_len_no_limit_radio.connect(
            "toggled",
            self._no_limit_len_radio_toggled,
        )
        max_len_no_limit_label = LabelWSubtitle(
            title="No limit",
            subtitle="The applet may grow into huge sizes, not recommended",
        )
        max_len_no_limit_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        max_len_no_limit_box.pack_start(max_len_no_limit_radio, False, False, 15)
        max_len_no_limit_box.pack_start(max_len_no_limit_label, False, False, 0)

        max_len_fixed_radio = Gtk.RadioButton(
            group=max_len_no_limit_radio,
            active=max_len_type == PanelLengthMode.Fixed,
        )
        max_len_fixed_label = LabelWSubtitle(
            title="Fixed",
            subtitle="The applet will always have the same length",
        )
        max_len_fixed_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        max_len_fixed_box.pack_start(max_len_fixed_radio, False, False, 15)
        max_len_fixed_box.pack_start(max_len_fixed_label, False, False, 0)
        max_len_fixed_value_label = Gtk.Label(
            label="Length:",
            halign=Gtk.Align.START,
            margin_left=30,
        )
        max_len_fixed_value_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 10, 1000, 1
        )
        max_len_fixed_value_scale.set_sensitive(max_len_type == PanelLengthMode.Fixed)
        max_len_fixed_value_scale.set_value_pos(Gtk.PositionType.LEFT)
        max_len_fixed_value_scale.set_value(
            self.settings.get_uint("panel-length-fixed")
        )
        max_len_fixed_value_scale.connect(
            "value-changed",
            lambda scale: self.settings.set_uint(
                "panel-length-fixed", round(scale.get_value())
            ),
        )
        max_len_fixed_radio.connect(
            "toggled",
            self._fixed_len_radio_toggled,
            {max_len_fixed_value_scale},
        )

        max_len_variable_radio = Gtk.RadioButton(
            group=max_len_no_limit_radio,
            active=max_len_type == PanelLengthMode.Variable,
        )
        max_len_variable_label = LabelWSubtitle(
            title="Maximal Length",
            subtitle="The applet will try to grow until it reaches the set maximum "
            "length, the length is set individually for the title and author, "
            "if disabled there is no limit.",
            wrap_subtitle=True,
        )
        max_len_variable_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        max_len_variable_box.pack_start(max_len_variable_radio, False, False, 15)
        max_len_variable_box.pack_start(max_len_variable_label, True, True, 0)

        max_len_variable_value_name_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=False,
            margin_left=15,
        )
        max_len_variable_value_name_label = Gtk.Label(
            label="Name:",
            halign=Gtk.Align.START,
        )
        max_len_variable_value_name = self.settings.get_int("media-title-max-length")
        self.max_len_variable_value_name_check = Gtk.CheckButton(
            active=max_len_variable_value_name >= 0,
            sensitive=max_len_type == PanelLengthMode.Variable,
        )
        self.max_len_variable_value_name_spin = Gtk.SpinButton.new_with_range(
            min=5,
            max=100,
            step=1,
        )
        self.max_len_variable_value_name_spin.set_value(
            max(abs(max_len_variable_value_name), 5)
        )
        self.max_len_variable_value_name_spin.set_sensitive(
            max_len_variable_value_name >= 0
            and max_len_type == PanelLengthMode.Variable
        )
        max_len_variable_value_name_box.pack_start(
            self.max_len_variable_value_name_check, False, False, 15
        )
        max_len_variable_value_name_box.pack_start(
            max_len_variable_value_name_label, False, False, 0
        )
        self.max_len_variable_value_name_check.connect(
            "toggled",
            lambda check: self._enabled_spin_check_changed(
                check,
                self.max_len_variable_value_name_spin,
                "media-title-max-length",
                min_value=5,
            ),
        )
        self.max_len_variable_value_name_spin.connect(
            "value-changed",
            lambda spin: self.settings.set_int(
                "media-title-max-length", spin.get_value_as_int()
            ),
        )

        max_len_variable_value_author_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=False,
            margin_left=15,
        )
        max_len_variable_value_author_label = Gtk.Label(
            label="Author:",
            halign=Gtk.Align.START,
        )
        max_len_variable_value_author = self.settings.get_int("author-name-max-length")
        self.max_len_variable_value_author_check = Gtk.CheckButton(
            active=max_len_variable_value_author >= 0,
            sensitive=max_len_type == PanelLengthMode.Variable,
        )
        self.max_len_variable_value_author_spin = Gtk.SpinButton.new_with_range(
            min=5,
            max=100,
            step=1,
        )
        max_len_variable_value_author_box.pack_start(
            self.max_len_variable_value_author_check, False, False, 15
        )
        max_len_variable_value_author_box.pack_start(
            max_len_variable_value_author_label, False, False, 0
        )
        self.max_len_variable_value_author_spin.set_value(
            max(abs(max_len_variable_value_author), 5)
        )
        self.max_len_variable_value_author_spin.set_sensitive(
            max_len_variable_value_author >= 0
            and max_len_type == PanelLengthMode.Variable
        )
        self.max_len_variable_value_author_check.connect(
            "toggled",
            lambda check: self._enabled_spin_check_changed(
                check,
                self.max_len_variable_value_author_spin,
                "author-name-max-length",
                min_value=5,
            ),
        )
        self.max_len_variable_value_author_spin.connect(
            "value-changed",
            lambda spin: self.settings.set_int(
                "author-name-max-length", spin.get_value_as_int()
            ),
        )

        max_len_variable_radio.connect(
            "toggled",
            self._variable_len_radio_toggled,
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
        self.attach(max_len_no_limit_box, 0, 4, 2, 1)
        self.attach(max_len_fixed_box, 0, 5, 2, 1)
        self.attach(max_len_fixed_value_label, 0, 6, 1, 1)
        self.attach(max_len_fixed_value_scale, 1, 6, 1, 1)
        self.attach(max_len_variable_box, 0, 7, 2, 1)
        self.attach(max_len_variable_value_name_box, 0, 8, 1, 1)
        self.attach(self.max_len_variable_value_name_spin, 1, 8, 1, 1)
        self.attach(max_len_variable_value_author_box, 0, 9, 1, 1)
        self.attach(self.max_len_variable_value_author_spin, 1, 9, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 10, 2, 1)

        self.attach(separator_label, 0, 11, 1, 1)
        self.attach(separator_combo, 1, 11, 1, 1)
        self.attach(show_arrow_label, 0, 12, 1, 1)
        self.attach(show_arrow_switch, 1, 12, 1, 1)

    def show_arrow_changed(self, _, new_state: bool) -> bool:
        self.settings.set_boolean("show-arrow", new_state)
        return False

    def _no_limit_len_radio_toggled(
        self,
        radio: Gtk.ToggleButton,
    ):
        if radio.get_active():
            self.settings.set_uint("panel-length-mode", PanelLengthMode.NoLimit)

    def _fixed_len_radio_toggled(
        self,
        radio: Gtk.ToggleButton,
        widgets_enabled_by_this: frozenset[Gtk.Widget],
    ):
        active = radio.get_active()
        for widget in widgets_enabled_by_this:
            widget.set_sensitive(active)

        if active:
            self.settings.set_uint("panel-length-mode", PanelLengthMode.Fixed)

    def _variable_len_radio_toggled(
        self,
        radio: Gtk.ToggleButton,
    ):
        active = radio.get_active()

        self.max_len_variable_value_author_check.set_sensitive(active)
        self.max_len_variable_value_name_check.set_sensitive(active)

        if self.settings.get_int("media-title-max-length") >= 0:
            self.max_len_variable_value_name_spin.set_sensitive(active)

        if self.settings.get_int("author-name-max-length") >= 0:
            self.max_len_variable_value_author_spin.set_sensitive(active)

        if active:
            self.settings.set_uint("panel-length-mode", PanelLengthMode.Variable)


class PopoverSettingsPage(_SettingsPageBase):
    def __init__(self, settings: Gio.Settings):
        super().__init__(settings)

        width_label = LabelWSubtitle(
            title="Width:",
            subtitle="Width of the popup in px",
        )
        width_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=80,
            max=2000,
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
            max=2000,
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
            subtitle="Percentage of available space",
        )
        cover_size_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            min=1,
            max=100,
            step=1,
        )
        cover_size_scale.set_hexpand(True)
        cover_size_scale.set_value(
            round(self.settings.get_double("popover-album-cover-size") * 100)
        )
        cover_size_scale.connect(
            "value-changed",
            lambda slider: self.settings.set_double(
                "popover-album-cover-size", round(slider.get_value() / 100, 2)
            ),
        )

        text_style_label = LabelWSubtitle(
            title="Popup text style:",
            subtitle="Style of the text in the popup",
        )

        text_style_combobox = Gtk.ComboBoxText()
        text_style_combobox.append("0", "Ellipt (Cut)")
        text_style_combobox.append("1", "Scroll, may be jittery")
        text_style_combobox.set_active_id(
            str(self.settings.get_uint("plasma-popover-text-style"))
        )
        text_style_combobox.connect("changed", self.text_style_combo_changed)

        text_size_label = LabelWSubtitle(
            title="Custom text size:",
            subtitle="Whether to set a custom text size",
            halign=Gtk.Align.START,
        )

        name_text_size_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=False,
            margin_left=10,
        )
        name_text_size_label = Gtk.Label(label="Name:")
        name_text_size_value = self.settings.get_int("plasma-popover-media-name-size")
        name_text_size_check = Gtk.CheckButton(
            active=name_text_size_value >= 0,
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

        scrolling_speed_label = LabelWSubtitle(
            title="Scrolling speed:",
            subtitle="Speed the text is scrolled when style set to scrolling",
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

        self.attach(width_label, 0, 0, 1, 1)
        self.attach(width_scale, 1, 0, 1, 1)
        self.attach(height_label, 0, 1, 1, 1)
        self.attach(height_scale, 1, 1, 1, 1)
        self.attach(cover_size_label, 0, 2, 1, 1)
        self.attach(cover_size_scale, 1, 2, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 3, 2, 1)

        self.attach(text_style_label, 0, 4, 1, 1)
        self.attach(text_style_combobox, 1, 4, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 5, 2, 1)

        self.attach(text_size_label, 0, 6, 2, 1)
        self.attach(name_text_size_box, 0, 7, 1, 1)
        self.attach(name_text_size_spin, 1, 7, 1, 1)
        self.attach(author_text_size_box, 0, 8, 1, 1)
        self.attach(author_text_size_spin, 1, 8, 1, 1)

        self.attach(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL), 0, 9, 2, 1)

        self.attach(scrolling_speed_label, 0, 10, 2, 1)
        self.attach(scrolling_speed_name_label, 0, 11, 1, 1)
        self.attach(self.scrolling_speed_name_scale, 1, 11, 1, 1)
        self.attach(scrolling_speed_author_label, 0, 12, 1, 1)
        self.attach(self.scrolling_speed_author_scale, 1, 12, 1, 1)

    def text_style_combo_changed(self, combo: Gtk.ComboBox) -> None:
        value = 0
        try:
            value = int(combo.get_active_id())
        except ValueError:
            pass

        self.settings.set_uint("plasma-popover-text-style", value)

        self.scrolling_speed_name_scale.set_sensitive(value == 1)
        self.scrolling_speed_author_scale.set_sensitive(value == 1)


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
