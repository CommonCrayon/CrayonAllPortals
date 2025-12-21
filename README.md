
# Usage

1. Download CrayonAllPortals.exe from releases.

2. Run downloaded executable file.

![](images/example.png?raw=true)

# BUILD

### Install Packages
`
python -m pip install -r requirements.txt
python -m pip install pyinstaller
`


### Build with PowerShell:
`
python -m PyInstaller --onefile --windowed --icon=icon.ico --collect-all ortools --name CrayonAllPortals_v1_0 --add-data "simple_rings.png;." CrayonAllPortals.py
`
