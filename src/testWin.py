#! /bin/python3

import gi.repository

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from BudgieMediaPlayer import BudgieMediaPlayer


class MyWindow(Gtk.Window):
    def __init__(self):
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
