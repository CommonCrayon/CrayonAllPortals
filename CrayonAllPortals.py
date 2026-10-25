import customtkinter as ctk
from  CustomTkinterMessagebox  import  *

from PIL import Image, ImageTk
import numpy as np
import sys, os, math, time, queue, json, multiprocessing

from StrongholdObject import StrongholdObject
from PathSolver import solve_in_background, plan_route, group_players, DEFAULT_PLAYER_WEIGHT, MIN_PLAYER_WEIGHT, MAX_PLAYER_WEIGHT, NETHER_SCALE

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

STRONGHOLDS_PER_RING = [3, 6, 10, 15, 21, 28, 36, 10]
STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]

MAGNITUDE_PER_RING = [2048, 5120, 8192, 11264, 14336, 17408, 20480, 23552]
BOUNDS_PER_RING = [(1280, 2816), (4352, 5888), (7424, 8960), (10496, 12032), (13568, 15104), (16640, 18176), (19712, 21248), (22784, 24320)]

WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN

# Path boxes: sized so four fit across the panel
PATH_BOX_WIDTH = 138
PATH_NAME_WIDTH = 84
PATH_WEIGHT_WIDTH = 38

# Seconds the solver may spend generating paths
DEFAULT_COMPUTATION_TIME = 60
MIN_COMPUTATION_TIME = 1
MAX_COMPUTATION_TIME = 3600

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)

img_path = resource_path("simple_rings.png")
icon_path = resource_path("icon.ico")
logo_path = resource_path("logo.png")

# Version lives only in version.txt (also used by build.bat), e.g. "1_6"
try:
    with open(resource_path("version.txt"), encoding="utf-8") as version_file:
        APP_VERSION = version_file.read().strip()
except OSError:
    APP_VERSION = "dev"

# Last session (rings, players, settings, paths) is saved here and loaded on start
SESSION_PATH = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "CrayonAllPortals", "session.json")



