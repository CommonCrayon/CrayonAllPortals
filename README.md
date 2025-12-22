# Information

## Main Page

![](images/main_page.png?raw=true)

### Stronghold Ring Locations
Here you enter locations of the starter room for each stronghold in a ring to get close estimate of where the other strongholds will be within the ring.

Each ring set has validation to make sure the stronghold is within the bounds of the ring. The optimal blind coordinate is on the top right of the widget.

### Overview Canvas
This showcases the stronghold locations and once generated the paths and their status. It's not ultimately necessary but good visual reference.

### Active Stronghold Widget
Showcases all the active strongholds.

### Remain Stronghold Widget
Showcases all the remaining strongholds to complete.

### Complete Stronghold Widget
Showcases all the completed strongholds.

### Mini Menu
Here you can open the "Player Manager" which lets you generate and customise paths for both solo and coop.

You can additionally, set "Ring Status Set" which decides the faith of what happens to the strongholds found and entered to determine the rings.

## Player Manager
Here you can customise paths and generate them too. Generation takes about 10 seconds.

![](images/player_manager.png?raw=true)


# Usage

1. Download CrayonAllPortals_v1_0.exe from releases.
2. Run the downloaded executable file.


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
