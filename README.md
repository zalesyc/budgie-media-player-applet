# Budgie Media Player Applet

Highly customizable applet for the budgie panel, for controlling all of your playing media

![screenshot](screenshot.png)

## Developing

There is a file: `src/testWin.py` that is not used when installing the applet, but it is used for debugging, as it creates the applet in a standalone window.

- If you pass -v it will show the vertical representation of the applet.
- If you pass -s the settings page will show. This page is fully operational and directly modifies the settings for `testwin`.

This project uses type annotations for better code readability,
they should be:

- on functions and methods
- class instance variables (starting with self.)

This applet targets python 3.9+ so, don't use any newer features.

For formatting, I use [black](https://github.com/psf/black)

## Install - Prebuild Packages

**Note:** I am not the maintainer of any of these packages

For other distributions, see: [_Install - Build from source_](#install---build-from-source)

### Budgie extras app

_Ubuntu Budgie 22.04+_

Go into the budgie extras app on ubuntu budgie and install Media Player Applet

### Ubuntu

_22.04+_

#### 1. Add the ubuntubudgie/backports ppa

```shell
sudo add-apt-repository ppa:ubuntubudgie/backports
```

#### 2. Update the package cache

```shell
sudo apt update
```

#### 3. Install the applet

```shell
sudo apt install budgie-media-player-applet
```

### Nixos

see: [Nixos Packages](https://search.nixos.org/packages?show=budgiePlugins.budgie-media-player-applet)

## Install - Build from source

#### 1. Install dependencies

Ubuntu, Debian:

```shell
sudo apt install git meson ninja-build python3-requests python3-gi libxfce4windowing-0-0 gir1.2-libxfce4windowing-0.0
```

Fedora:

```shell
sudo dnf install git meson ninja-build python3-requests python3-gobject libxfce4windowing
```

Arch Linux:

```shell
sudo pacman -S git meson ninja python-requests python-gobject libxfce4windowing
```

openSUSE:

```shell
sudo zypper in git-core ninja meson glib2-tools python3-requests python3-gobject python3-gobject-Gdk libxfce4windowing-0-0
```

<details>
 <summary>
  <b>
   Full list of dependencies - for other distributions
  </b>
 </summary>
 
#### Runtime
- budgie-1.0 or budgie-2.0
- gtk+-3.0
- python3 >= 3.9
- python3-requests
- python3-gobject
- gsettings
- libxfce4windowing-0.0
#### Buildtime
- meson
- ninja
- git
  
</details>

#### 2. Download the repository

```shell
git clone https://github.com/zalesyc/budgie-media-player-applet.git && cd budgie-media-player-applet
```

#### 3. Build the applet

note: _if you use budgie 10.10 (i.e. with wayland) set `-Dfor-wayland=true`_

Ubuntu, Debian, Arch Linux

```shell
meson setup build --libdir=/usr/lib --prefix=/usr -Dfor-wayland=false
```

Fedora, openSUSE

```shell
meson setup build --libdir=/usr/lib64 --prefix=/usr -Dfor-wayland=false
```

#### 4. Install the applet

```shell
sudo ninja install -C build
```

#### 5. Add the applet from Budgie Desktop Settings

You may need to log out and back in, for the changes to show up

## Troubleshooting

### Instalation does not work

- Make sure all dependencies are installed
- Try again - remove the entire directory cloned with git and start from step 1

### The applet cannot be added to the panel or isn't showing up in the panel

Run `budgie-panel --replace` from terminal, this will run the panel and
all of the applets from the terminal displaying any errors.

### The applet is installed but isn't showing in budgie desktop settings

Look into `/usr/lib64/budgie-desktop/plugins` or `/usr/lib/budgie-desktop/plugins`,
is there a `budgie-media-player-applet` directory? are there folders for other applets?

If in neither of theese directories is a `budgie-media-player-applet` directory, try installing the applet again.

If there is only a single directory that is `budgie-media-player-applet`, you may installed the applet in the wrong place, try to look for any other directory named `budgie-desktop` which contains the folders for other applets.

If nothing works try reinstalling from scratch, or try following the steps from the previous categories.
