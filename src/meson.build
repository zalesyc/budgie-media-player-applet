budgie_library_version = configure_file(
    input: 'BudgieApiVersions.py.in',
    output: 'BudgieApiVersions.py',
    configuration: {'X11': budgie_2 ? '2.0' : '1.0'}
)

install_data(
    'applet.py',
    'SingleAppPlayer.py',
    'PanelControlView.py',
    'BudgieMediaPlayer.py',
    'PopupPlasmaControlView.py',
    'EnumsStructs.py',
    'mprisWrapper.py',
    'SettingsPage.py',
    'Labels.py',
    'FixedSizeBin.py',
    'Popover.py',
    budgie_library_version,
    install_dir: PLUGINS_INSTALL_DIR
)
