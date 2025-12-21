import customtkinter as ctk
from  CustomTkinterMessagebox  import  *
from PathSolver import make_stronghold_list
import math

WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN

class PlayerManager(ctk.CTkToplevel):
    def __init__(self, parent, stronghold_objects, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # OVERRIDE the X button
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        self.parent = parent
        self.num_of_players = 1
        self.stronghold_objects = stronghold_objects
        self.player_paths = [[[0, ""]]]

        self.attributes("-topmost", True)
        self.title("Player Manager")

        self.geometry("930x655")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.grid_rowconfigure(1, weight=1)

        self.colors = ["cyan", "magenta", "yellow", "orange", "purple", "red", "blue", "green", "brown", "pink", "lime", "navy", "teal", "gold"]

        #======================================================================================================================
        # Settings Frame
        #======================================================================================================================
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)


        ctk.CTkLabel(settings_frame, text="Settings", font=("Arial", 22)).grid(row=0, column=0, columnspan=2, sticky="nesw", padx=10, pady=10)


        ctk.CTkLabel(settings_frame, text="Number of Players:", font=("Arial", 18)).grid(row=1, column=0, sticky="e", padx=(10, 5), pady=5)

        # Number of players entry box
        self.num_players_entry = ctk.CTkEntry(settings_frame, textvariable=ctk.StringVar(value="1"), font=("Arial", 18))
        self.num_players_entry.grid(row=1, column=1, sticky="w", padx=(5, 10), pady=5)

        # Number of players Button Set
        ctk.CTkButton(settings_frame, text="SET", font=("Arial", 18), width=300, command=self.set_player_number).grid(row=2, column=0, columnspan=2, sticky="ns", padx=(5, 10), pady=5)


        # Draw on Canvas Bool
        self.canvas_draw_bool = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Draw on Canvas", font=("Arial", 18), variable=self.canvas_draw_bool, command=self.draw_paths_on_canvas
            ).grid(row=3, column=0, columnspan=2, padx=10, pady=(20, 10))

        #======================================================================================================================
        # Player Stronghold Assigner
        #======================================================================================================================
        path_gen_frame = ctk.CTkFrame(self)
        path_gen_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        path_gen_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(path_gen_frame, text="Path Generator", font=("Arial", 22)).grid(row=0, column=0, sticky="nesw", padx=10, pady=10)

        # Set first to Active in Path Bool
        self.first_active_bool = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(path_gen_frame, text="Make First Stronghold Active on Path", font=("Arial", 18), variable=self.first_active_bool
            ).grid(row=1, column=0, padx=10, pady=10)
        
        # Auto Set Active in Path Bool
        self.auto_active_bool = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(path_gen_frame, text="Auto Set Stronghold Active on Path", font=("Arial", 18), variable=self.auto_active_bool
            ).grid(row=2, column=0, padx=10, pady=10)

        # Generate a path and assign strongholds to players
        ctk.CTkButton(path_gen_frame, text="Generate", font=("Arial", 18), width=300, command=self.generate_path).grid(row=3, column=0, sticky="ns", padx=10, pady=(10, 6))

        # Copy to Clipboard
        ctk.CTkButton(path_gen_frame, text="Copy to Clipboard", font=("Arial", 18), width=300, command=self.copy_paths_to_clipboard).grid(row=4, column=0, sticky="ns", padx=10, pady=(6, 10))


        #======================================================================================================================
        # Scrollable Window for each player
        #======================================================================================================================
        scrollable_window_frame = ctk.CTkFrame(self)
        scrollable_window_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

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
        ctk.CTkButton(frame, text="Complete All", font=("Arial", 18), command=lambda i=0: self.complete_all_strongholds(0)
            ).grid(row=4, column=0, padx=5, pady=(0, 5), sticky="nesw")



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
            self.player_paths.append([[0, ""]])

            frame = ctk.CTkFrame(self.scrollable_window)
            frame.grid(row=0, column=i, pady=5, padx=5, sticky="nsw")

            # Player Id
            ctk.CTkLabel(frame, text=f"Player {i+1}", font=("Arial", 18), text_color=self.colors[i]).grid(row=0, column=0, padx=5, pady=5, sticky="w")

            # Player Name
            player_name_entry = ctk.CTkEntry(frame, placeholder_text="Name", font=("Arial", 18))
            player_name_entry.grid(row=1, column=0, padx=5, pady=(0,5), sticky="nesw")
            player_name_entry.bind("<KeyRelease>", lambda event, idx=i: self.update_stronghold_ids(idx))

            # Path by stronghold id
            ctk.CTkLabel(frame, text="Stronghold Ids:", font=("Arial", 18), anchor="w").grid(row=2, column=0, padx=5, pady=(15, 5), sticky="nesw")

            # Textbox for Stronghold Ids
            textbox = ctk.CTkTextbox(frame, font=("Arial", 18))
            textbox.grid(row=3, column=0, padx=5, pady=5, sticky="nesw")
            textbox.bind("<KeyRelease>", lambda event, idx=i: self.update_stronghold_ids(idx))

            # Complete All Button 
            ctk.CTkButton(frame, text="Complete All", font=("Arial", 18), command=lambda idx=i: self.complete_all_strongholds(idx)
                ).grid(row=4, column=0, padx=5, pady=(0, 5), sticky="nesw")


        # Update Everything
        self.update_textbox()
        self.draw_paths_on_canvas()



    # Updates the Stronghold Ids of each player
    def update_textbox(self):
        for idx, player_path in enumerate(self.player_paths):

            # Get the textbox for this player
            textbox = self.scrollable_window.winfo_children()[idx].winfo_children()[3]

            # create stronghold IDs list
            stronghold_ids = [str(sh_id) for sh_id, _, _ in player_path[1:]]
            textbox_text = ",".join(stronghold_ids)

            # Update the textbox
            textbox.delete("1.0", "end")
            textbox.insert("end", textbox_text)



    def update_stronghold_ids(self, player_index):

        name_entry = self.scrollable_window.winfo_children()[player_index].winfo_children()[1]

        label_with_count = self.scrollable_window.winfo_children()[player_index].winfo_children()[2]

        # Get textbox for this player
        textbox = self.scrollable_window.winfo_children()[player_index].winfo_children()[3]

        # Parse Text
        text = textbox.get("1.0", "end").strip()
        text = text.replace(" ", "")
        raw_ids = [item for item in text.split(",") if item]

        # Convert to int of stronghold ids
        try:
            stronghold_ids = [int(x) for x in raw_ids]
        except ValueError:
            print("Failed to Parse Stronghold Ids!")
        


        new_path = [[player_index, str(name_entry.get())]] 

        for i, stronghold_id in enumerate(stronghold_ids):

            # Look up SH object from stronghold_objects
            sh = next((sh for sh in self.stronghold_objects if sh.number == stronghold_id), None)

            if sh is None:
                print(f"Stronghold {stronghold_id} not found!")
                continue

            # Use real coordinates from object
            new_path.append([stronghold_id, sh.x, sh.z])

            sh.update_name(str(name_entry.get()))

            # If the first one in the path, set active
            if self.first_active_bool.get() and i == 0:
                sh.set_status("ACT")

            # Point to next stronghold so next stronghold in path to active
            if self.auto_active_bool.get():
                sh.next_sh = stronghold_ids[i + 1] if i < len(stronghold_ids) - 1 else None


        # Save back into main structure
        self.player_paths[player_index] = new_path

        label_with_count.configure(text=f"Stronghold Ids ({len(stronghold_ids)})")

        # Update Everything
        #self.update_textbox()
        self.draw_paths_on_canvas()



    def complete_all_strongholds(self, player_index):
        for stronghold_id, _, _ in self.player_paths[player_index][1:]:
            sh = next((sh for sh in self.stronghold_objects if sh.number == stronghold_id), None)

            sh.set_status("COM")

        

    def draw_paths_on_canvas(self):
    
        # Delete previous canvas items if any
        if hasattr(self, "canvas_items"):
            for item in self.canvas_items:
                try:
                    self.parent.canvas.delete(item)
                except Exception:
                    pass
        self.canvas_items = []

        # If not set to draw, then don't draw
        if (self.canvas_draw_bool.get() == False):
            return

        # Use the square image size
        side = self.parent.image_size

        # Offsets for centering
        offset_x = (self.parent.canvas.winfo_width() - side) // 2
        offset_y = (self.parent.canvas.winfo_height() - side) // 2

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
                    line = self.parent.canvas.create_line(prev_x, prev_y, img_x, img_y, fill=color, width=4)
                    self.canvas_items.append(line)

                prev_x, prev_y = img_x, img_y


        # Redraw canvas markers
        for sh in self.parent.stronghold_objects:
            sh.draw_on_canvas()
    


    def generate_path(self):

        # Clear existing paths
        new_paths = []
        for i in range(self.num_of_players):
            name_entry = self.scrollable_window.winfo_children()[i].winfo_children()[1]
            player_name = str(name_entry.get())
            new_paths.append([[i, player_name]])


        # ANGLE SPLITTING
        angle_per_player = 360 / self.num_of_players

        for sh in self.parent.stronghold_objects:

            # Skip if already complete
            if sh.widget_status == "COM":
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
            count_label = self.scrollable_window.winfo_children()[i].winfo_children()[2]
            count_label.configure(text=f"Stronghold Ids ({len(new_paths[i]) - 1})")

        # Update all sh ids
        for i in range(len(self.player_paths)):
            self.update_stronghold_ids(i)

        # Finally redraw paths
        self.draw_paths_on_canvas()



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

