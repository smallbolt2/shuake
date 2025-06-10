# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=['C:\\Users\\Administrator\\Desktop\\mooc-python'],  # 修改为你的项目路径
    binaries=[],
    datas=[
        ('templates/index.html', 'templates'),
        ('static/css/style.css', 'static/css'),
        ('static/js/main.js', 'static/js'),
        ('config.json', '.'),
        ('mooc', 'mooc'),
        ('icon.ico', '.')
    ],
    hiddenimports=[
        'engineio.async_drivers.threading',
        'flask_socketio',
        'mooc.user'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='smallbolt2',  # 生成的exe文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设置为False可以隐藏控制台窗口
    icon='icon.ico',  # 可选：应用图标
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='smallbolt2',
)