#! /bin/python3

# Copyright 2023 - 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi.repository
from BudgieMediaPlayer import BudgieMediaPlayer

gi.require_version("Gtk", "3.0")
gi.require_version("Budgie", "1.0")
gi.require_version("GLib", "2.0")

from gi.repository import Gtk, GLib, Budgie


class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="MediaPlayerTestWin")
        self.player = BudgieMediaPlayer("test")
        if len(sys.argv) > 1:
            if sys.argv[1] == "-s":
                self.add(self.player.do_get_settings_ui())
                return
            if sys.argv[1] == "-v":
                self.player.do_panel_position_changed(Budgie.PanelPosition.LEFT)
        self.add(self.player)
        popover_mgr = Budgie.PopoverManager()
        self.player.do_update_popovers(popover_mgr)


def main():
    mainloop = GLib.MainLoop()

    def quit_window(*_):
        mainloop.quit()

    win = MyWindow()
    win.connect("destroy", quit_window)
    win.show()

    mainloop.run()


if __name__ == "__main__":
    main()
