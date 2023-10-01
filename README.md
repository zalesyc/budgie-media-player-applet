# Budgie Media Player Applet
Applet for the budgie panel for controling all of your playing media

![screenshot](screenshot.png)

## Developing
There is a file: src/testWin.py that is not used when installing the applet, but it is used for debuging, as it creates the applet in a standalone window.

## Issues 
- Works only on horizontal panels
- Minimal supported panel size is 32px
- No maximum length of the text

## Requirements
- budgie-1.0 
- gtk+-3.0
- python3
- python3-pil / python3-pillow

## Build 
Only for current user (No root privilegies needed)
~~~ shell
meson setup build --prefix=~/.local --libdir=share

cd build && ninja install
~~~

