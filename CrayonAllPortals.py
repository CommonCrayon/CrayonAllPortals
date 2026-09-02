import customtkinter as ctk
from  CustomTkinterMessagebox  import  *

from PIL import Image, ImageTk
import numpy as np
import sys, os, math

from StrongholdObject import StrongholdObject
from PlayerManager import PlayerManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

STRONGHOLDS_PER_RING = [3, 6, 10, 15, 21, 28, 36, 10]

MAGNITUDE_PER_RING = [2048, 5120, 8192, 11264, 14336, 17408, 20480, 23552]
BOUNDS_PER_RING = [(1280, 2816), (4352, 5888), (7424, 8960), (10496, 12032), (13568, 15104), (16640, 18176), (19712, 21248), (22784, 24320)]

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

        # ctk.deactivate_automatic_dpi_awareness()
        # ctk.set_widget_scaling(1)  # widget dimensions and text size
        # ctk.set_window_scaling(1)  # window geometry dimensions

        # self.geometry("1280x980")

        self.stronghold_objects = []
        self.image_size = 869 # Size of simple_rings.png
        self.player_management_window = None

        # Configure weight so scroll frames expand properly
        # self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # Contains all widget references for strongholds
        self.stronghold_widgets = []
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
        ctk.CTkButton(player_manager_menu_frame, text="SET", font=("Arial", 18), command=self.set_player_number).grid(row=2, column=0, columnspan=2, sticky="nesw", pady=5, padx=10)

        # Generate a path and assign strongholds to players
        ctk.CTkButton(player_manager_menu_frame, text="Generate Path", font=("Arial", 18), command=self.generate_path).grid(row=3, column=0, columnspan=2, sticky="nesw", pady=5, padx=10)

        # Copy to Clipboard
        ctk.CTkButton(player_manager_menu_frame, text="Copy to Clipboard", font=("Arial", 18), command=self.copy_paths_to_clipboard).grid(row=4, column=0, columnspan=2, sticky="nesw", pady=(5, 10), padx=10)

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
        # Default 1 Player Frame
        #======================================================================================================================
        frame = ctk.CTkFrame(self.scrollable_window)
        frame.grid(row=0, column=0, pady=5, padx=5, sticky="nsw")

        # Player Id
        ctk.CTkLabel(frame, text=f"Player 1", font=("Arial", 18), text_color=self.colors[0]).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Player Name
        player_name_entry = ctk.CTkEntry(frame, placeholder_text="Name", font=("Arial", 18))
        player_name_entry.grid(row=1, column=0, padx=5, pady=(0,5), sticky="nesw")
        player_name_entry.bind("<KeyRelease>", lambda event: self.update_stronghold_ids(0))

        # Path by stronghold id
        ctk.CTkLabel(frame, text="Stronghold Ids (0)", font=("Arial", 18), anchor="w").grid(row=2, column=0, padx=5, sticky="nesw")

        # Textbox for Stronghold Ids
        textbox = ctk.CTkTextbox(frame, font=("Arial", 18))
        textbox.grid(row=3, column=0, padx=5, pady=5, sticky="nesw")
        textbox.bind("<KeyRelease>", lambda event: self.update_stronghold_ids(0))

        # Complete All Button 
        ctk.CTkButton(frame, text="Complete All", font=("Arial", 18), command=lambda i=0: self.update_stronghold_ids(0)).grid(row=4, column=0, padx=5, pady=(0, 5), sticky="nesw")


    #==========================================================================================

    def set_player_number():
        pass

    def generate_path():
        pass

    def copy_paths_to_clipboard():
        pass

    def update_stronghold_ids():
        pass

    def update_stronghold_ids():
        pass
    

    #==========================================================================================

    def update_ring(self, ring, x, z):

        ring_val = int(ring.get()) - 1

        # Validate X
        x_raw = x.get().strip()
        try:
            x_val = int(x_raw)
        except ValueError:
            CTkMessagebox.messagebox(title="Invalid X Value", text="X must be an integer.", sound='off')
            return

        # Validate Z
        z_raw = z.get().strip()
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
            sh = StrongholdObject(app=self, ring=ring_val, index=i, x=x, z=z, angle=angle)

            # Handle first stronghold enter, the stronghold used to calculate ring angle
            if i == 0:
                if (self.ring_set_status_combobox.get() == "Active"):
                    sh.set_status("ACT")
                elif (self.ring_set_status_combobox.get() == "Complete"):
                    sh.set_status("COM")

            # Append to list
            self.stronghold_objects.append(sh)

        # Refresh Lists
        self.filter_remaining_strongholds()
        self.filter_active_strongholds()
        self.filter_complete_strongholds()

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
        for sh in self.stronghold_objects:
            sh.draw_on_canvas()


if __name__ == "__main__":
    app = App()
    app.mainloop()
