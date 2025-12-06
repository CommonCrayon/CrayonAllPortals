import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np
import sys, os

from StrongholdObject import StrongholdObject

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

STRONGHOLDS_PER_RING = [3, 6, 10, 15, 21, 28, 36, 10]
MAGNITUDE_PER_RING = [2048, 5120, 8192, 11264, 14336, 17408, 20480, 23552]
STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]
WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN



def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

img_path = resource_path("simple_rings.png")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Crayon All Portals")
        self.stronghold_objects = []  # all stronghold objects

        self.player_colors = ["purple", "orange", "cyan", "yellow", "magenta", "lime", "brown"]


        # Configure weight so scroll frames expand properly
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_rowconfigure(0, minsize=32)
        self.grid_rowconfigure(1, weight=1)

        #======================================================================================================================
        # LEFT SIDEBAR 
        #======================================================================================================================
        sidebar = ctk.CTkFrame(self)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nws", padx=10, pady=10)

        title = ctk.CTkLabel(sidebar, text="Stronghold Ring\nLocations", font=("Arial", 18))
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        # Make a entry box for all 8 rings
        for i in range(8):
            row_frame = ctk.CTkFrame(sidebar)
            row_frame.grid(row=i+1, column=0, sticky="nsew", padx=4, pady=4)

            label = ctk.CTkLabel(row_frame, text=f"Stronghold Ring {i+1}")
            label.grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=2)

            # X and Z Strings
            stronghold_ring_string = ctk.StringVar(value=f"{i+1}")
            x_coordinate_string = ctk.StringVar()
            z_coordinate_string = ctk.StringVar()

            # X input box
            entry_x = ctk.CTkEntry(row_frame, placeholder_text="X Coord", width=64, textvariable=x_coordinate_string)
            entry_x.grid(row=1, column=0, sticky="w", padx=4, pady=2)

            # Z input box
            entry_z = ctk.CTkEntry(row_frame, placeholder_text="Z Coord", width=64, textvariable=z_coordinate_string)
            entry_z.grid(row=1, column=1, sticky="w", padx=4, pady=2)

            # Update Button
            ring_button = ctk.CTkButton(
                row_frame,
                text="Update",
                command=lambda ring=stronghold_ring_string, x=x_coordinate_string, z=z_coordinate_string: self.update_ring(ring, x, z)
            )
            ring_button.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=2)


        #======================================================================================================================
        # Image
        #======================================================================================================================

        image_frame = ctk.CTkFrame(self)
        image_frame.grid(row=0, column=1, sticky="nsew", pady=10)

        self.canvas = ctk.CTkCanvas(
            image_frame,
            width=869,
            height=869,
            bg="#2B2B2B",
            highlightthickness=0
        )

        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.original_image = Image.open(img_path)
        self.bg_img = ImageTk.PhotoImage(self.original_image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_img)



        #======================================================================================================================
        # Player Path
        #======================================================================================================================
        player_path_frame = ctk.CTkFrame(self)
        player_path_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 10))

        player_path_frame.grid_columnconfigure(0, weight=1)
        player_path_frame.grid_columnconfigure(1, weight=1)


        # Title
        ctk.CTkLabel(
            player_path_frame,
            text="Player Pathing Generator",
            font=("Arial", 24),
            justify="left"
        ).grid(row=0, column=0, columnspan=2, sticky="new", padx=10, pady=(10, 20))

        # Number of players label
        num_players_label = ctk.CTkLabel(
            player_path_frame,
            text="Number of Players:",
            font=("Arial", 16)
        )
        num_players_label.grid(row=1, column=0, sticky="e", padx=(10, 5), pady=5)

        # Number of players entry box
        self.num_players_entry = ctk.CTkEntry(
            player_path_frame,
            width=120,
            placeholder_text="Enter amount"
        )
        self.num_players_entry.grid(row=1, column=1, sticky="w", padx=(5, 10), pady=5)

        # Generate button
        self.generate_path_button = ctk.CTkButton(
            player_path_frame,
            text="Generate Paths",
            font=("Arial", 16),
            width=160,
            height=38,
            corner_radius=12,
            command=self.generate_paths
        )

        self.generate_path_button.grid(row=2, column=0, columnspan=2, pady=(15, 10))



        #======================================================================================================================
        # Strongholds List Panels
        #======================================================================================================================
        # ACTIVE STRONGHOLDS
        self.active_count = ctk.StringVar(value="Active Strongholds (0)")

        active_panel = ctk.CTkFrame(self)
        active_panel.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=10, pady=10)

        active_label = ctk.CTkLabel(active_panel, textvariable=self.active_count, font=("Arial", 18))
        active_label.grid(row=0, column=0, sticky="new", padx=5, pady=5)

        self.active_list = ctk.CTkScrollableFrame(active_panel, width=256)
        self.active_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        active_panel.grid_rowconfigure(1, weight=1)
        active_panel.grid_columnconfigure(0, weight=1)

        # REMAINING STRONGHOLDS
        self.remaining_count = ctk.StringVar(value="Remaining Strongholds (0)")

        remaining_panel = ctk.CTkFrame(self)
        remaining_panel.grid(row=0, column=3, rowspan=2, sticky="nsew", pady=10)

        remaining_label = ctk.CTkLabel(remaining_panel, textvariable=self.remaining_count, font=("Arial", 18))
        remaining_label.grid(row=0, column=0, sticky="new", padx=5, pady=5)

        self.remaining_list = ctk.CTkScrollableFrame(remaining_panel, width=256)
        self.remaining_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        remaining_panel.grid_rowconfigure(1, weight=1)
        remaining_panel.grid_columnconfigure(0, weight=1)

        # COMPLETED STRONGHOLDS
        self.completed_count = ctk.StringVar(value="Completed Strongholds (0)")

        completed_panel = ctk.CTkFrame(self)
        completed_panel.grid(row=0, column=4, rowspan=2, sticky="nsew", padx=10, pady=10)

        completed_label = ctk.CTkLabel(completed_panel, textvariable=self.completed_count, font=("Arial", 18))
        completed_label.grid(row=0, column=0, sticky="new", padx=5, pady=5)

        self.completed_list = ctk.CTkScrollableFrame(completed_panel, width=256)
        self.completed_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        completed_panel.grid_rowconfigure(1, weight=1)
        completed_panel.grid_columnconfigure(0, weight=1)


    # Updates the Count of the List
    def update_counts(self):
        active = len(self.active_list.winfo_children())
        remaining = len(self.remaining_list.winfo_children())
        completed = len(self.completed_list.winfo_children())

        self.active_count.set(f"Active Strongholds ({active})")
        self.remaining_count.set(f"Remaining Strongholds ({remaining})")
        self.completed_count.set(f"Completed Strongholds ({completed})")

    
    def update_ring(self, ring, x, z):

        ring_val = int(ring.get()) - 1
        x_val = int(x.get())
        z_val = int(z.get())

        print(f"Updated Ring {ring_val+1} → X={x_val}, Z={z_val}")

        # Remove OLD strongholds from this stronghold ring
        ring_to_remove = [sh for sh in self.stronghold_objects if sh.ring == ring_val]
        for stronghold in ring_to_remove:
            stronghold.destroy()
            self.stronghold_objects.remove(stronghold)

        # Predict new strongholds
        coords = []
        magnitude = MAGNITUDE_PER_RING[ring_val]

        # get the angle
        base_angle = np.arctan2(z_val, x_val)

        for j in range(STRONGHOLDS_PER_RING[ring_val]):
            ang = base_angle + j * (2 * np.pi / STRONGHOLDS_PER_RING[ring_val])

            new_x = magnitude * np.cos(ang)
            new_z = magnitude * np.sin(ang)

            coords.append((round(new_x), round(new_z)))

        # Fix first stronghold to be exact input
        coords[0] = (x_val, z_val)

        # Create new StrongholdObject instances
        for idx, (sx, sz) in enumerate(coords):
            sh = StrongholdObject(app=self, ring=ring_val, index=idx, x=sx, z=sz)
            self.stronghold_objects.append(sh)


    def distance(self, p, sh):
        px, pz = p
        return ((sh.x - px)**2 + (sh.z - pz)**2) ** 0.5


    def generate_paths(self):

        # Clear previous path lines
        if hasattr(self, 'path_lines'):
            for line in self.path_lines:
                try:
                    self.canvas.delete(line)
                except:
                    pass
        self.path_lines = []

        # Number of players
        try:
            num_players = int(self.num_players_entry.get())
            if num_players <= 0:
                raise ValueError
        except:
            print("Invalid number of players.")
            return

        players = [f"Player {i+1}" for i in range(num_players)]

        # list only active + remaining strongholds
        strongholds_todo = [sh for sh in self.stronghold_objects if sh.status_var.get() in ("Active", "Remaining")]

        # Initialize player locations to 0 0. MAYBE CHANGE
        player_locations = {player: [0, 0] for player in players}

        while len(strongholds_todo) > 0:

            for idx, player in enumerate(players):

                if len(strongholds_todo) == 0:
                    break

                current_player_location = player_locations[player]

                shortest_distance = float("inf")
                best_sh_i = 0

                # Get closest stronghold to this player's location
                for index, sh in enumerate(strongholds_todo):

                    distance = self.distance(current_player_location, sh)

                    if distance < shortest_distance:
                        shortest_distance = distance
                        best_sh_i = index

                chosen_sh = strongholds_todo[best_sh_i]

                # print(player + " will go to Stronghold: " + str(chosen_sh.index + 1))

                # Draw path
                color = self.player_colors[idx % len(self.player_colors)]

                # Current Player Location X Z
                x1 = int((current_player_location[0] - WORLD_MIN) / WORLD_RANGE * 869)
                z1 = int((current_player_location[1] - WORLD_MIN) / WORLD_RANGE * 869)

                # Next Stronghold Location X Z
                x2 = int((chosen_sh.x - WORLD_MIN) / WORLD_RANGE * 869)
                z2 = int((chosen_sh.z - WORLD_MIN) / WORLD_RANGE * 869)

                # Draw Line
                line = self.canvas.create_line(x1, z1, x2, z2, fill=color, width=3)
                self.path_lines.append(line)

                # update player location
                player_locations[player] = [chosen_sh.x, chosen_sh.z]

                # remove stronghold from future paths
                strongholds_todo.pop(best_sh_i)




if __name__ == "__main__":
    app = App()
    app.mainloop()
