project('budgie-media-player-applet')


plugins_install_dir = join_paths(get_option('prefix'), get_option('libdir'), 'budgie-desktop', 'plugins', meson.project_name())


install_data(
    'budgie-media-player-applet.plugin',
    install_dir: plugins_install_dir
)

subdir('src')
