#! /bin/python3

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
            if sys.argv[1] == "-v":
                self.player.do_panel_position_changed(Budgie.PanelPosition.LEFT)
                return
            if sys.argv[1] == "-s":
                self.add(self.player.do_get_settings_ui())
                return

        self.add(self.player)


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
