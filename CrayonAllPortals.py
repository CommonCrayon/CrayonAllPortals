import customtkinter as ctk
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

        self.geometry("1280x980")

        self.stronghold_objects = []
        self.image_size = 869 # Size of simple_rings.png
        self.player_management_window = None

        # Configure weight so scroll frames expand properly
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        self.grid_rowconfigure(0, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # Contains all widget references for strongholds
        self.stronghold_widgets = []

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
        self.image_frame.grid(row=0, column=1, columnspan=2, sticky="nsew", pady=10)

        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)

        self.canvas = ctk.CTkCanvas(self.image_frame, bg="#2B2B2B", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Load original image once
        self.original_image = Image.open(img_path)

        # Bind canvas resize
        self.canvas.bind("<Configure>", self.resize_canvas_frame)

        #======================================================================================================================
        # Player Path
        #======================================================================================================================
        mini_menu_frame = ctk.CTkFrame(self)
        mini_menu_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        mini_menu_frame.grid_columnconfigure(0, weight=1)
        mini_menu_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(mini_menu_frame, text="Mini Menu", font=("Arial", 20)).grid(row=0, column=0, columnspan=2, sticky="new", padx=10, pady=(10, 20))

        # Player Manager Button
        ctk.CTkButton(mini_menu_frame, text="Open Player Manager", font=("Arial", 18, "bold"), command=self.player_manager).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nesw")

        # When setting a stronghold ring, what happens to the stronghold that was used to set it.
        ctk.CTkLabel(mini_menu_frame, text="Ring Status Set:", font=("Arial", 18)).grid(row=2, column=0, padx=(10, 0), pady=10, sticky="nesw")
        self.ring_set_status_combobox = ctk.CTkComboBox(mini_menu_frame, values=["Remaining", "Active", "Complete"])
        self.ring_set_status_combobox.grid(row=2, column=1, padx=(0, 10), pady=10, sticky="nesw")
        self.ring_set_status_combobox.set("Active")

        #======================================================================================================================
        # Strongholds List Panels
        #======================================================================================================================
        # ===== ACTIVE STRONGHOLDS =====
        self.active_count = ctk.StringVar(value="Active (0)")

        active_panel = ctk.CTkFrame(self)
        active_panel.grid(row=0, column=3, rowspan=2, sticky="nsew", padx=10, pady=10)

        active_label = ctk.CTkLabel(active_panel, textvariable=self.active_count, font=("Arial", 20))
        active_label.grid(row=0, column=0, sticky="ne", padx=5, pady=5)

        # Search variable
        self.active_search_var = ctk.StringVar()
        self.active_search_var.trace_add("write", self.filter_active_strongholds)
        active_search_entry = ctk.CTkEntry(active_panel, textvariable=self.active_search_var, width=64, font=("Arial", 16))
        active_search_entry.grid(row=0, column=1, sticky="ne", padx=8, pady=(6, 0))

        # List
        self.active_list = ctk.CTkScrollableFrame(active_panel, width=256)
        self.active_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        active_panel.grid_rowconfigure(1, weight=1)
        active_panel.grid_columnconfigure(0, weight=1)
        active_panel.grid_columnconfigure(1, weight=1)

        # ===== REMAINING STRONGHOLDS =====
        self.remaining_count = ctk.StringVar(value="Remain (0)")

        remaining_panel = ctk.CTkFrame(self)
        remaining_panel.grid(row=1, column=1, sticky="nsew", padx=(0, 5), pady=(0, 10))

        remaining_label = ctk.CTkLabel(remaining_panel, textvariable=self.remaining_count, font=("Arial", 20))
        remaining_label.grid(row=0, column=0, sticky="ne", padx=5, pady=5)

        # Search variable
        self.remaining_search_var = ctk.StringVar()
        self.remaining_search_var.trace_add("write", self.filter_remaining_strongholds)
        remaining_search_entry = ctk.CTkEntry(remaining_panel, textvariable=self.remaining_search_var, width=64, font=("Arial", 16))
        remaining_search_entry.grid(row=0, column=1, sticky="ne", padx=8, pady=(6, 0))

        # List
        self.remaining_list = ctk.CTkScrollableFrame(remaining_panel, width=256)
        self.remaining_list.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        remaining_panel.grid_rowconfigure(2, weight=1)
        remaining_panel.grid_columnconfigure(0, weight=1)
        remaining_panel.grid_columnconfigure(1, weight=1)

        # ===== COMPLETED STRONGHOLDS =====
        self.completed_count = ctk.StringVar(value="Complete (0)")

        completed_panel = ctk.CTkFrame(self)
        completed_panel.grid(row=1, column=2, sticky="nsew", padx=(5, 0), pady=(0, 10))

        completed_label = ctk.CTkLabel(completed_panel, textvariable=self.completed_count, font=("Arial", 20))
        completed_label.grid(row=0, column=0, sticky="ne", padx=5, pady=5)

        # Search variable
        self.complete_search_var = ctk.StringVar()
        self.complete_search_var.trace_add("write", self.filter_complete_strongholds)
        complete_search_entry = ctk.CTkEntry(completed_panel, textvariable=self.complete_search_var, width=64, font=("Arial", 16))
        complete_search_entry.grid(row=0, column=1, sticky="ne", padx=8, pady=(6, 0))

        self.completed_list = ctk.CTkScrollableFrame(completed_panel, width=256)
        self.completed_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        completed_panel.grid_rowconfigure(1, weight=1)
        completed_panel.grid_columnconfigure(0, weight=1)
        completed_panel.grid_columnconfigure(1, weight=1)


    #==========================================================================================
    # STRONGHOLD FILTERS
    #==========================================================================================

    def filter_remaining_strongholds(self, *_):
        query = self.remaining_search_var.get().strip()

        # Get filtered stronghold widgets
        if not query:
            filtered = self.stronghold_widgets
        else:
            filtered = [s for s in self.stronghold_widgets if query.lower() in str(s.number)]

        count = 0

        # Update Filter
        for sh in self.stronghold_widgets:
            count += sh.update_from_filter("REM", set(filtered))

        # Update counts
        self.remaining_count.set(f"Remain ({count})")


    def filter_active_strongholds(self, *_):
        query = self.active_search_var.get().strip()

        # Get filtered stronghold widgets
        if not query:
            filtered = self.stronghold_widgets
        else:
            filtered = [s for s in self.stronghold_widgets if query.lower() in str(s.number)]

        count = 0

        # Update Filter
        for sh in self.stronghold_widgets:
            count += sh.update_from_filter("ACT", set(filtered))

        # Update counts
        self.active_count.set(f"Active ({count})")


    def filter_complete_strongholds(self, *_):
        query = self.complete_search_var.get().strip()

        # Get filtered stronghold widgets
        if not query:
            filtered = self.stronghold_widgets
        else:
            filtered = [s for s in self.stronghold_widgets if query.lower() in str(s.number)]

        count = 0

        # Update Filter
        for sh in self.stronghold_widgets:
            count += sh.update_from_filter("COM", set(filtered))

        # Update counts
        self.completed_count.set(f"Complete ({count})")

    #==========================================================================================

    def update_ring(self, ring, x, z):

        ring_val = int(ring.get()) - 1
        x_val = int(x.get())
        z_val = int(z.get())

        # Get current ring bounds
        lower, upper = BOUNDS_PER_RING[ring_val]

        # Compute distance from origin
        distance = math.sqrt(x_val**2 + z_val**2)

        # Check if distance within bounds. If not show error
        if not (lower <= distance <= upper):

            error_win = ctk.CTkToplevel(self)
            error_win.title("Invalid Coordinates")
            error_win.transient(self)
            error_win.grab_set()

            error_win.attributes("-topmost", True)

            ctk.CTkLabel(error_win, text=f"{x_val} and {z_val} are NOT in bounds of Ring {ring_val+1}", text_color="red", font=("Arial", 18)).pack(padx=20, pady=20)

            ctk.CTkButton(error_win, text="OK", command=error_win.destroy, font=("Arial", 18)).pack(pady=10)

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

    
    def player_manager(self):
        if self.player_management_window is None or not self.player_management_window.winfo_exists():
            self.player_management_window = PlayerManager(self, self.stronghold_objects)
        else:
            self.player_management_window.deiconify()
            self.player_management_window.focus()



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
