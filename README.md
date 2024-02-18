# Budgie Media Player Applet
Applet for the budgie panel for controlling all of your playing media

![screenshot](screenshot.png)

## Developing
There is a file: `src/testWin.py` that is not used when installing the applet, but it is used for debugging, as it creates the applet in a standalone window.
- If you pass -s as a commandline argument it will instead show the settings page.
- If you pass -v it will show the vertical representation of the applet.

## Dependencies
#### Runtime
- budgie-1.0
- gtk+-3.0
- python3
- python3-pil / python3-pillow
- python3-requests
#### Buildtime
- meson
- ninja
- git

## Install
### Install from the budgie extras app
 **Only Ubuntu Budgie 24.04+**

Go into the budgie extras app on ubuntu budgie and install Media Player Applet

### From commandline using package manager
**Only Ubuntu**

 #### 1. Add the ubuntubudgie/backports ppa
 ~~~ shell
sudo add-apt-repository ppa:ubuntubudgie/backports
~~~
#### 2. Update the package cache
~~~ shell
sudo apt update
~~~
#### 3. Install the applet
~~~ shell
sudo apt install budgie-media-player-applet
~~~


### Build from source
#### 1. Install the dependencies
#### 2. Download the repository
~~~ shell
git clone https://github.com/zalesyc/budgie-media-player-applet.git && cd budgie-media-player-applet
~~~

#### 3. Build the applet
Ubuntu Budgie, Arch Linux
~~~ shell
meson setup build --libdir=/usr/lib
~~~

Fedora, openSUSE
~~~ shell
meson setup build --libdir=/usr/lib64
~~~

#### 4. Install the applet
~~~ shell
cd build && sudo ninja install
~~~

The applet becomes visible only when there is media actively playing.

