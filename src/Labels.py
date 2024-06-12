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


from typing import Optional
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")


from gi.repository import Gtk, Gdk
from gi.repository.Pango import EllipsizeMode


class ScrollingLabel(Gtk.ScrolledWindow):
    """
    Label that is scrolling if longer then parent

    if text_size is None, system default will be used

    """

    def __init__(
        self,
        text: str = "",
        speed: float = 1.0,
        text_size: Optional[int] = None,
        is_visible: bool = False,
    ):
        Gtk.ScrolledWindow.__init__(self)
        self.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.NEVER)

        self.scrolling_value: float = 0.0
        self._scroll_callback_id: Optional[int] = None
        self._speed: float = speed if speed > 0 else 1.0
        self._is_visible: bool = is_visible

        self._css_provider = Gtk.CssProvider()

        if text_size is None:
            self._css_provider.load_from_data(b"")
        else:
            self._css_provider.load_from_data(
                f"""
                .scrolled_label {{
                    font-size: {text_size}px
                }}
                """.encode()
            )

        self._label1 = Gtk.Label.new(str=text)
        self._label1.get_style_context().add_class("scrolled_label")
        self._label1.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        self._label2 = Gtk.Label.new(str=text)
        self._label2.get_style_context().add_class("scrolled_label")
        self._label2.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        self._separator1 = Gtk.Label.new(str=" - ")
        self._separator1.get_style_context().add_class("scrolled_label")
        self._separator1.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )
        self._separator2 = Gtk.Label.new(str=" - ")
        self._separator2.get_style_context().add_class("scrolled_label")
        self._separator2.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self._labels_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._labels_hbox.pack_start(self._label1, False, False, 0)
        self._labels_hbox.pack_start(self._separator1, False, False, 0)
        self._labels_hbox.pack_start(self._label2, False, False, 0)
        self._labels_hbox.pack_start(self._separator2, False, False, 0)

        self.add(self._labels_hbox)

        if self._is_visible:
            self._wait_for_self_allocate_and_resize()

    def set_label(self, text: str) -> None:
        self._label1.set_text(text)
        self._label2.set_text(text)
        if self._is_visible:
            self._resize(
                self._get_label_width(self._label1),
                self.get_allocated_width(),
            )

    def set_markup(self, markup: str) -> None:
        self._label1.set_markup(markup)
        self._label2.set_markup(markup)
        if self._is_visible:
            self._resize(
                self._get_label_width(self._label1),
                self.get_allocated_width(),
            )

    def set_text_size(self, new_size: Optional[int]) -> None:
        """
        set the text size in px, if None use system default
        """
        if new_size is None:
            self._css_provider.load_from_data(b"")
        else:
            self._css_provider.load_from_data(
                f"""
                .scrolled_label {{
                    font-size: {new_size}px
                }}
                """.encode()
            )
        if self._is_visible:
            self._resize(
                self._get_label_width(self._label1),
                self.get_allocated_width(),
            )

    def set_speed(self, new_speed: float) -> None:
        if new_speed > 0:
            self._speed = new_speed

    def to_get_visible(self) -> None:
        """
        Call this when the label starts to be visible in the ui,
        it'll start all the animations,
        see: to_get_invisible()
        """
        self._is_visible = True
        self._wait_for_self_allocate_and_resize()

    def to_get_invisible(self) -> None:
        """
        Call this when the label ends being visible in the ui,
        it'll stop all the animations, to save resources
        see: to_get_visible()
        """
        if self._scroll_callback_id is not None:
            self.remove_tick_callback(self._scroll_callback_id)
            self._scroll_callback_id = None
        self._is_visible = False

    def _resize(self, label_width: int, self_width: int) -> None:
        if label_width > self_width:
            self._label2.show()
            self._separator1.show()
            self._separator2.show()
            if self._scroll_callback_id is None:
                self._scroll_callback_id = self.add_tick_callback(self._scroll, None)
        else:
            self._label2.hide()
            self._separator1.hide()
            self._separator2.hide()
            self.get_hadjustment().set_value(0.0)
            self.scrolling_value = 0.0
            if self._scroll_callback_id is not None:
                self.remove_tick_callback(self._scroll_callback_id)
                self._scroll_callback_id = None

    def _scroll(self, *_) -> bool:
        lower = self.get_hadjustment().get_lower()
        upper = self.get_hadjustment().get_upper()
        size = upper - lower
        self.scrolling_value = ((self.scrolling_value + self._speed) % size) + lower

        if self.scrolling_value > size / 2:
            self.scrolling_value -= size / 2

        self.get_hadjustment().set_value(self.scrolling_value)

        return True

    def _wait_for_self_allocate_and_resize(self) -> None:
        self._resize(
            self._get_label_width(self._label1),
            self.get_allocated_width(),
        )
        self.connect("size-allocate", self._size_allocate)

    def _size_allocate(self, _, rect: Gdk.Rectangle) -> None:
        self._resize(
            self._get_label_width(self._label1),
            rect.width,
        )
        self.disconnect_by_func(self._size_allocate)

    @staticmethod
    def _get_label_width(label: Gtk.Label) -> int:
        return label.get_layout().get_pixel_size()[0]


class ElliptedLabel(Gtk.Label):
    """
    Ellipted label that can set its text size,
    if text_size is None, a system default will be used
    """

    def __init__(self, *args, text_size=None, **kwargs):
        Gtk.Label.__init__(self, *args, **kwargs)

        self.set_max_width_chars(1)
        self.set_ellipsize(EllipsizeMode.END)
        self.set_xalign(0.0)

        self._css_provider = Gtk.CssProvider()
        if text_size is None:
            self._css_provider.load_from_data(b"")
        else:
            self._css_provider.load_from_data(
                f"""
                .sized_label {{
                    font-size: {text_size}px
                }}
                """.encode()
            )

        self.get_style_context().add_class("sized_label")
        self.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def set_text_size(self, new_size: Optional[int]) -> None:
        if new_size is None:
            self._css_provider.load_from_data(b"")
        else:
            self._css_provider.load_from_data(
                f"""
                .sized_label {{
                    font-size: {new_size}px
                }}
                """.encode()
            )
