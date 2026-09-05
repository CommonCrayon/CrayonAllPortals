import customtkinter as ctk
from  CustomTkinterMessagebox  import  *

from PIL import Image, ImageTk
import numpy as np
import sys, os, math

from StrongholdObject import StrongholdObject
from PathSolver import make_stronghold_list

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

STRONGHOLDS_PER_RING = [3, 6, 10, 15, 21, 28, 36, 10]
STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]

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

        self.geometry("1000x980")

        self.stronghold_objects = []
        self.image_size = 869 # Size of simple_rings.png
        self.player_management_window = None

        self.num_of_players = 1
        self.player_paths = [[[0, ""]]]

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
        ctk.CTkButton(player_manager_menu_frame, text="Set Players", font=("Arial", 18), command=self.set_player_number).grid(row=2, column=0, columnspan=2, sticky="nesw", pady=5, padx=10)

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
        # Default Path 0 Frame
        #======================================================================================================================
        frame = ctk.CTkFrame(self.scrollable_window)
        frame.grid(row=0, column=0, pady=5, padx=5, sticky="nsw")

        # Player Id
        ctk.CTkLabel(frame, text=f"Path 1 (0)", font=("Arial", 18), text_color=self.colors[0]).grid(row=0, column=0, padx=5, pady=5, sticky="w")

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
        

        # Set Num of Players in object
        self.num_of_players = num_players

        current_players = len(self.scrollable_window.winfo_children())

        # Destroy widgets and Pop extra players
        if self.num_of_players < current_players:
            # Destroy extra widgets
            for widget in self.scrollable_window.winfo_children()[self.num_of_players:]:
                widget.destroy()

            # Remove extra player paths
            while len(self.player_paths) > self.num_of_players:
                self.player_paths.pop(self.num_of_players)



        # Generate frames for new players if needed
        for i in range(current_players, self.num_of_players):
            # Create a player path in index
            self.player_paths.append([[0, f"{self.colors[i]}"]])

            frame = ctk.CTkFrame(self.scrollable_window)
            frame.grid(row=0, column=i, pady=5, padx=5, sticky="nsw")

            # Player Id
            ctk.CTkLabel(frame, text=f"Path {i+1} (0)", font=("Arial", 18), text_color=self.colors[i]).grid(row=0, column=0, padx=5, pady=5, sticky="w")

            # Textbox for Stronghold Ids
            textbox = ctk.CTkTextbox(frame, font=("Arial", 18))
            textbox.grid(row=3, column=0, padx=5, pady=5, sticky="nesw")
            textbox.bind("<KeyRelease>", lambda event, idx=i: self.update_stronghold_ids(idx))

        # Update Everything
        self.update_textbox()
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

        # Use the square image size
        side = self.image_size

        # Offsets for centering
        offset_x = (self.canvas.winfo_width() - side) // 2
        offset_y = (self.canvas.winfo_height() - side) // 2

        # Iterate through each player's path
        for idx, player_path in enumerate(self.player_paths):

            color = self.colors[idx % len(self.colors)]
            prev_x, prev_y = None, None
            
            for point in player_path[1:]:
                x, y = point[1], point[2]

                # Map world coordinates to canvas coordinates
                img_x = int((x - WORLD_MIN) / WORLD_RANGE * side) + offset_x
                img_y = int((y - WORLD_MIN) / WORLD_RANGE * side) + offset_y

                # Draw line from previous point
                if prev_x is not None and prev_y is not None:
                    line = self.canvas.create_line(prev_x, prev_y, img_x, img_y, fill=color, width=4)
                    self.canvas_items.append(line)

                prev_x, prev_y = img_x, img_y


        # Redraw canvas markers
        for sh in self.stronghold_objects:
            sh.draw_on_canvas()

    #==========================================================================================

    def generate_path(self):
        # Clear existing paths
        new_paths = []
        for i in range(self.num_of_players):
            new_paths.append([[i, f"{self.colors[i]}"]])


        # ANGLE SPLITTING
        angle_per_player = 360 / self.num_of_players

        for sh in self.stronghold_objects:

            # Skip any stronghold ring starters
            if sh.number in STRONGHOLDS_RING_START:
                continue

            angle = sh.angle % 360  # Normalize

            # Determine player index
            player_index = int(angle // angle_per_player)
            if player_index >= self.num_of_players:
                player_index = self.num_of_players - 1

            # Add stronghold to the player
            new_paths[player_index].append([sh.number, sh.x, sh.z])


        # Sort each player's strongholds by ID
        for i in range(self.num_of_players):

            sh_points = new_paths[i]
            first_entry = sh_points[0]

            sorted_strongholds = make_stronghold_list(sh_points[1:], math.ceil(10 / self.num_of_players)) # Hardcoded, should take around 10 seconds to calculate
            new_paths[i] = [first_entry] + sorted_strongholds

        # Save into main structure
        self.player_paths = new_paths

        # Update textboxes
        self.update_textbox()

        # Update counts in labels
        for i in range(self.num_of_players):
            count_label = self.scrollable_window.winfo_children()[i].winfo_children()[0]
            count_label.configure(text=f"Path {i} ({len(new_paths[i]) - 1})")

        # Update all sh ids
        for i in range(len(self.player_paths)):
            self.update_stronghold_ids(i)

        # Finally redraw paths
        self.draw_paths_on_canvas()

    #==========================================================================================

    def copy_paths_to_clipboard(self):
        # Build the export text
        export_text = "All Portals Paths\n"

        for x in self.player_paths:
            export_text += f'\n"{x[0][0]}:{x[0][1]}"\n'
            for y in x[1:]:
                export_text += f"[{y[0]},{y[1]},{y[2]}]\n"

        # Copy to clipboard
        self.clipboard_clear()
        self.clipboard_append(export_text)

        print("Copied to clipboard!")

    #==========================================================================================

    def update_stronghold_ids(self, player_index):

        label_with_count = self.scrollable_window.winfo_children()[player_index].winfo_children()[0]

        # Get textbox for this player
        textbox = self.scrollable_window.winfo_children()[player_index].winfo_children()[1]

        # Parse Text
        text = textbox.get("1.0", "end").strip()
        text = text.replace(" ", "")
        raw_ids = [item for item in text.split(",") if item]

        # Convert to int of stronghold ids
        try:
            stronghold_ids = [int(x) for x in raw_ids]
        except ValueError:
            print("Failed to Parse Stronghold Ids!")
        
        new_path = [[player_index, f"{self.colors[player_index]}"]] 

        for i, stronghold_id in enumerate(stronghold_ids):

            # Look up SH object from stronghold_objects
            sh = next((sh for sh in self.stronghold_objects if sh.number == stronghold_id), None)

            if sh is None:
                print(f"Stronghold {stronghold_id} not found!")
                continue

            # Use real coordinates from object
            new_path.append([stronghold_id, sh.x, sh.z])

        # Save back into main structure
        self.player_paths[player_index] = new_path

        label_with_count.configure(text=f"Path {player_index+1} ({len(stronghold_ids)})")

        # Update Everything
        #self.update_textbox()
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
