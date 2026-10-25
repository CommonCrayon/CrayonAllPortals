# Information

This is a tool designed for Minecraft Speedrunning in the All Portals category. 
It allows for both solo and coop Stronghold Ring calculations and best path traversals.
In coop only 1 player needs to download and use this tool.

## Main Page

![](images/guide.png?raw=true)



# Usage

1. Download CrayonAllPortals.exe from releases.
2. Run the downloaded executable file.
3. The first step of an All Portals speedrun is to measure and gather the location of a stronghold in each ring. Which can be done with the help of [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava). The X and Z coordinate of each stronghold can be inputted into the Stronghold Ring Locations and if the locations are out of bounds the program will error. Doing this will generate the optimal measuring locations for each stronghold and create an optimal route.

4. Within the Player Manager Menu widget you can now set the number of players which will create the number of paths you desire.
5. Now, we can generate some paths in by clicking "Generate".
6. With our paths generated you will be see the Overview Canvas populate with paths and each player will have a list of stronghold numbers within their widget. These can be edited to change the path live. Additionally, the color of the Player ID is equal to the color of the path on the Canvas Overview.
10. Now we can click the "Copy for NavAssist" button which lets us receive parseable text like the example below that can be inputted into the [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava). Each player can then enter their given path and traverse through each stronghold 1 by 1. Which is where the critical use of the tool ends.
```text
All Portals Paths

Path 1 - Player 1 & Player 2
[5,941,5033]
[12,118,8191]
[23,2565,10968]
[11,4910,6557]
[22,6804,8977]

Path 2 - Player 3 & Player 4
[2,-1246,1625]
[6,-3888,3331]
[13,-4719,6696]
[25,-6435,9245]
[41,-5786,13117]
```

# Quick build
Set the version in `version.txt`, then double-click `build.bat`. It checks the packages, then builds `dist\CrayonAllPortals_v<version>.exe` with the icon, logo and version bundled.


