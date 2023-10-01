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

import gi.repository

gi.require_version("Budgie", "1.0")
from gi.repository import Budgie, GObject
from BudgieMediaPlayer import BudgieMediaPlayer


class BudgieMediaPlayerApplet(GObject.GObject, Budgie.Plugin):
    # This is simply an entry point into your Budgie Applet implementation.
    # Note: you must always override Object, and implement Plugin.

    # Good manners, make sure we have unique name in GObject type system
    __gtype_name__ = "BudgieMediaPlayer"

    def __init__(self):
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        # This is where the real fun happens. Return a new Budgie.Applet
        # instance with the given UUID. The UUID is determined by the
        # BudgiePanelManager, and is used for lifetime tracking.
        return BudgieMediaPlayer(uuid)
