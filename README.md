
# Usage

1. Download CrayonAllPortals.exe from releases.

2. Run downloaded executable file.

3. TODO


# TODO

1. Better Path Tracking Algorithm
2. Player Path Depth Control
3. Ideal Path for discovering portals in new ring calculator
4. Angle to stronghold from position calculator

# TODO
- Generation Methods: Split by Pie, Do Closest First, Do Closest to Furtherest Zig Zag

# BUILD

### Install Packages
`
python -m pip install -r requirements.txt
python -m pip install pyinstaller
`


### Build with PowerShell:
`
python -m PyInstaller --onefile --windowed --name CrayonAllPortals_v0_1 --add-data "simple_rings.png;." CrayonAllPortals.py
`
