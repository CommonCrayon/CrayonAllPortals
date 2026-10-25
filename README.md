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
This showcases the stronghold locations and once generated the paths and their status. It's not ultimately necessary but good visual reference. Each stronghold dot takes the colour of the path it's on (pink means not on a path yet, green is the ring's measured stronghold), and an arrow from spawn points at each path's first stronghold so you can see which way the list runs.

## Player Manager Menu
Here you can:
- Set number of players to generate paths for.
- Set how long the solver may spend generating paths with "Time (s)" (default 60, anywhere from 1 to 3600). More time can find shorter routes for multiple players.
- Turn the path optimisers on or off (see below).
- Generate the paths, which is almost instant for 1 player but uses the full time for multiple players (or with "Respawn at previous bed" on). While it runs the window stays usable: the map draws the best routes found so far, and a panel over the path boxes shows the time left, what the solver is doing, how many better routes it has found (and how long ago the last one was), the total travel, how much shorter it is than the first solution, and the strongholds and nether blocks of each path. Stop ends it early and keeps the best paths found so far (or your previous paths if it hadn't found any yet). If "last improvement" keeps climbing, more time probably won't help; if it keeps improving right up to the end, try a longer time.
- Press Enter in a ring's X/Z box or the Players box instead of clicking SET.
- "Reset" (click it twice to confirm) clears the rings, players, settings and paths back to a fresh start.
- Name each player in their path's box. Names appear in the NavAssist headers (e.g. `Path 1 - Crayon & Noyarc`).
- Each path has its own "Copy" button that copies just that path, so every player can paste only their own strongholds into NavAssist.
- "Copy for NavAssist" which copies all the pathing information for [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava).

### Path Optimisers
By default every leg is flown from a bed placed at the stronghold you just finished. Two optional optimisers can be ticked:
- **Respawn at spawn**: skip the bed so you respawn at world spawn when that's closer to the next stronghold. NavAssist shows `DO NOT PLACE BED!` on those strongholds.
- **Respawn at previous bed**: keep the bed you already have set (left at an earlier stronghold) when that's closer. NavAssist shows `KEEP CURRENT BED!` on those strongholds. With this on, the solver plans routes around it too, so generating uses the full time even for 1 player.

The notes in "Copy for NavAssist" always follow the current checkboxes.

### How Paths Are Balanced
The solver estimates each path's time as **5 minutes per stronghold** plus **travel at 30 nether blocks per second**, then shares that between the path's players. It balances those times so every path finishes at about the same time, so it will give a path an extra stronghold when that saves another path a long trip. Both numbers are `STRONGHOLD_SECONDS` and `TRAVEL_SPEED` at the top of `PathSolver.py`.

### Player Weights
Players are paired onto shared paths in order (P1 + P2 on Path 1, P3 + P4 on Path 2, ...), and with an odd player count the last player gets a solo path. Each path shows a weight box per player.

A weight is how fast that player is compared to the others: a player with weight 2 gets through strongholds and travel twice as fast, so they're given about twice the work. A path's speed is the sum of its players' weights, so with 4 players where P1 and P2 are twice as fast (2, 2, 1, 1), Path 1 gets about twice the work of Path 2 (around 81 strongholds to 40, depending on where they are). To put the fast players on different paths instead, use weights like 2, 1, 2, 1. Weights can be anything from 0.1 to 10.



### Sessions
Everything you enter (ring locations, players, names, weights, time, optimisers and paths) is saved as you go and loaded the next time you open the app, so a crash or restart mid-run doesn't lose anything. The session is stored in `%APPDATA%\CrayonAllPortals\session.json`; delete that file to start fresh.



# Usage

1. Download CrayonAllPortals_v1_2.exe from releases.
2. Run the downloaded executable file.
3. The first step of an All Portals speedrun is to measure and gather the location of a stronghold in each ring. Which can be done with the help of [CrayonNavAssist](https://github.com/CommonCrayon/CrayonAllPortalsJava). The X and Z coordinate of each stronghold can be inputted into the Stronghold Ring Locations and if the locations are out of bounds the program will error. Doing this will generate the optimal measuring locations for each stronghold and create an optimal route.

7. Within the Player Manager Menu widget you can now set the number of players which will create the number of paths you desire.
8. Now, we can generate some paths in by clicking "Generate" which is almost instant for 1 player but uses the full "Time (s)" for multiple.
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

### Quick build
Set the version in `version.txt` (e.g. `1_6`; the app shows it in its title bar), then double-click `build.bat`. It checks the packages, then builds `dist\CrayonAllPortals_v<version>.exe` with the icon, logo and version bundled. It uses `portals_venv` if that folder exists, otherwise the Python on your PATH.

### Manual build
Install packages:
`
python -m pip install -r requirements.txt
python -m pip install pyinstaller
`

Build with PowerShell:
`
python -m PyInstaller --onefile --windowed --icon=icon.ico --collect-all ortools --name CrayonAllPortals_v1_6 --add-data "simple_rings.png;." --add-data "icon.ico;." --add-data "logo.png;." --add-data "version.txt;." CrayonAllPortals.py
`
