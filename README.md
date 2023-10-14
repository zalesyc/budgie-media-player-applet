# Budgie Media Player Applet
Applet for the budgie panel for controling all of your playing media

![screenshot](screenshot.png)

## Developing
There is a file: src/testWin.py that is not used when installing the applet, but it is used for debuging, as it creates the applet in a standalone window.

## Issues 
- Works only on horizontal panels
- Minimal supported panel size is 32px

## Requirements
- budgie-1.0 
- gtk+-3.0
- python3
- python3-pil / python3-pillow

## Build 
### Ubuntu Budgie
~~~ shell
meson setup build --libdir=/usr/lib

cd build && sudo ninja install
~~~
### Fedora
~~~ shell
meson setup build --libdir=/usr/lib64

cd build && sudo ninja install
~~~

