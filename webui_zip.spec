# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

import rapidocr_onnxruntime


block_cipher = None

# 参考 https://github.com/RapidAI/RapidOCR/blob/main/ocrweb/rapidocr_web/ocrweb.spec
package_name = "rapidocr_onnxruntime"
install_dir = Path(rapidocr_onnxruntime.__file__).resolve().parent

onnx_paths = list(install_dir.rglob("*.onnx"))
yaml_paths = list(install_dir.rglob("*.yaml"))

onnx_add_data = [(str(v.parent), f"{package_name}/{v.parent.name}") for v in onnx_paths]

yaml_add_data = []
for v in yaml_paths:
    if package_name == v.parent.name:
        yaml_add_data.append((str(v.parent / "*.yaml"), package_name))
    else:
        yaml_add_data.append(
            (str(v.parent / "*.yaml"), f"{package_name}/{v.parent.name}")
        )

add_data = list(set(yaml_add_data + onnx_add_data))


mower_a = Analysis(
    ["webview_ui.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("arknights_mower/fonts", "arknights_mower/__init__/fonts"),
        ("arknights_mower/models", "arknights_mower/__init__/models"),
        ("arknights_mower/templates", "arknights_mower/__init__/templates"),
        ("arknights_mower/resources", "arknights_mower/__init__/resources"),
        ("arknights_mower/data", "arknights_mower/__init__/data"),
        ("arknights_mower/ocr", "arknights_mower/__init__/ocr"),
        ("arknights_mower/vendor", "arknights_mower/__init__/vendor"),
        ("arknights_mower/solvers", "arknights_mower/__init__/solvers"),
        (
            "venv/Lib/site-packages/onnxruntime/capi/onnxruntime_providers_shared.dll",
            "onnxruntime/capi/",
        ),
        ("venv/Lib/site-packages/shapely/DLLs/geos.dll", "."),
        ("venv/Lib/site-packages/shapely/DLLs/geos_c.dll", "."),
        ("logo.png", "."),
    ]
    + add_data,
    hiddenimports=["imghdr", "imgaug", "scipy.io", "lmdb"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

mower_pyz = PYZ(mower_a.pure, mower_a.zipped_data, cipher=block_cipher)

mower_exe = EXE(
    mower_pyz,
    mower_a.scripts,
    [],
    exclude_binaries=True,
    name="mower",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="logo.ico",
)

coll = COLLECT(
    mower_exe,
    mower_a.binaries,
    mower_a.zipfiles,
    mower_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="mower",
)
