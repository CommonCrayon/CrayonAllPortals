
# Usage

1. Install

2. Run

3. Enter Data

4. Boom


# TODO
1. Add real method to update ordering of player
2. Split by Pie, Do Closest First, Do Closest to Furtherest Zig Zag
3. Data Validation when clicking set on rings.
4. Redraw paths on canvas resize
5. Larger font on widgets
6. Larger font for active, smaller for rest


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