class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"CrayonAllPortals v{APP_VERSION.replace('_', '.')}")
        self.set_window_icon()

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

        # Path widgets ({"frame", "label", "textbox"}) and one weight per player
        self.path_widgets = []
        self.weight_vars = [ctk.StringVar(value=str(DEFAULT_PLAYER_WEIGHT))]
        self.name_vars = [ctk.StringVar(value=self.default_player_name(0))]

        # Path optimisers
        self.spawn_reset_var = ctk.BooleanVar(value=False)
        self.previous_bed_var = ctk.BooleanVar(value=False)

        # Background path generation ({"process", "queue", "start", "time"} while running)
        self.generation = None
        self.lockable_widgets = []  # disabled while paths generate
        self.preview_paths = None   # best routes so far, drawn on the map while generating
        self.progress_info = None   # latest progress snapshot from the solver
        self.ring_vars = []         # (ring, x, z) StringVars per ring
        self.loading_session = False

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

        # Title with the ender eye logo
        self.logo_image = self.load_logo(size=32)
        if self.logo_image:
            title = ctk.CTkLabel(sidebar, text="  Stronghold Ring Locations", image=self.logo_image, compound="left", font=("Arial", 20))
        else:
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

            # Enter in either box does the same as SET
            for entry in (entry_x, entry_z):
                entry.bind("<Return>", lambda event, button=ring_button: self.press_if_enabled(button))
            self.lockable_widgets.append(ring_button)
            self.ring_vars.append((stronghold_ring_string, x_coordinate_string, z_coordinate_string))


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
        # Columns: label | entry | button, centred
        player_manager_menu_frame.grid_columnconfigure(0, weight=1)
        player_manager_menu_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(player_manager_menu_frame, text="Player Manager Menu", font=("Arial", 20)).grid(row=0, column=0, columnspan=3, sticky="new", pady=(10, 5))

        ctk.CTkLabel(player_manager_menu_frame, text="Players:", font=("Arial", 18)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        # Number of players entry box
        self.num_players_var = ctk.StringVar(value="1")
        self.num_players_entry = ctk.CTkEntry(player_manager_menu_frame, textvariable=self.num_players_var, width=96, font=("Arial", 18))
        self.num_players_entry.grid(row=1, column=1, sticky="w", pady=5)

        # Number of players Button Set
        set_players_button = ctk.CTkButton(player_manager_menu_frame, text="SET", width=64, font=("Arial", 16, 'bold'), command=self.set_player_number)
        set_players_button.grid(row=1, column=2, sticky="w", pady=5, padx=5)
        self.num_players_entry.bind("<Return>", lambda event: self.press_if_enabled(set_players_button))
        self.lockable_widgets.append(set_players_button)

        # Computation time for generating paths
        ctk.CTkLabel(player_manager_menu_frame, text="Time (s):", font=("Arial", 18)).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.computation_time_var = ctk.StringVar(value=str(DEFAULT_COMPUTATION_TIME))
        self.computation_time_entry = ctk.CTkEntry(player_manager_menu_frame, textvariable=self.computation_time_var, width=96, font=("Arial", 18))
        self.computation_time_entry.grid(row=2, column=1, sticky="w", pady=5)

        # Path optimisers
        ctk.CTkCheckBox(player_manager_menu_frame, text="Respawn at spawn", font=("Arial", 16), variable=self.spawn_reset_var, onvalue=True, offvalue=False, command=self.save_session).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5, 2), padx=10)
        ctk.CTkCheckBox(player_manager_menu_frame, text="Respawn at previous bed", font=("Arial", 16), variable=self.previous_bed_var, onvalue=True, offvalue=False, command=self.save_session).grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 5), padx=10)

        # Generate a path and assign strongholds to players
        self.generate_button = ctk.CTkButton(player_manager_menu_frame, text="Generate Paths", height=34, font=("Arial", 18, "bold"), command=self.generate_path)
        self.generate_button.grid(row=5, column=0, columnspan=3, sticky="nesw", pady=5, padx=10)
        self.lockable_widgets.append(self.generate_button)

        # Copy to Clipboard
        ctk.CTkButton(player_manager_menu_frame, text="Copy for NavAssist", font=("Arial", 18), command=self.copy_paths_to_clipboard).grid(row=6, column=0, columnspan=2, sticky="nesw", pady=(5, 10), padx=(10, 5))

        # Reset everything (needs a second click to confirm)
        self.reset_button = ctk.CTkButton(player_manager_menu_frame, text="Reset", width=80, font=("Arial", 18), fg_color="#B04A4A", hover_color="#8E3B3B", command=self.reset_clicked)
        self.reset_button.grid(row=6, column=2, sticky="nesw", pady=(5, 10), padx=(5, 10))
        self.lockable_widgets.append(self.reset_button)
        self.reset_armed = None

        #======================================================================================================================
        # Scrollable Window for each player
        #======================================================================================================================
        scrollable_window_frame = ctk.CTkFrame(self)
        scrollable_window_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))

        scrollable_window_frame.grid_columnconfigure(0, weight=1)
        scrollable_window_frame.grid_rowconfigure(0, weight=1)

        self.scrollable_window = ctk.CTkScrollableFrame(scrollable_window_frame, orientation="horizontal")
        self.scrollable_window.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scrollable_window_frame.bind("<Configure>", lambda event: self.after(50, self.fit_path_boxes))

        #======================================================================================================================
        # Progress panel shown over the path boxes while paths generate (the map shows the best routes live)
        #======================================================================================================================
        self.progress_overlay = ctk.CTkFrame(scrollable_window_frame, corner_radius=8, border_width=2)
        self.progress_overlay.grid_columnconfigure(1, weight=1)

        status_frame = ctk.CTkFrame(self.progress_overlay, fg_color="transparent")
        status_frame.grid(row=0, column=0, sticky="nw", padx=(16, 8), pady=12)

        ctk.CTkLabel(status_frame, text="Generating Paths...", font=("Arial", 20)).grid(row=0, column=0, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=260, height=12, mode="determinate")
        self.progress_bar.grid(row=1, column=0, sticky="w", pady=(6, 4))

        # "42 s left · Improving routes"
        self.progress_label = ctk.CTkLabel(status_frame, text="", font=("Arial", 16))
        self.progress_label.grid(row=2, column=0, sticky="w")

        # Better routes found / total travel / improvement
        self.progress_stats = ctk.CTkLabel(status_frame, text="", font=("Arial", 14), justify="left")
        self.progress_stats.grid(row=3, column=0, sticky="w", pady=(4, 8))

        # Stop early and keep the best paths found so far
        ctk.CTkButton(status_frame, text="Stop", width=110, font=("Arial", 16), fg_color="#B04A4A", hover_color="#8E3B3B", command=self.stop_generation).grid(row=4, column=0, sticky="w")

        # Per path: strongholds and nether blocks of the best solution so far
        self.progress_table = ctk.CTkFrame(self.progress_overlay, fg_color="transparent")
        self.progress_table.grid(row=0, column=1, sticky="nw", padx=(8, 16), pady=12)
        self.progress_rows = []

        # Default Solo Path frame
        self.build_path_frames()
        self.update_path_labels()

        # Pick up where the last session left off, and save it again on close
        self.load_session()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    #==========================================================================================

    def set_window_icon(self):
        # Ender eye in the title bar / taskbar (iconbitmap also stops CustomTkinter swapping in its own icon)
        try:
            if sys.platform == "win32":
                self.iconbitmap(icon_path)
            else:
                self.icon_photo = ImageTk.PhotoImage(Image.open(logo_path))
                self.iconphoto(True, self.icon_photo)
        except Exception as error:
            print(f"Could not set window icon: {error}")

    def load_logo(self, size):
        # Pixel art: pre-scale with nearest neighbour to the on-screen size so it stays crisp instead of blurring
        try:
            try:
                scaling = ctk.ScalingTracker.get_widget_scaling(self)
            except Exception:
                scaling = 1
            pixels = max(1, round(size * scaling))
            logo = Image.open(logo_path).convert("RGBA").resize((pixels, pixels), Image.NEAREST)
            return ctk.CTkImage(light_image=logo, dark_image=logo, size=(size, size))
        except Exception as error:
            print(f"Could not load logo: {error}")
            return None

    def build_path_frames(self):
        # Rebuild one frame per path: label, player weights and stronghold ids
        for widgets in self.path_widgets:
            widgets["frame"].destroy()
        self.path_widgets = []

        for idx, players in enumerate(group_players(self.num_of_players)):
            frame = ctk.CTkFrame(self.scrollable_window)
            frame.grid(row=0, column=idx, pady=5, padx=5, sticky="nsw")

            # Path label + copy button for just this path
            header_frame = ctk.CTkFrame(frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, padx=5, pady=(5, 2), sticky="ew")
            header_frame.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(header_frame, text=f"Path {idx+1} (0)", font=("Arial", 16, "bold"), text_color=self.colors[idx])
            label.grid(row=0, column=0, sticky="w")

            ctk.CTkButton(header_frame, text="Copy", width=48, height=24, font=("Arial", 13), command=lambda idx=idx: self.copy_path_to_clipboard(idx)).grid(row=0, column=1, sticky="e", padx=(6, 0))

            # Player names and weights: "name  x weight"
            players_frame = ctk.CTkFrame(frame, fg_color="transparent")
            players_frame.grid(row=1, column=0, padx=5, pady=(0, 2), sticky="w")

            for row, player in enumerate(players):
                name_entry = ctk.CTkEntry(players_frame, textvariable=self.name_vars[player], width=PATH_NAME_WIDTH, height=26, font=("Arial", 14))
                name_entry.grid(row=row, column=0, pady=2)
                name_entry.bind("<FocusOut>", lambda event: self.save_session())
                ctk.CTkLabel(players_frame, text="×", width=14, font=("Arial", 14)).grid(row=row, column=1, padx=2)
                ctk.CTkEntry(players_frame, textvariable=self.weight_vars[player], width=PATH_WEIGHT_WIDTH, height=26, font=("Arial", 14)).grid(row=row, column=2, pady=2)

            # Textbox for Stronghold Ids (its height is fitted to the panel by fit_path_boxes)
            textbox = ctk.CTkTextbox(frame, width=PATH_BOX_WIDTH, height=80, font=("Arial", 16))
            textbox.grid(row=2, column=0, padx=5, pady=5, sticky="nesw")
            textbox.bind("<KeyRelease>", lambda event, idx=idx: self.update_stronghold_ids(idx))

            self.path_widgets.append({"frame": frame, "label": label, "textbox": textbox})

        self.after(50, self.fit_path_boxes)

    def fit_path_boxes(self):
        # Let each stronghold list fill the height left in the panel instead of being cut off at the bottom
        canvas = getattr(self.scrollable_window, "_parent_canvas", None)
        if canvas is None or not self.path_widgets:
            return

        self.update_idletasks()
        visible = canvas.winfo_height()
        if visible <= 1:
            return

        try:
            scaling = ctk.ScalingTracker.get_widget_scaling(self)
        except Exception:
            scaling = 1

        for widgets in self.path_widgets:
            top = widgets["frame"].winfo_y() + widgets["textbox"].winfo_y()
            height = (visible - top) / scaling - 12  # textbox + frame padding below
            widgets["textbox"].configure(height=max(60, int(height)))

    def read_player_weights(self):
        # Returns a weight per player, or None (after telling the user) if any are invalid
        weights = []

        for player, var in enumerate(self.weight_vars):
            try:
                weight = float(var.get().strip())
                if not (MIN_PLAYER_WEIGHT <= weight <= MAX_PLAYER_WEIGHT):
                    raise ValueError
            except ValueError:
                CTkMessagebox.messagebox(title="Invalid weight", text=f"P{player+1}'s weight must be a number\nfrom {MIN_PLAYER_WEIGHT} to {MAX_PLAYER_WEIGHT}.", sound='off')
                return None

            weights.append(weight)

        return weights

    #==========================================================================================

    def press_if_enabled(self, button):
        # Enter key: act like clicking the button, unless it's locked while paths generate
        if button.cget("state") != "disabled":
            button.invoke()

    def reset_clicked(self):
        # First click arms the button for 3 seconds, second click resets
        if self.reset_armed is None:
            self.reset_button.configure(text="Sure?")
            self.reset_armed = self.after(3000, self.disarm_reset)
            return

        self.disarm_reset()
        self.reset_all()

    def disarm_reset(self):
        if self.reset_armed is not None:
            self.after_cancel(self.reset_armed)
            self.reset_armed = None
        self.reset_button.configure(text="Reset")

    def reset_all(self):
        # Back to a fresh start: no rings, 1 player, default settings, no paths
        for sh in self.stronghold_objects:
            sh.destroy()
        self.stronghold_objects = []

        for _, x_var, z_var in self.ring_vars:
            x_var.set("")
            z_var.set("")

        self.computation_time_var.set(str(DEFAULT_COMPUTATION_TIME))
        self.spawn_reset_var.set(False)
        self.previous_bed_var.set(False)

        self.player_paths = [[[0, f"{self.colors[0]}"]]]
        del self.weight_vars[1:]
        self.weight_vars[0].set(str(DEFAULT_PLAYER_WEIGHT))
        del self.name_vars[1:]
        self.name_vars[0].set(self.default_player_name(0))
        self.num_players_var.set("1")
        self.set_player_number()  # rebuilds the path boxes, redraws and saves the session

    @staticmethod
    def default_player_name(player):
        return f"Player {player+1}"

    def player_name(self, player):
        # Brackets and quotes would confuse NavAssist's parser, so they're dropped
        name = "".join(ch for ch in self.name_vars[player].get() if ch not in '[]"').strip()
        return name or self.default_player_name(player)

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

        # Keep existing names and weights, new players start at the defaults
        del self.weight_vars[num_players:]
        del self.name_vars[num_players:]
        while len(self.weight_vars) < num_players:
            self.weight_vars.append(ctk.StringVar(value=str(DEFAULT_PLAYER_WEIGHT)))
        while len(self.name_vars) < num_players:
            self.name_vars.append(ctk.StringVar(value=self.default_player_name(len(self.name_vars))))

        # Pop extra paths / add empty new ones
        del self.player_paths[self.num_of_paths:]
        for i in range(len(self.player_paths), self.num_of_paths):
            self.player_paths.append([[i, f"{self.colors[i]}"]])

        # Pairings change with the player count, so rebuild the path frames
        self.build_path_frames()

        # Update Everything
        self.update_textbox()
        self.update_path_labels()
        self.draw_paths_on_canvas()
        self.save_session()



    # Updates the Stronghold Ids of each player
    def update_textbox(self):
        for idx, player_path in enumerate(self.player_paths):

            # Get the textbox for this path
            textbox = self.path_widgets[idx]["textbox"]

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

        # While generating, show the solver's best routes so far
        paths = self.preview_paths if self.preview_paths is not None else self.player_paths

        # Stronghold dots take the colour of the path they're on
        self.stronghold_colors = {}

        for idx, player_path in enumerate(paths):

            stops = player_path[1:]
            if not stops:
                continue

            color = self.colors[idx % len(self.colors)]
            prev_x, prev_y = origin_x, origin_y

            for i, point in enumerate(stops):
                x, y = point[1], point[2]
                self.stronghold_colors[point[0]] = color

                img_x = int((x - WORLD_MIN) / WORLD_RANGE * side) + offset_x
                img_y = int((y - WORLD_MIN) / WORLD_RANGE * side) + offset_y

                if i == 0:
                    # Arrow from spawn to the first stronghold shows which end the path starts at
                    end_x, end_y = img_x, img_y
                    length = math.hypot(img_x - prev_x, img_y - prev_y)
                    gap = self.dot_radius() + 2
                    if length > gap:
                        end_x = img_x - (img_x - prev_x) * gap / length
                        end_y = img_y - (img_y - prev_y) * gap / length
                    line = self.canvas.create_line(prev_x, prev_y, end_x, end_y, fill=color, width=4, arrow="last", arrowshape=(14, 18, 7))
                else:
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

    def dot_radius(self):
        # Stronghold dots scale with the map so outer rings don't overlap
        return max(10, round(self.image_size * 0.021))

    def is_solo_path(self, idx):
        # With an odd player count the last path belongs to the unpaired player
        return self.num_of_players % 2 == 1 and idx == self.num_of_paths - 1

    def update_path_labels(self):
        for idx, path in enumerate(self.player_paths):
            label = self.path_widgets[idx]["label"]
            # With an odd player count the last path belongs to the unpaired player
            name = "Solo" if self.is_solo_path(idx) else f"Path {idx+1}"
            text = f"{name} ({len(path) - 1})"

            label.configure(text=text)

    def read_computation_time(self):
        # Returns whole seconds, or None (after telling the user) if invalid
        try:
            seconds = int(self.computation_time_entry.get().strip())
            if not (MIN_COMPUTATION_TIME <= seconds <= MAX_COMPUTATION_TIME):
                raise ValueError
        except ValueError:
            CTkMessagebox.messagebox(title="Invalid time", text=f"Time must be a whole number of seconds\nfrom {MIN_COMPUTATION_TIME} to {MAX_COMPUTATION_TIME}.", sound='off')
            return None

        return seconds

    def generate_path(self):
        if self.generation is not None:
            return

        player_weights = self.read_player_weights()
        if player_weights is None:
            return

        computation_time = self.read_computation_time()
        if computation_time is None:
            return

        valid_strongholds = []

        # Skip any strongholds that were first in the ring.
        for sh in self.stronghold_objects:
            if sh.number not in STRONGHOLDS_RING_START:
                valid_strongholds.append([sh.number, sh.x, sh.z])

        solver_args = {
            "strongholds": valid_strongholds,
            "player_weights": player_weights,
            "computation_time": computation_time,
            "spawn_reset": self.spawn_reset_var.get(),
            "previous_bed": self.previous_bed_var.get(),
        }

        # Compute optimal paths (one per spawn -> spawn loop) in a separate process so the window stays responsive
        context = multiprocessing.get_context("spawn")
        result_queue = context.Queue()
        process = context.Process(target=solve_in_background, args=(result_queue, solver_args), daemon=True)
        process.start()

        self.generation = {"process": process, "queue": result_queue, "start": time.monotonic(), "time": computation_time}
        self.show_generating(True)
        self.after(100, self.poll_generation)

    def poll_generation(self):
        job = self.generation
        if job is None:  # cancelled
            return

        # Read everything the solver has sent: progress snapshots, then "done" or "error"
        finished = self.read_solver_messages(job, wait=False)

        if finished is None and not job["process"].is_alive():
            # Process ended; collect anything still in flight
            finished = self.read_solver_messages(job, wait=True) or ("error", "The path solver stopped unexpectedly.")

        if finished is None:
            # Still working: update the progress display and check again shortly
            self.update_progress_display()
            self.after(100, self.poll_generation)
            return

        status, result = finished
        self.generation = None
        self.show_generating(False)

        if status == "error":
            CTkMessagebox.messagebox(title="Path generation failed", text=str(result), sound='off')
            return

        self.apply_routes(result)

    def read_solver_messages(self, job, wait):
        # Applies progress messages; returns ("done", routes) / ("error", message) once one arrives, else None
        while True:
            try:
                kind, payload = job["queue"].get(timeout=1) if wait else job["queue"].get_nowait()
            except queue.Empty:
                return None

            if kind != "progress":
                return kind, payload

            self.progress_info = payload
            if payload["routes"] is not None:
                self.preview_paths = [[[i, f"{self.colors[i]}"]] + route for i, route in enumerate(payload["routes"])]
                self.draw_paths_on_canvas()

    def update_progress_display(self):
        job = self.generation
        info = self.progress_info

        elapsed = time.monotonic() - job["start"]
        remaining = job["time"] - elapsed
        stage = info["stage"] if info else "Starting solver"

        self.progress_bar.set(min(elapsed / job["time"], 1))
        time_text = f"{math.ceil(remaining)} s left" if remaining > 0 else "Finishing up"
        self.progress_label.configure(text=f"{time_text} · {stage}...")

        if not info or info["total"] is None:
            self.progress_stats.configure(text="Waiting for the first solution...")
            return

        since = max(0, round(time.time() - info["last_improvement"]))
        lines = [
            f"Better routes found: {info['improvements']} (last {since} s ago)",
            f"Total travel: {info['total']:,.0f} nether blocks",
        ]
        if info["first_total"] and info["total"] < info["first_total"]:
            lines.append(f"{(1 - info['total'] / info['first_total']) * 100:.1f}% shorter than the first solution")
        else:
            lines.append("First solution found")
        self.progress_stats.configure(text="\n".join(lines))

        for (count_label, distance_label), path in zip(self.progress_rows, info["paths"]):
            count_label.configure(text=str(path["count"]))
            distance_label.configure(text=f"{path['distance']:,.0f}")

    def build_progress_table(self):
        # Header + one row per path: name (in its map colour), strongholds, nether blocks
        for widget in self.progress_table.winfo_children():
            widget.destroy()
        self.progress_rows = []

        for col, heading in enumerate(["Path", "Strongholds", "Nether Blocks"]):
            ctk.CTkLabel(self.progress_table, text=heading, font=("Arial", 14, "bold")).grid(row=0, column=col, sticky="w", padx=8)

        for idx, players in enumerate(group_players(self.num_of_players)):
            name = "Solo Path" if len(players) == 1 else f"Path {idx+1}"
            ctk.CTkLabel(self.progress_table, text=name, font=("Arial", 14), text_color=self.colors[idx]).grid(row=idx+1, column=0, sticky="w", padx=8)

            count_label = ctk.CTkLabel(self.progress_table, text="-", font=("Arial", 14))
            count_label.grid(row=idx+1, column=1, sticky="e", padx=8)
            distance_label = ctk.CTkLabel(self.progress_table, text="-", font=("Arial", 14))
            distance_label.grid(row=idx+1, column=2, sticky="e", padx=8)

            self.progress_rows.append((count_label, distance_label))

    def stop_generation(self):
        # Stop the solver now and use the best paths it has found so far
        # (if it hasn't found any yet, the previous paths stay)
        job = self.generation
        if job is None:
            return

        # Pick up any progress that arrived since the last poll
        finished = self.read_solver_messages(job, wait=False)

        self.generation = None
        job["process"].terminate()

        if finished and finished[0] == "done":
            best_routes = finished[1]
        elif self.progress_info and self.progress_info["routes"] is not None:
            best_routes = self.progress_info["routes"]
        else:
            best_routes = None

        self.show_generating(False)

        if best_routes is not None:
            self.apply_routes(best_routes)

    def show_generating(self, generating):
        # Lock controls that would change the inputs and show/hide the progress overlay
        for widget in self.lockable_widgets:
            widget.configure(state="disabled" if generating else "normal")

        self.generate_button.configure(text="Generating..." if generating else "Generate Paths")

        if generating:
            # Start from a clean map; the best routes are drawn as the solver finds them
            self.progress_info = None
            self.preview_paths = [[[i, f"{self.colors[i]}"]] for i in range(self.num_of_paths)]
            self.build_progress_table()
            self.update_progress_display()
            self.progress_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.progress_overlay.lift()
        else:
            self.progress_overlay.place_forget()
            self.preview_paths = None
            self.progress_info = None

        self.draw_paths_on_canvas()

    def apply_routes(self, routes):
        # Reconstruct paths
        new_paths = []
        for i in range(self.num_of_paths):
            header = [i, f"{self.colors[i]}"]
            new_paths.append([header] + routes[i])

        self.player_paths = new_paths

        self.update_textbox()
        self.update_path_labels()
        self.draw_paths_on_canvas()
        self.save_session()

    #==========================================================================================
    # Session: saved after every change and on close, loaded on start
    #==========================================================================================

    def save_session(self):
        if self.loading_session:
            return

        # Rings are stored by the coordinates they were SET with (the first stronghold of each ring)
        rings = {}
        for sh in self.stronghold_objects:
            if sh.ring_index == 0:
                rings[str(sh.ring)] = [sh.x, sh.z]

        session = {
            "version": APP_VERSION,
            "rings": rings,
            "players": self.num_of_players,
            "weights": [var.get() for var in self.weight_vars],
            "names": [var.get() for var in self.name_vars],
            "time": self.computation_time_var.get(),
            "spawn_reset": bool(self.spawn_reset_var.get()),
            "previous_bed": bool(self.previous_bed_var.get()),
            "paths": [[stop[0] for stop in path[1:]] for path in self.player_paths],
        }

        try:
            os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
            temp_path = SESSION_PATH + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(session, file, indent=2)
            os.replace(temp_path, SESSION_PATH)  # never leaves a half-written session
        except OSError as error:
            print(f"Could not save session: {error}")

    def load_session(self):
        try:
            with open(SESSION_PATH, encoding="utf-8") as file:
                session = json.load(file)
        except FileNotFoundError:
            return
        except (OSError, ValueError) as error:
            print(f"Could not load session: {error}")
            return

        self.loading_session = True
        try:
            # Rings (re-predicts every stronghold)
            for ring, (x, z) in session.get("rings", {}).items():
                ring_var, x_var, z_var = self.ring_vars[int(ring)]
                x_var.set(str(x))
                z_var.set(str(z))
                self.update_ring(ring_var, x_var, z_var)

            # Players and their weights
            self.num_players_var.set(str(session.get("players", 1)))
            self.set_player_number()
            for var, weight in zip(self.weight_vars, session.get("weights", [])):
                var.set(str(weight))
            for var, name in zip(self.name_vars, session.get("names", [])):
                var.set(str(name))

            # Settings
            self.computation_time_var.set(str(session.get("time", DEFAULT_COMPUTATION_TIME)))
            self.spawn_reset_var.set(bool(session.get("spawn_reset", False)))
            self.previous_bed_var.set(bool(session.get("previous_bed", False)))

            # Paths, rebuilt from the current strongholds
            by_number = {sh.number: sh for sh in self.stronghold_objects}
            for idx, ids in enumerate(session.get("paths", [])[:self.num_of_paths]):
                stops = [[number, by_number[number].x, by_number[number].z] for number in ids if number in by_number]
                self.player_paths[idx] = [[idx, f"{self.colors[idx]}"]] + stops

            self.update_textbox()
            self.update_path_labels()
            self.draw_paths_on_canvas()
        except Exception as error:
            print(f"Could not restore session: {error}")
        finally:
            self.loading_session = False

    def on_close(self):
        # Weights and time aren't saved as they're typed, so save once more on the way out
        self.save_session()
        if self.generation is not None:
            self.generation["process"].terminate()
        self.destroy()

    #==========================================================================================

    def path_export_text(self, path_idx):
        # One path for NavAssist: a header naming its players, then [id,x,z]"note" per stronghold
        spawn_reset = self.spawn_reset_var.get()
        previous_bed = self.previous_bed_var.get()

        path = self.player_paths[path_idx]
        path_notes = {}

        stops = path[1:]
        is_shared = not self.is_solo_path(path_idx)

        # Pick where to respawn before each leg using the enabled optimisers
        _, legs = plan_route(stops, closed=is_shared, spawn_reset=spawn_reset, previous_bed=previous_bed)

        for i, leg in enumerate(legs):
            # The return to spawn on a shared path isn't a leg anyone follows a note for
            if leg is None or i == len(stops) - 1:
                continue

            saving = round(leg["saving"] / NETHER_SCALE)

            if leg["option"] == "spawn":
                path_notes[i] = f"DO NOT PLACE BED! {saving} nether blocks faster via SPAWN."
            elif leg["option"] == "keep":
                if saving > 0:
                    path_notes[i] = f"KEEP CURRENT BED! {saving} nether blocks faster via CURRENT bed."
                else:
                    # Costs a little on this leg but pays off on a later one
                    path_notes[i] = "KEEP CURRENT BED! Faster overall via CURRENT bed."

        players = " & ".join(self.player_name(p) for p in group_players(self.num_of_players)[path_idx])
        text = f'Path {path_idx + 1} - {players}\n'

        for i, y in enumerate(stops):
            text += f"[{y[0]},{y[1]},{y[2]}]"

            if i in path_notes:
                text += f'"{path_notes[i]}"'

            text += "\n"

        return text

    def copy_path_to_clipboard(self, path_idx):
        # Just one path, ready to paste into that player's NavAssist
        self.clipboard_clear()
        self.clipboard_append(self.path_export_text(path_idx))
        print(f"Copied path {path_idx + 1} to clipboard!")

    def copy_paths_to_clipboard(self):
        export_text = "All Portals Paths\n"
        for path_idx in range(len(self.player_paths)):
            export_text += "\n" + self.path_export_text(path_idx)

        self.clipboard_clear()
        self.clipboard_append(export_text)

        print("Copied to clipboard!")

    #==========================================================================================

    def update_stronghold_ids(self, player_index):  # player_index is now a path index

        textbox = self.path_widgets[player_index]["textbox"]

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
        self.save_session()

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

        self.save_session()

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
    # Needed for the path solver process in the PyInstaller exe
    multiprocessing.freeze_support()

    # Give the app its own taskbar entry so Windows shows the ender eye instead of Python's icon
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CommonCrayon.CrayonAllPortals")
        except Exception:
            pass

    app = App()
    app.mainloop()
