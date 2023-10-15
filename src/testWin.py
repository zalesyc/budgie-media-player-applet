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

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gio
from BudgieMediaPlayer import BudgieMediaPlayer
from SettingsPage import SettingsPage


class MyWindow(Gtk.Window):
    def __init__(self):
        if len(sys.argv) > 1 and sys.argv[1] == "-s":
            super().__init__(title="MediaPlayerSettingsTestWin")
            self.mp = SettingsPage(
                Gio.Settings.new("com.github.zalesyc.budgie-media-player-applet")
            )
        else:
            super().__init__(title="MediaPlayerTestWin")
            self.mp = BudgieMediaPlayer(0)
        self.add(self.mp)


def main():
    mainloop = GLib.MainLoop()

    def quit(*args):
        mainloop.quit()

    win = MyWindow()
    win.connect("destroy", quit)
    win.show()

    mainloop.run()


if __name__ == "__main__":
    main()
