# Copyright 2023 - 2025, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

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
