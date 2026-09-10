# Information

This is a tool designed for Minecraft Speedrunning in the All Portals category. 
It allows for both solo and coop Stronghold Ring calculations and best path traversals.
In coop only 1 player needs to download and use this tool.

## Main Page

![](images/window.png?raw=true)

### Stronghold Ring Locations
Here you enter locations of the starter room for each stronghold in a ring to get close estimate of where the other strongholds will be within the ring.

Each ring set has validation to make sure the stronghold is within the bounds of the ring. The optimal blind coordinate is on the top right of the widget.

### Overview Canvas
This showcases the stronghold locations and once generated the paths and their status. It's not ultimately necessary but good visual reference.

## Player Manager Menu
Here you can:
- Set number of players to generate paths for.
- Generate the paths, which is almost instant for 1 player but takes a minute for multiple.
- "Copy To Clipboard" which copies all the pathing information for [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava).



# Usage

1. Download CrayonAllPortals_v1_2.exe from releases.
2. Run the downloaded executable file.
3. The first step of an All Portals speedrun is to measure and gather the location of a stronghold in each ring. Which can be done with the help of [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava). The X and Z coordinate of each stronghold can be inputted into the Stronghold Ring Locations and if the locations are out of bounds the program will error. Doing this will generate the optimal measuring locations for each stronghold and create an optimal route.

7. Within the Player Manager Menu widget you can now set the number of players which will create the number of paths you desire.
8. Now, we can generate some paths in by clicking "Generate" which is almost instant for 1 player but takes a minute for multiple.
9. With our paths generated you will be see the Overview Canvas populate with paths and each player will have a list of stronghold numbers within their widget. These can be edited to change the path live. Additionally, the color of the Player ID is equal to the color of the path on the Canvas Overview.
10. Now we can click the "Copy to Clipboard" button which lets us receive parseable text like the example below that can be inputted into the [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava). Each player can then enter their given path and traverse through each stronghold 1 by 1. Which is where the critical use of the tool ends.
```text
All Portals Paths

"0:Crayon"
[3,2024,310]
[21,10085,5017]
[22,7172,8685]
[23,3020,10852]
[11,4866,6591]
[5,3284,3928]

"1:Noyarc"
[7,-5044,880]
[14,-7772,2591]
[27,-11108,1869]
[26,-9387,6225]
[13,-4764,6664]
[25,-6044,9505]
[24,-1655,11142]
[12,62,8192]
[6,-1760,4808]

"2:Common"
[2,-744,-1908]
[8,-3284,-3928]
[16,-4866,-6591]
[31,-697,-11242]
[30,-5210,-9987]
[29,-8821,-7004]
[28,-10908,-2811]
[15,-7810,-2472]

"3:Nommoc"
[19,7772,-2591]
[34,10477,-4137]
[33,7888,-8041]
[18,4764,-6664]
[32,3936,-10554]
[17,-62,-8192]
[9,1760,-4808]
```

# Build

### Install Packages
`
python -m pip install -r requirements.txt
python -m pip install pyinstaller
`

### Build with PowerShell:
`
python -m PyInstaller --onefile --windowed --icon=icon.ico --collect-all ortools --name CrayonAllPortals_v1_2 --add-data "simple_rings.png;." CrayonAllPortals.py
`
