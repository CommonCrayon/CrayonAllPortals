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
        self.status_var = ctk.StringVar()

        self.widget_frame = None
        self.entry_widget = None
        self.canvas_items = []

        # Append to List
        if self.number in STRONGHOLDS_RING_START:
            self.status_var.set("Active")
            self.app.active_strongholds.append(self)
            parent = self.app.active_list
        else:
            self.status_var.set("Remaining")
            self.app.remaining_strongholds.append(self)
            parent = self.app.remaining_list
        
        self.create_widget(parent)
        self.app.update_counts()
        self.draw_on_canvas()



    # Create widget in given parent container
    def create_widget(self, parent):
        if self.widget_frame is None:
            frame = ctk.CTkFrame(parent)
            self.widget_frame = frame

            # layout config
            frame.grid_columnconfigure(0, minsize=48)
            frame.grid_columnconfigure(1, weight=1)
            frame.grid_columnconfigure(2, weight=1)
            frame.grid_columnconfigure(3, weight=1)

            # ID label
            ctk.CTkLabel(frame, text=str(self.number), font=("Arial", 24)).grid(row=0, column=0, rowspan=3, padx=5, pady=5)

            # Overworld
            ctk.CTkLabel(frame, text="Overworld", font=("Arial", 18)).grid(row=1, column=1, sticky="w", padx=5)
            ctk.CTkLabel(frame, text=str(self.x), font=("Arial", 18)).grid(row=1, column=2, sticky="e")
            ctk.CTkLabel(frame, text=str(self.z), font=("Arial", 18)).grid(row=1, column=3, padx=(0, 5), sticky="e")

            # Nether
            ctk.CTkLabel(frame, text="Nether", font=("Arial", 18)).grid(row=2, column=1, sticky="w", padx=5)
            ctk.CTkLabel(frame, text=str(round(self.x / 8)), font=("Arial", 18)).grid(row=2, column=2, sticky="e")
            ctk.CTkLabel(frame, text=str(round(self.z / 8)), font=("Arial", 18)).grid(row=2, column=3, padx=(0, 5), sticky="e")

            # Player field
            ctk.CTkEntry(frame, textvariable=self.entry_var, placeholder_text="Enter Name"
            ).grid(row=3, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

            # Status combo
            status_box = ctk.CTkComboBox(
                frame,
                values=["Active", "Remaining", "Complete"],
                state="readonly",
                variable=self.status_var,
                command=self.on_status_change
            )
            status_box.grid(row=3, column=2, columnspan=2, padx=5, pady=(0, 5), sticky="ew")


        # Re-parent safely
        self.widget_frame.pack_forget()
        self.widget_frame.pack(in_=parent, fill="x", pady=2, padx=2)



    # Update on status change
    def on_status_change(self, *_):
        target = {
            "Active": self.app.active_list,
            "Remaining": self.app.remaining_list,
            "Complete": self.app.completed_list,
        }[self.status_var.get()]

        self.destroy()
        self.create_widget(target)
        self.app.update_counts()
        self.draw_on_canvas()



    def update_name(self, new_text):
        # Get the entry widget
        entry = self.widget_frame.winfo_children()[7]

        entry.configure(textvariable=ctk.StringVar(value=new_text))


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
            "Active": {
                "color": "#1976D2",
                "text":  "#FFFFFF",
                "font_size": 18,
                "radius": 18,
            },
            "Remaining": {
                "color": "#DC8D8C",
                "text":  "#FFFFFF",
                "font_size": 14,
                "radius": 14,
            },
            "Complete": {
                "color": "#43A047",
                "text":  "#FFFFFF",
                "font_size": 14,
                "radius": 14,
            },
        }

        # Get style for current status (fallback: Remaining)
        status = self.status_var.get()
        style = STATUS_STYLE.get(status, STATUS_STYLE["Remaining"])

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

        # Save latest entry var
        self.entry_var = ctk.StringVar(value=str(self.widget_frame.winfo_children()[7].get()))

        # destroy widget
        if self.widget_frame is not None:
            try:
                self.widget_frame.destroy()
            except Exception:
                pass
        self.widget_frame = None
        self.canvas_items = []
        self.app.update_counts()

