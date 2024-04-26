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


from typing import Optional, Union
from enum import IntEnum
from dataclasses import dataclass
import gi

gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gio, GdkPixbuf


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
