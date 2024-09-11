# Copyright 2024, zalesyc and the budgie-media-player-applet contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, Union
from enum import IntEnum
from dataclasses import dataclass
import gi

gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gio, GdkPixbuf

"""
This file is for enums and dataclasses (structs) 
that are accessed from multiple files and having 
them there would result in circular imports
"""


class AlbumCoverType(IntEnum):
    Null = 0
    Pixbuf = 1
    Gicon = 2
    IconName = 3


@dataclass
class AlbumCoverData:
    cover_type: AlbumCoverType
    image_url_http: Optional[str]
    song_cover_pixbuf: Optional[GdkPixbuf.Pixbuf]
    song_cover_other: Union[Gio.Icon, str, None]


class PanelLengthMode(IntEnum):
    NoLimit = 0
    Variable = 1
    Fixed = 2
