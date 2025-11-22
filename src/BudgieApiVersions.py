# Copyright 2025, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Only purpouse of this file is to be used together with testWin.py in testing the
installed applet uses BudgieLibraryVersion.py.in which is connfigured by meson instead
"""

BUDGIE_VERSION_X11 = (
    "2.0"  # set this to "2.0" if budgie > 10.9.4, othervise set this to "1.0"
)
BUDGIE_VERSION_WAYLAND = "3.0"
