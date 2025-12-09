
# Usage

1. Install

2. Run

3. Enter Data

4. Boom


# TODO
- Generation Methods: Split by Pie, Do Closest First, Do Closest to Furtherest Zig Zag

- Create text where it gives each player information of where to go.

- Data Validation when clicking set on rings.


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