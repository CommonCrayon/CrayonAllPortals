
# Usage

1. Install

2. Run

3. Enter Data

4. Boom


# TODO

1. Better Path Tracking Algorithm
2. Player Path Depth Control
3. Ideal Path for discovering portals in new ring calculator
4. Angle to stronghold from position calculator

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
