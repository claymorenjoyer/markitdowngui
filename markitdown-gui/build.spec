# PyInstaller spec for MarkItDown GUI.
# Build with:  pyinstaller build.spec --noconfirm
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Packages that ship data files / native libs / dynamically-imported submodules
# that PyInstaller's static analysis would otherwise miss.
_DATA_PACKAGES = [
    "markitdown",            # entry points + converters
    "magika",                # ML model files used for type detection
    "onnxruntime",           # native runtime behind magika
    "pdfminer",              # CMap data files for PDF text extraction
    "pdfplumber",
    "pptx",                  # python-pptx default templates
    "docx",                  # python-docx default templates
    "openpyxl",
    "xlrd",
    "olefile",
    "charset_normalizer",
    "markdownify",
    "bs4",
    "soupsieve",
    "lxml",
    "PIL",
    "youtube_transcript_api",
]

datas, binaries, hiddenimports = [], [], []

for pkg in _DATA_PACKAGES:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as exc:  # package not installed -> skip
        print(f"[build.spec] skipping {pkg}: {exc}")

# markitdown imports some converters lazily; pull in all submodules to be safe.
hiddenimports += collect_submodules("markitdown")

a = Analysis(
    ["app/main.py"],
    pathex=["app"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MarkItDownGUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,   # macOS: allow dropping files onto the app icon
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="MarkItDownGUI",
)

# macOS application bundle.
app = BUNDLE(
    coll,
    name="MarkItDownGUI.app",
    icon=None,
    bundle_identifier="com.markitdown.gui",
)
