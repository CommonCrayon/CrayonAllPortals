import customtkinter as ctk

WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN

STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]

class StrongholdObject:
    def __init__(self, app, ring, index, x, z, angle):

        self.app = app

        self.number = STRONGHOLDS_RING_START[ring] + index
        self.ring = ring
        self.ring_index = index

        self.x = x
        self.z = z
        self.angle = angle

        self.entry_var = ctk.StringVar(value="")
        self.widget_status = None

        # Keep a widget per status to avoid lag of creating and destroying widgets
        self.remaining_widget_frame = None
        self.active_widget_frame = None
        self.completed_widget_frame = None

        self.canvas_items = []

        # Widget that would be next in player path
        # self.prev_sh = None
        self.next_sh = None

        # Append to Remaning on Default
        self.widget_status = "REM"
        self.app.stronghold_widgets.append(self)
        self.create_widget()
        self.draw_on_canvas()



    # Create widget in given parent container
    def create_widget(self):

        # =========================================================================================
        # self.remaining_widget_frame
        # =========================================================================================
        remaining_frame = ctk.CTkFrame(self.app.remaining_list)
        self.remaining_widget_frame = remaining_frame

        # layout config
        remaining_frame.grid_columnconfigure(0, minsize=48)
        remaining_frame.grid_columnconfigure(1, weight=1)
        remaining_frame.grid_columnconfigure(2, weight=3)
        remaining_frame.grid_columnconfigure(3, weight=3)

        # ID label
        ctk.CTkLabel(remaining_frame, text=str(self.number), font=("Arial", 24)).grid(row=0, column=0, rowspan=3, padx=5, pady=5)

        # Overworld
        ctk.CTkLabel(remaining_frame, text="Overworld", font=("Arial", 14)).grid(row=1, column=1, sticky="w", padx=5)
        ctk.CTkLabel(remaining_frame, text=str(self.x), font=("Arial", 18)).grid(row=1, column=2, sticky="e")
        ctk.CTkLabel(remaining_frame, text=str(self.z), font=("Arial", 18)).grid(row=1, column=3, padx=(0, 5), sticky="e")

        # Nether
        ctk.CTkLabel(remaining_frame, text="Nether", font=("Arial", 14)).grid(row=2, column=1, sticky="w", padx=5)
        ctk.CTkLabel(remaining_frame, text=str(round(self.x / 8)), font=("Arial", 18)).grid(row=2, column=2, sticky="e")
        ctk.CTkLabel(remaining_frame, text=str(round(self.z / 8)), font=("Arial", 18)).grid(row=2, column=3, padx=(0, 5), sticky="e")

        # Player field
        ctk.CTkEntry(remaining_frame, textvariable=self.entry_var, placeholder_text="Enter Name"
        ).grid(row=3, column=0, columnspan=2, padx=(5,2), pady=(0, 5), sticky="w")

        # Status Change Buttons
        ctk.CTkButton(remaining_frame, text="ACT", font=("Arial", 12, "bold"), fg_color="#1976D2", command=lambda status="ACT": self.set_status(status)).grid(row=3, column=2, padx=(0, 2), pady=(0, 5), sticky="ns")
        ctk.CTkButton(remaining_frame, text="COM", font=("Arial", 12, "bold"), fg_color="#43A047", command=lambda status="COM": self.set_status(status)).grid(row=3, column=3, padx=(0, 5), pady=(0, 5), sticky="ns")


        # =========================================================================================
        # self.active_widget_frame
        # =========================================================================================
        active_frame = ctk.CTkFrame(self.app.active_list)
        self.active_widget_frame = active_frame

        # layout config
        active_frame.grid_columnconfigure(0, minsize=48)
        active_frame.grid_columnconfigure(1, weight=1)
        active_frame.grid_columnconfigure(2, weight=3)
        active_frame.grid_columnconfigure(3, weight=3)

        # ID label
        ctk.CTkLabel(active_frame, text=str(self.number), font=("Arial", 24)).grid(row=0, column=0, rowspan=3, padx=5, pady=5)

        # Overworld
        ctk.CTkLabel(active_frame, text="Overworld", font=("Arial", 14)).grid(row=1, column=1, sticky="w", padx=5)
        ctk.CTkLabel(active_frame, text=str(self.x), font=("Arial", 18)).grid(row=1, column=2, sticky="e")
        ctk.CTkLabel(active_frame, text=str(self.z), font=("Arial", 18)).grid(row=1, column=3, padx=(0, 5), sticky="e")

        # Nether
        ctk.CTkLabel(active_frame, text="Nether", font=("Arial", 14)).grid(row=2, column=1, sticky="w", padx=5)
        ctk.CTkLabel(active_frame, text=str(round(self.x / 8)), font=("Arial", 18)).grid(row=2, column=2, sticky="e")
        ctk.CTkLabel(active_frame, text=str(round(self.z / 8)), font=("Arial", 18)).grid(row=2, column=3, padx=(0, 5), sticky="e")

        # Player field
        ctk.CTkEntry(active_frame, textvariable=self.entry_var, placeholder_text="Enter Name"
        ).grid(row=3, column=0, columnspan=2, padx=(5,2), pady=(0, 5), sticky="w")

        # Status Change Buttons
        ctk.CTkButton(active_frame, text="REM", font=("Arial", 12, "bold"), fg_color="#DC8D8C", command=lambda status="REM": self.set_status(status)).grid(row=3, column=2, padx=(0, 2), pady=(0, 5), sticky="ns")
        ctk.CTkButton(active_frame, text="COM", font=("Arial", 12, "bold"), fg_color="#43A047", command=lambda status="COM": self.set_status(status)).grid(row=3, column=3, padx=(0, 5), pady=(0, 5), sticky="ns")


        # =========================================================================================
        # self.completed_widget_frame
        # =========================================================================================
        completed_frame = ctk.CTkFrame(self.app.completed_list)
        self.completed_widget_frame = completed_frame

        # layout config
        completed_frame.grid_columnconfigure(0, minsize=48)
        completed_frame.grid_columnconfigure(1, weight=1)
        completed_frame.grid_columnconfigure(2, weight=3)
        completed_frame.grid_columnconfigure(3, weight=3)

        # ID label
        ctk.CTkLabel(completed_frame, text=str(self.number), font=("Arial", 24)).grid(row=0, column=0, rowspan=3, padx=5, pady=5)

        # Overworld
        ctk.CTkLabel(completed_frame, text="Overworld", font=("Arial", 14)).grid(row=1, column=1, sticky="w", padx=5)
        ctk.CTkLabel(completed_frame, text=str(self.x), font=("Arial", 18)).grid(row=1, column=2, sticky="e")
        ctk.CTkLabel(completed_frame, text=str(self.z), font=("Arial", 18)).grid(row=1, column=3, padx=(0, 5), sticky="e")

        # Nether
        ctk.CTkLabel(completed_frame, text="Nether", font=("Arial", 14)).grid(row=2, column=1, sticky="w", padx=5)
        ctk.CTkLabel(completed_frame, text=str(round(self.x / 8)), font=("Arial", 18)).grid(row=2, column=2, sticky="e")
        ctk.CTkLabel(completed_frame, text=str(round(self.z / 8)), font=("Arial", 18)).grid(row=2, column=3, padx=(0, 5), sticky="e")

        # Player field
        ctk.CTkEntry(completed_frame, textvariable=self.entry_var, placeholder_text="Enter Name"
        ).grid(row=3, column=0, columnspan=2, padx=(5,2), pady=(0, 5), sticky="w")

        # Status Change Buttons
        ctk.CTkButton(completed_frame, text="REM", font=("Arial", 12, "bold"), fg_color="#DC8D8C", command=lambda status="REM": self.set_status(status)).grid(row=3, column=2, padx=(0, 2), pady=(0, 5), sticky="ns")
        ctk.CTkButton(completed_frame, text="ACT", font=("Arial", 12, "bold"), fg_color="#1976D2", command=lambda status="ACT": self.set_status(status)).grid(row=3, column=3, padx=(0, 5), pady=(0, 5), sticky="ns")


    def set_status(self, new_status: str):

        self.widget_status = new_status

        self.draw_on_canvas()

        # Get next widget in path
        if new_status == "COM" and self.next_sh is not None:

            next_obj = next((sh for sh in self.app.stronghold_objects if sh.number == self.next_sh), None)

            if next_obj and next_obj.widget_status == "REM":
                print(f"Setting: {self.next_sh} to Active")
                next_obj.set_status("ACT")

        
        # reapply filters
        self.app.filter_remaining_strongholds()
        self.app.filter_active_strongholds()
        self.app.filter_complete_strongholds()



    # Method to update widget entry from PlayerManager.py
    def update_name(self, new_text):
        # Get the entry of the widgets
        rem = self.remaining_widget_frame.winfo_children()[7]
        act = self.active_widget_frame.winfo_children()[7]
        com = self.completed_widget_frame.winfo_children()[7]

        # Apply given text
        rem.configure(textvariable=ctk.StringVar(value=new_text))
        act.configure(textvariable=ctk.StringVar(value=new_text))
        com.configure(textvariable=ctk.StringVar(value=new_text))



    # Use function to get counts too, if 1 returned then count otherwise return 0
    def update_from_filter(self, status, filtered_set) -> int:

        if status == "REM" and self.remaining_widget_frame is not None:
            if self.widget_status == status and self in filtered_set:
                self.remaining_widget_frame.pack(fill="x")
                return 1
            else:
                self.remaining_widget_frame.pack_forget()

        elif status == "ACT" and self.active_widget_frame is not None:
            if self.widget_status == status and self in filtered_set:
                self.active_widget_frame.pack(fill="x")
                return 1
            else:
                self.active_widget_frame.pack_forget()

        elif status == "COM" and self.completed_widget_frame is not None:
            if self.widget_status == status and self in filtered_set:
                self.completed_widget_frame.pack(fill="x")
                return 1
            else:
                self.completed_widget_frame.pack_forget()

        return 0



    # Draw on canvas
    def draw_on_canvas(self):

        # Use square image size
        side = self.app.image_size 

        offset_x = (self.app.canvas.winfo_width() - side) // 2
        offset_y = (self.app.canvas.winfo_height() - side) // 2

        # Map world coordinates to image coordinates
        img_x = int((self.x - WORLD_MIN) / WORLD_RANGE * side) + offset_x
        img_y = int((self.z - WORLD_MIN) / WORLD_RANGE * side) + offset_y

        # Delete previous canvas items if any
        for item in self.canvas_items:
            try:
                self.app.canvas.delete(item)
            except Exception:
                pass


        # Style presets by status
        STATUS_STYLE = {
            "ACT": {
                "color": "#1976D2",
                "text":  "#FFFFFF",
                "font_size": 18,
                "radius": 18,
            },
            "REM": {
                "color": "#DC8D8C",
                "text":  "#FFFFFF",
                "font_size": 14,
                "radius": 14,
            },
            "COM": {
                "color": "#43A047",
                "text":  "#FFFFFF",
                "font_size": 14,
                "radius": 14,
            },
        }

        # Get style for current status (fallback: Remaining)
        style = STATUS_STYLE.get(self.widget_status, STATUS_STYLE["REM"])

        dot_color  = style["color"]
        font_size  = style["font_size"]
        dot_radius = style["radius"]


        # Draw new dot and text
        dot = self.app.canvas.create_oval(img_x-dot_radius, img_y-dot_radius, img_x+dot_radius, img_y+dot_radius, fill=dot_color, outline="")
        text = self.app.canvas.create_text(img_x, img_y, text=str(self.number), fill="black", font=("Arial", font_size, 'bold'))

        self.canvas_items = [dot, text]



    # Clean up everything for this stronghold
    def destroy(self):
        # delete canvas items
        for item in self.canvas_items:
            try:
                self.app.canvas.delete(item)
            except Exception:
                pass

        # destroy all widgets
        if self.remaining_widget_frame is not None:
            try:
                self.remaining_widget_frame.destroy()
                self.remaining_widget_frame = None
            except Exception:
                pass

        if self.active_widget_frame is not None:
            try:
                self.active_widget_frame.destroy()
                self.active_widget_frame = None
            except Exception:
                pass

        if self.completed_widget_frame is not None:
            try:
                self.completed_widget_frame.destroy()
                self.completed_widget_frame = None
            except Exception:
                pass

        self.canvas_items = []

