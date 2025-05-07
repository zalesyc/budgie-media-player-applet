# Copyright 2024 - 2025, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
from typing import Optional

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk


class FixedSizeBin(Gtk.Bin):
    """
    A single-child container that has fixed size (width or height) based on orientation.
    """

    def __init__(
        self,
        size: Optional[int] = None,
        orientation: Gtk.Orientation = Gtk.Orientation.HORIZONTAL,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.preferred_size: Optional[int] = size
        self.orientation: Gtk.Orientation = orientation

    def set_size(self, new_size: Optional[int]) -> None:
        self.preferred_size = new_size
        self.queue_resize()

    def set_orientation(self, new_orientation: Gtk.Orientation) -> None:
        self.orientation = new_orientation
        self.queue_resize()

    def do_size_allocate(self, allocation: Gdk.Rectangle) -> None:
        if self.get_child() is None:
            return
        if self.preferred_size is None:
            self.get_child().size_allocate(allocation)
            return
        child_allocation = Gdk.Rectangle()
        child_allocation.x = allocation.x
        child_allocation.y = allocation.y
        if self.orientation == Gtk.Orientation.HORIZONTAL:
            child_min_width, _ = self.get_child().get_preferred_width()
            child_allocation.height = allocation.height
            child_allocation.width = min(
                max(child_min_width, self.preferred_size),
                allocation.width,
            )
        else:
            child_min_height, _ = self.get_child().get_preferred_height()
            child_allocation.width = allocation.width
            child_allocation.height = min(
                max(child_min_height, self.preferred_size),
                allocation.height,
            )

        self.get_child().size_allocate(child_allocation)

    def do_get_preferred_width(self) -> tuple[int, int]:
        if self.get_child() is None:
            return 0, 0

        if self.preferred_size is None:
            return self.get_child().get_preferred_width()

        if self.orientation == Gtk.Orientation.HORIZONTAL:
            child_min_width, _ = self.get_child().get_preferred_width()
            return child_min_width, max(child_min_width, self.preferred_size)
        else:
            return self.get_child().get_preferred_width()

    def do_get_preferred_height(self):
        if self.get_child() is None:
            return 0, 0

        if self.preferred_size is None:
            return self.get_child().get_preferred_height()

        if self.orientation == Gtk.Orientation.HORIZONTAL:
            return self.get_child().get_preferred_height()
        else:
            child_min_height, _ = self.get_child().get_preferred_height()
            return child_min_height, max(child_min_height, self.preferred_size)

    def do_get_preferred_height_for_width(self, _) -> tuple[int, int]:
        return self.do_get_preferred_height()

    def do_get_preferred_width_for_height(self, _) -> tuple[int, int]:
        return self.do_get_preferred_width()
