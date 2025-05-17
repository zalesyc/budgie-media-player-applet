project('budgie-media-player-applet')

datadir = join_paths(get_option('prefix'), get_option('datadir'))

PLUGINS_INSTALL_DIR = join_paths(get_option('libdir'), 'budgie-desktop', 'plugins', meson.project_name())
PIXMAPS_DIR = join_paths(datadir, 'pixmaps')
HICOLOR_THEME_DIR = join_paths(datadir, 'icons', 'hicolor')

for_wayland = get_option('for-wayland')

if for_wayland == false
	python_loader = 'python3'
else
	python_loader = 'python' 
endif

configdata= configuration_data()
configdata.set('PYTHON', python_loader)
plugininstall = configure_file(
    input: 'budgie-media-player-applet.plugin.in',
    output: 'budgie-media-player-applet.plugin',
    configuration: configdata
)

install_data(
    plugininstall,
    install_dir: PLUGINS_INSTALL_DIR
)

install_data('schema/com.github.zalesyc.budgie-media-player-applet.gschema.xml',
    install_dir: '/usr/share/glib-2.0/schemas'
    )
meson.add_install_script('meson_post_install.py')

subdir('src')
subdir('icons')
