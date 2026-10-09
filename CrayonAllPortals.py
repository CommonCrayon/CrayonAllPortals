import customtkinter as ctk
from  CustomTkinterMessagebox  import  *

from PIL import Image, ImageTk
import numpy as np
import sys, os, math

from StrongholdObject import StrongholdObject
from PathSolver import solve_player_paths

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

STRONGHOLDS_PER_RING = [3, 6, 10, 15, 21, 28, 36, 10]
STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]

MAGNITUDE_PER_RING = [2048, 5120, 8192, 11264, 14336, 17408, 20480, 23552]
BOUNDS_PER_RING = [(1280, 2816), (4352, 5888), (7424, 8960), (10496, 12032), (13568, 15104), (16640, 18176), (19712, 21248), (22784, 24320)]

WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN

ADVANCED_PATHING = False

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

img_path = resource_path("simple_rings.png")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Crayon All Portals")

        # ctk.deactivate_automatic_dpi_awareness()
        # ctk.set_widget_scaling(1)  # widget dimensions and text size
        # ctk.set_window_scaling(1)  # window geometry dimensions

        self.geometry("1000x980")
        self.image_size = 869 # Size of simple_rings.png
        self.player_management_window = None

        # Stronghold variables
        self.stronghold_objects = []
        self.num_of_players = 1
        self.num_of_paths = 1
        self.player_paths = [[[0, ""]]]

        # Configure weight so scroll frames expand properly
        # self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # Contains all widget references for strongholds
        self.colors = ["cyan", "magenta", "yellow", "orange", "purple", "red", "blue", "green", "brown", "pink", "lime", "navy", "teal", "gold"]

        #======================================================================================================================
        # Stronghold Ring Reference
        #======================================================================================================================
        sidebar = ctk.CTkFrame(self)
        sidebar.grid(row=0, column=0, sticky="nesw", padx=10, pady=10)

        sidebar.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(sidebar, text="Stronghold Ring Locations", font=("Arial", 20))
        title.grid(row=0, column=0, padx=10, pady=10)

        # Make a entry box for all 8 rings
        for i in range(8):
            row_frame = ctk.CTkFrame(sidebar)
            row_frame.grid(row=i+1, column=0, sticky="nsew", padx=4, pady=4)

            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)

            row_frame.grid_rowconfigure(0, weight=1)
            row_frame.grid_rowconfigure(1, weight=1)

            # Ring
            ctk.CTkLabel(row_frame, text=f"Ring {i+1}", font=("Arial", 18)).grid(row=0, column=0, sticky="w", padx=(5, 0), pady=(5, 0))

            # blind label
            ctk.CTkLabel(row_frame, text=f"OW: {MAGNITUDE_PER_RING[i]} | Nether: {int(MAGNITUDE_PER_RING[i]/8)}").grid(row=0, column=1, columnspan=2, sticky="e", padx=(0, 5), pady=(5, 0))

            # X and Z Strings
            stronghold_ring_string = ctk.StringVar(value=f"{i+1}")
            x_coordinate_string = ctk.StringVar(value="")
            z_coordinate_string = ctk.StringVar(value="")

            # X input box
            entry_x = ctk.CTkEntry(row_frame, placeholder_text="X Coord", textvariable=x_coordinate_string, width=96, font=("Arial", 16))
            entry_x.grid(row=1, column=0, sticky="w", padx=(5, 0), pady=5)

            # Z input box
            entry_z = ctk.CTkEntry(row_frame, placeholder_text="Z Coord", textvariable=z_coordinate_string, width=96, font=("Arial", 16))
            entry_z.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=5)

            # Update Button
            ring_button = ctk.CTkButton(row_frame, text="SET", width=64, font=("Arial", 16, 'bold'), command=lambda ring=stronghold_ring_string, x=x_coordinate_string, z=z_coordinate_string: self.update_ring(ring, x, z))
            ring_button.grid(row=1, column=2, sticky="e", padx=5, pady=5)


        #======================================================================================================================
        # Image
        #======================================================================================================================

        self.image_frame = ctk.CTkFrame(self)
        self.image_frame.grid(row=0, column=1, columnspan=2, sticky="nsew", pady=10, padx=(0, 10))

        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)

        self.canvas = ctk.CTkCanvas(self.image_frame, bg="#2B2B2B", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Load original image once
        self.original_image = Image.open(img_path)

        # Bind canvas resize
        self.canvas.bind("<Configure>", self.resize_canvas_frame)

        #======================================================================================================================
        # Player Manager Menu
        #======================================================================================================================
        player_manager_menu_frame = ctk.CTkFrame(self)
        player_manager_menu_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        player_manager_menu_frame.grid_columnconfigure(0, weight=1)
        player_manager_menu_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(player_manager_menu_frame, text="Player Manager Menu", font=("Arial", 20)).grid(row=0, column=0, columnspan=2, sticky="new", pady=(10, 5))

        ctk.CTkLabel(player_manager_menu_frame, text="Players:", font=("Arial", 18)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        # Number of players entry box
        self.num_players_entry = ctk.CTkEntry(player_manager_menu_frame, textvariable=ctk.StringVar(value="1"), font=("Arial", 18))
        self.num_players_entry.grid(row=1, column=1, sticky="w", pady=5)

        # Number of players Button Set
        ctk.CTkButton(player_manager_menu_frame, text="Set Players", font=("Arial", 18), command=self.set_player_number).grid(row=2, column=0, columnspan=2, sticky="nesw", pady=5, padx=10)

        # Generate a path and assign strongholds to players
        ctk.CTkButton(player_manager_menu_frame, text="Generate Paths (1 Min)", font=("Arial", 18), command=self.generate_path).grid(row=3, column=0, columnspan=2, sticky="nesw", pady=5, padx=10)

        # Copy to Clipboard
        ctk.CTkButton(player_manager_menu_frame, text="Copy for NavAssist", font=("Arial", 18), command=self.copy_paths_to_clipboard).grid(row=4, column=0, columnspan=2, sticky="nesw", pady=(5, 10), padx=10)

        #======================================================================================================================
        # Scrollable Window for each player
        #======================================================================================================================
        scrollable_window_frame = ctk.CTkFrame(self)
        scrollable_window_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))

        scrollable_window_frame.grid_columnconfigure(0, weight=1)
        scrollable_window_frame.grid_rowconfigure(0, weight=1)

        self.scrollable_window = ctk.CTkScrollableFrame(scrollable_window_frame, orientation="horizontal")
        self.scrollable_window.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        #======================================================================================================================
        # Default Path 0 Frame
        #======================================================================================================================
        frame = ctk.CTkFrame(self.scrollable_window)
        frame.grid(row=0, column=0, pady=5, padx=5, sticky="nsw")

        # Player Id
        ctk.CTkLabel(frame, text=f"Solo Path (0)", font=("Arial", 18), text_color=self.colors[0]).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Textbox for Stronghold Ids
        textbox = ctk.CTkTextbox(frame, font=("Arial", 18))
        textbox.grid(row=1, column=0, padx=5, pady=5, sticky="nesw")
        textbox.bind("<KeyRelease>", lambda event: self.update_stronghold_ids(0))

    #==========================================================================================

    def set_player_number(self):
        # Get Number of players
        try:
            num_players = int(self.num_players_entry.get())
            if num_players <= 0 or num_players >= 15:
                raise ValueError
        except:
            CTkMessagebox.messagebox(title="Invalid number of players", text="Number of players must be\ngreater than 0 and less than 15.", sound='off')
            return

        # Players share paths: 2 players per spawn -> spawn loop
        self.num_of_players = num_players
        self.num_of_paths = (num_players + 1) // 2

        current_paths = len(self.scrollable_window.winfo_children())

        # Destroy widgets and pop extra paths
        if self.num_of_paths < current_paths:
            for widget in self.scrollable_window.winfo_children()[self.num_of_paths:]:
                widget.destroy()

            while len(self.player_paths) > self.num_of_paths:
                self.player_paths.pop(self.num_of_paths)

        # Generate frames for new paths if needed
        for i in range(current_paths, self.num_of_paths):
            self.player_paths.append([[i, f"{self.colors[i]}"]])

            frame = ctk.CTkFrame(self.scrollable_window)
            frame.grid(row=0, column=i, pady=5, padx=5, sticky="nsw")

            ctk.CTkLabel(frame, text=f"Path {i+1} (0)", font=("Arial", 18), text_color=self.colors[i]).grid(row=0, column=0, padx=5, pady=5, sticky="w")

            textbox = ctk.CTkTextbox(frame, font=("Arial", 18))
            textbox.grid(row=1, column=0, padx=5, pady=5, sticky="nesw")
            textbox.bind("<KeyRelease>", lambda event, idx=i: self.update_stronghold_ids(idx))

        # Update Everything
        self.update_textbox()
        self.update_path_labels()
        self.draw_paths_on_canvas()



    # Updates the Stronghold Ids of each player
    def update_textbox(self):
        for idx, player_path in enumerate(self.player_paths):

            # Get the textbox for this player
            textbox = self.scrollable_window.winfo_children()[idx].winfo_children()[1]

            # create stronghold IDs list
            stronghold_ids = [str(sh_id) for sh_id, _, _ in player_path[1:]]
            textbox_text = ",".join(stronghold_ids)

            # Update the textbox
            textbox.delete("1.0", "end")
            textbox.insert("end", textbox_text)



    def draw_paths_on_canvas(self):
    


        # Delete previous canvas items if any
        if hasattr(self, "canvas_items"):
            for item in self.canvas_items:
                try:
                    self.canvas.delete(item)
                except Exception:
                    pass
        
        self.canvas_items = []

        side = self.image_size
        offset_x = (self.canvas.winfo_width() - side) // 2
        offset_y = (self.canvas.winfo_height() - side) // 2

        # Spawn (0, 0) on the canvas
        origin_x = int((0 - WORLD_MIN) / WORLD_RANGE * side) + offset_x
        origin_y = int((0 - WORLD_MIN) / WORLD_RANGE * side) + offset_y

        for idx, player_path in enumerate(self.player_paths):

            stops = player_path[1:]
            if not stops:
                continue

            color = self.colors[idx % len(self.colors)]
            prev_x, prev_y = origin_x, origin_y

            for point in stops:
                x, y = point[1], point[2]

                img_x = int((x - WORLD_MIN) / WORLD_RANGE * side) + offset_x
                img_y = int((y - WORLD_MIN) / WORLD_RANGE * side) + offset_y

                line = self.canvas.create_line(prev_x, prev_y, img_x, img_y, fill=color, width=4)
                self.canvas_items.append(line)

                prev_x, prev_y = img_x, img_y

            # Close the loop back at spawn
            if not self.is_solo_path(idx):
                line = self.canvas.create_line(prev_x, prev_y, origin_x, origin_y, fill=color, width=4)
                self.canvas_items.append(line)

        # Redraw canvas markers
        for sh in self.stronghold_objects:
            sh.draw_on_canvas()

    #==========================================================================================

    def is_solo_path(self, idx):
        # With an odd player count the last path belongs to the unpaired player
        return self.num_of_players % 2 == 1 and idx == self.num_of_paths - 1

    def update_path_labels(self):
        frames = self.scrollable_window.winfo_children()
        
        for idx, path in enumerate(self.player_paths):
            label = frames[idx].winfo_children()[0]
            text = f"Path {idx+1} ({len(path) - 1})"

            # With an odd player count the last path belongs to the unpaired player
            if self.is_solo_path(idx):
                text = f"Solo Path ({len(path) - 1})"
            else:
                text = f"Shared Path {idx+1} ({len(path) - 1})"


            label.configure(text=text)

    def generate_path(self):
        valid_strongholds = []

        # Skip any strongholds that were first in the ring.
        for sh in self.stronghold_objects:
            if sh.number not in STRONGHOLDS_RING_START:
                valid_strongholds.append([sh.number, sh.x, sh.z])

        # Compute optimal paths (one per spawn -> spawn loop)
        routes = solve_player_paths(strongholds=valid_strongholds, num_players=self.num_of_players, computation_time=60, advanced_pathing=ADVANCED_PATHING)

        # Reconstruct paths
        new_paths = []
        for i in range(self.num_of_paths):
            header = [i, f"{self.colors[i]}"]
            new_paths.append([header] + routes[i])

        self.player_paths = new_paths

        self.update_textbox()
        self.update_path_labels()
        self.draw_paths_on_canvas()
    #==========================================================================================

    def copy_paths_to_clipboard(self):

        export_text = "All Portals Paths\n"
        spawn = [-1, 0, 0]

        for path_idx, path in enumerate(self.player_paths):
            total_distance = 0
            path_notes = {}

            stops = path[1:]
            route = [spawn] + stops
            if not self.is_solo_path(path_idx):
                route.append(spawn)
            has_return = not self.is_solo_path(path_idx)

            for k in range(len(route) - 1):
                current = route[k]
                next_portal = route[k + 1]
                is_return = has_return and (k == len(route) - 2)

                distance_from_stronghold = math.hypot(current[1] - next_portal[1], current[2] - next_portal[2])

                if not ADVANCED_PATHING:
                    total_distance += distance_from_stronghold
                    continue

                # Advanced: the final reset back to spawn is free
                if is_return:
                    continue

                # From spawn (not applicable when already standing at spawn)
                distance_from_origin = math.hypot(next_portal[1], next_portal[2]) if k > 0 else float("inf")

                # From previous stronghold (needs a stronghold before current)
                if k >= 2:
                    previous = route[k - 1]
                    distance_from_previous = math.hypot(previous[1] - next_portal[1], previous[2] - next_portal[2])
                else:
                    distance_from_previous = float("inf")

                distances = {"stronghold": distance_from_stronghold, "origin": distance_from_origin, "previous": distance_from_previous}
                shortest = min(distances, key=distances.get)

                total_distance += distances[shortest]

                if shortest == "origin":
                    path_notes[k - 1] = f"DO NOT PLACE BED! {round((distance_from_stronghold - distance_from_origin)/8)} nether blocks faster via SPAWN."
                elif shortest == "previous":
                    path_notes[k - 1] = f"KEEP CURRENT BED! {round((distance_from_stronghold - distance_from_previous)/8)} nether blocks faster via CURRENT bed."

            # Divide by 8 for Nether coordinates
            total_distance = round(total_distance / 8)

            export_text += f'\nPath {path[0][0] + 1} = {total_distance} Nether Blocks\n'

            for i, y in enumerate(stops):
                export_text += f"[{y[0]},{y[1]},{y[2]}]"

                if i in path_notes:
                    export_text += f'"{path_notes[i]}"'

                export_text += "\n"

        self.clipboard_clear()
        self.clipboard_append(export_text)

        print("Copied to clipboard!")

    #==========================================================================================

    def update_stronghold_ids(self, player_index):  # player_index is now a path index

        textbox = self.scrollable_window.winfo_children()[player_index].winfo_children()[1]

        # Parse Text
        text = textbox.get("1.0", "end").strip()
        text = text.replace(" ", "")
        raw_ids = [item for item in text.split(",") if item]

        try:
            stronghold_ids = [int(x) for x in raw_ids]
        except ValueError:
            print("Failed to Parse Stronghold Ids!")
            return  # previously fell through with stronghold_ids undefined

        new_path = [[player_index, f"{self.colors[player_index]}"]]

        for stronghold_id in stronghold_ids:
            sh = next((sh for sh in self.stronghold_objects if sh.number == stronghold_id), None)

            if sh is None:
                print(f"Stronghold {stronghold_id} not found!")
                continue

            new_path.append([stronghold_id, sh.x, sh.z])

        self.player_paths[player_index] = new_path

        self.update_path_labels()
        self.draw_paths_on_canvas()

    #==========================================================================================

    def update_ring(self, ring, x, z):

        ring_val = int(ring.get()) - 1
        F3Cprefix = "/execute in minecraft:overworld run tp @s"
        # "/execute in minecraft:overworld run tp @s 244.14 70.00 83.08 -45.56 1.22" 

        # Read inputs
        x_raw = x.get().strip()
        z_raw = z.get().strip()

        # Check if either input contains the F3+C command
        if F3Cprefix in x_raw:
            raw_f3 = x_raw
        elif F3Cprefix in z_raw:
            raw_f3 = z_raw
        else:
            raw_f3 = None


        if raw_f3:
            try:
                # Parse values
                floatList = raw_f3.split(F3Cprefix)[1].strip().split()
                
                x_val = int(float(floatList[0]))
                z_val = int(float(floatList[2]))

                # Update both entry fields
                x.set(str(x_val))
                z.set(str(z_val))

            except (IndexError, ValueError):
                CTkMessagebox.messagebox(title="Invalid F3+C String", text="Could not parse coordinates from the F3+C string.", sound='off')
                return
        else:
            # X Validation
            try:
                x_val = int(x_raw)
            except ValueError:
                CTkMessagebox.messagebox(title="Invalid X Value", text="X must be an integer.", sound='off')
                return

            # Z Validation
            try:
                z_val = int(z_raw)
            except ValueError:
                CTkMessagebox.messagebox(title="Invalid Z Value", text="Z must be an integer.", sound='off')
                return


        # Validate Bounds. Check if distance within bounds. If not show error
        if not (BOUNDS_PER_RING[ring_val][0] <= math.sqrt(x_val**2 + z_val**2) <= BOUNDS_PER_RING[ring_val][1]):
            CTkMessagebox.messagebox(title="Invalid Coordinates", text=f"{x_val} and {z_val} are NOT in bounds of Ring {ring_val+1}", sound='off')
            return

        print(f"Updated Ring {ring_val+1} → X={x_val}, Z={z_val}")

        # Remove OLD strongholds from this stronghold ring
        ring_to_remove = [sh for sh in self.stronghold_objects if sh.ring == ring_val]
        for stronghold in ring_to_remove:
            stronghold.destroy()
            self.stronghold_objects.remove(stronghold)

        # Magnitude of Ring
        magnitude = MAGNITUDE_PER_RING[ring_val]
        base_angle = np.arctan2(z_val, x_val)

        # Predict new strongholds
        new_strongholds = []

        for j in range(STRONGHOLDS_PER_RING[ring_val]):
            ang = base_angle + j * (2 * np.pi / STRONGHOLDS_PER_RING[ring_val])

            new_x = magnitude * np.cos(ang)
            new_z = magnitude * np.sin(ang)

            new_strongholds.append([round(new_x), round(new_z), round(np.degrees(ang))])

        # Fix first stronghold to be exact input
        new_strongholds[0] = [x_val, z_val, round(np.degrees(base_angle))]

        # Create new StrongholdObject instances
        for i, [x, z, angle] in enumerate(new_strongholds):
            # Append to list
            self.stronghold_objects.append(StrongholdObject(app=self, ring=ring_val, index=i, x=x, z=z, angle=angle))

    def resize_canvas_frame(self, event):
        # Canvas size
        cw, ch = event.width, event.height

        # Choose square size
        side = min(cw, ch)

        # Resize original image into a square
        img = self.original_image.resize((side, side), Image.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(img)

        # Center position
        x = (cw - side) // 2
        y = (ch - side) // 2

        # Set imagesize for canvas draw
        self.image_size = side

        # Redraw
        self.canvas.delete("all")
        self.canvas.create_image(x, y, anchor="nw", image=self.bg_img)

        # Redraw canvas markers
        self.draw_paths_on_canvas()


if __name__ == "__main__":
    app = App()
    app.mainloop()
