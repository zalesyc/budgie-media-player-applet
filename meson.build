project('budgie-media-player-applet')


PLUGINS_INSTALL_DIR = join_paths(get_option('libdir'), 'budgie-desktop', 'plugins', meson.project_name())


install_data(
    'budgie-media-player-applet.plugin',
    install_dir: PLUGINS_INSTALL_DIR
)

install_data('schema/com.github.zalesyc.budgie-media-player-applet.gschema.xml',
    install_dir: '/usr/share/glib-2.0/schemas'
    )
meson.add_install_script('meson_post_install.py')

subdir('src')
