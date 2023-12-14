# Budgie Media Player Applet
Applet for the budgie panel for controlling all of your playing media

![screenshot](screenshot.png)

## Developing
There is a file: `src/testWin.py` that is not used when installing the applet, but it is used for debugging, as it creates the applet in a standalone window.
If you pass -s as a commandline argument it will instead show the settings page.
If you pass -v it will show the vertical representation of the applet.

## Requirements
- budgie-1.0 
- gtk+-3.0
- python3
- python3-pil / python3-pillow
- meson
- ninja
- git

## Build 
### Download the repository
~~~ shell
git clone https://github.com/zalesyc/budgie-media-player-applet.git && cd budgie-media-player-applet
~~~

### Build the applet
**Ubuntu Budgie, Arch Linux**
~~~ shell
meson setup build --libdir=/usr/lib
~~~

**Fedora, openSUSE**
~~~ shell
meson setup build --libdir=/usr/lib64
~~~

### Install the applet
~~~ shell
cd build && sudo ninja install
~~~

The applet becomes visible only when there is media actively playing.
