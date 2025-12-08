import customtkinter as ctk

STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]

WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN

class PlayerManager(ctk.CTkToplevel):
    def __init__(self, parent, stronghold_objects, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.parent = parent
        self.stronghold_objects = stronghold_objects
        self.player_paths = None

        self.attributes("-topmost", True)
        self.title("Player Manager")

        self.geometry("1080x540")

        self.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(2, weight=1)

        #======================================================================================================================
        # Settings Frame
        #======================================================================================================================
        player_num_frame = ctk.CTkFrame(self)
        player_num_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Number of players label
        num_players_label = ctk.CTkLabel(player_num_frame, text="Number of Players:", font=("Arial", 18))
        num_players_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)

        # Number of players entry box
        self.num_players_entry = ctk.CTkEntry(player_num_frame, width=120, placeholder_text="Enter amount", font=("Arial", 18))
        self.num_players_entry.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=5)


        # Number of players Button Set
        ctk.CTkButton(player_num_frame, width=64, text="SET", font=("Arial", 18), command=self.set_player_number).grid(row=0, column=2, sticky="w", padx=5, pady=5)


        # Depth Label
        depth_label = ctk.CTkLabel(player_num_frame, text="Depth of Path:", font=("Arial", 18))
        depth_label.grid(row=0, column=3, sticky="w", padx=(10, 5), pady=5)

        # Depth Entry
        self.depth_entry = ctk.CTkEntry(player_num_frame, width=120, placeholder_text="Enter Depth", font=("Arial", 18))
        self.depth_entry.grid(row=0, column=4, sticky="w", padx=(5, 10), pady=5)

        #======================================================================================================================
        # Player Stronghold Assigner
        #======================================================================================================================
        button_actions_frame = ctk.CTkFrame(self)
        button_actions_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Generate a path and assign strongholds to players
        self.assign_stronghold_button = ctk.CTkButton(button_actions_frame, text="Generate Stronghold Assignments", font=("Arial", 18), command=self.assign_strongholds)
        self.assign_stronghold_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Number of players Button Set
        self.assign_stronghold_button = ctk.CTkButton(button_actions_frame, text="Draw on Canvas", font=("Arial", 18), command=self.draw_on_canvas)
        self.assign_stronghold_button.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        #======================================================================================================================
        # Scrollable Window for each player
        #======================================================================================================================
        scrollable_window_frame = ctk.CTkFrame(self)
        scrollable_window_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        scrollable_window_frame.grid_columnconfigure(0, weight=1)
        scrollable_window_frame.grid_rowconfigure(0, weight=1)

        self.scrollable_window = ctk.CTkScrollableFrame(scrollable_window_frame, orientation="horizontal")
        self.scrollable_window.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)


        ctk.CTkLabel(self.scrollable_window, text="Set Player Number First", font=("Arial", 22), anchor="center").grid(row=0, column=0, sticky="nesw")



    def set_player_number(self):

        # Get Number of players
        try:
            num_players = int(self.num_players_entry.get())
            if num_players <= 0:
                raise ValueError
        except:
            print("Invalid number of players.")
            return
        
        
        # Clear old widgets
        for widget in self.scrollable_window.winfo_children():
            widget.destroy()


        self.player_name_entries = []

        # Generate frames
        for i in range(num_players):

            frame = ctk.CTkFrame(self.scrollable_window)
            frame.grid(row=0, column=i, pady=5, padx=5, sticky="nsw")

            # Player Number
            label = ctk.CTkLabel(frame, text=f"Player {i+1}", font=("Arial", 18))
            label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

            # Player Name
            entry = ctk.CTkEntry(frame, placeholder_text="Name", font=("Arial", 18))
            entry.grid(row=1, column=0, padx=5, pady=(0,5), sticky="w")

            self.player_name_entries.append(entry)



    def distance(self, p, sh):
        px, pz = p
        return ((sh.x - px)**2 + (sh.z - pz)**2) ** 0.5



    def assign_strongholds(self):
        # Get Number of players
        try:
            num_players = int(self.num_players_entry.get())
            if num_players <= 0:
                raise ValueError
        except:
            print("Invalid number of players.")
            return


        # Get Depth to make path
        try:
            depth = int(self.depth_entry.get())
            if depth <= 0:
                raise ValueError
        except:
            print("Invalid number of players.")
            return
        

        # Get strongholds left todo
        strongholds_todo = [sh for sh in self.stronghold_objects if sh.status_var.get() in ("Active", "Remaining")]

        # Intialise Player path
        self.player_paths = [[["START", 0, 0]] for i in range(num_players)]
        players_last_position = [[0, 0] for i in range(num_players)]

        # Iterate over strongholds whilst popping the ones assigned
        while len(strongholds_todo) > 0:
            # Only go to depth set
            if (depth <= 0):
                break

            for idx, player in enumerate(self.player_paths):

                if len(strongholds_todo) == 0:
                    break

                current_player_location = players_last_position[idx]

                shortest_distance = float("inf")
                best_sh_i = 0

                # Get closest stronghold to this player's location
                for index, sh in enumerate(strongholds_todo):

                    distance = self.distance(current_player_location, sh)

                    if distance < shortest_distance:
                        shortest_distance = distance
                        best_sh_i = index

                chosen_sh = strongholds_todo[best_sh_i]

                # Append to Player Path
                self.player_paths[idx].append([STRONGHOLDS_RING_START[chosen_sh.ring] + chosen_sh.index, chosen_sh.x, chosen_sh.z])

                # Update Last Player Position
                players_last_position[idx] = [chosen_sh.x, chosen_sh.z]

                # remove stronghold from future paths
                strongholds_todo.pop(best_sh_i)

            depth = depth - 1

        
        # Append path info to the existing player frames
        for idx, player_path in enumerate(self.player_paths):
            frame = self.scrollable_window.winfo_children()[idx]  # Get the frame for this player

            # Add Labels
            label_frame = ctk.CTkFrame(frame)
            label_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
            ctk.CTkLabel(label_frame, width=80, text="SH", font=("Arial", 18)).grid(row=2, column=0, sticky="ew")
            ctk.CTkLabel(label_frame, width=80, text="X", font=("Arial", 18)).grid(row=2, column=1, sticky="ew")
            ctk.CTkLabel(label_frame, width=80, text="Z", font=("Arial", 18)).grid(row=2, column=2, sticky="ew")

            # Start adding after labels
            row = 3
            for sh_number, x, z in player_path:  # skip the START entry
                # Create a frame for each stronghold entry
                sh_frame = ctk.CTkFrame(frame)
                sh_frame.grid(row=row, column=0, sticky="w", padx=5, pady=2)

                # Stronghold number
                sh_number_var = ctk.StringVar(value=str(sh_number))
                ctk.CTkEntry(sh_frame, width=80, font=("Arial", 14), textvariable=sh_number_var).grid(row=0, column=0, padx=2)

                # X coordinate
                x_var = ctk.StringVar(value=str(x))
                ctk.CTkEntry(sh_frame, width=80, font=("Arial", 14), textvariable=x_var, state="disabled").grid(row=0, column=1, padx=2)

                # Z coordinate
                z_var = ctk.StringVar(value=str(z))
                ctk.CTkEntry(sh_frame, width=80, font=("Arial", 14), textvariable=z_var, state="disabled").grid(row=0, column=2, padx=2)

                row += 1

            # Add Update Button
            button_frame = ctk.CTkFrame(frame)
            button_frame.grid(row=row, column=0, sticky="esw", padx=5, pady=5)

            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_rowconfigure(0, weight=1)
            ctk.CTkButton(button_frame, text="Update").grid(row=0, column=0, sticky="nesw")


    def draw_on_canvas(self):
        
        # Use the square image size
        side = self.parent.image_size

        # Offsets for centering
        offset_x = (self.parent.canvas.winfo_width() - side) // 2
        offset_y = (self.parent.canvas.winfo_height() - side) // 2

        # Delete previous canvas items if any
        if hasattr(self, "canvas_items"):
            for item in self.canvas_items:
                try:
                    self.parent.canvas.delete(item)
                except Exception:
                    pass
        self.canvas_items = []

        colors = ["cyan", "magenta", "yellow", "orange", "purple"]

        # Iterate through each player's path
        for i, path in enumerate(self.player_paths):

            color = colors[i % len(colors)]
            prev_x, prev_y = None, None
            
            for point in path:
                x, y = point[1], point[2]

                # Map world coordinates to canvas coordinates (inside the square image)
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
