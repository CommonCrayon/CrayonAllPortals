
# Usage

1. Install

2. Run

3. Enter Data

4. Boom


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