import customtkinter as ctk

WORLD_MIN = -24320
WORLD_MAX = 24320
WORLD_RANGE = WORLD_MAX - WORLD_MIN

STRONGHOLDS_RING_START = [1, 4, 10, 20, 35, 56, 84, 120]

class StrongholdObject:
    def __init__(self, app, ring, index, x, z):
        self.app = app
        self.ring = ring
        self.index = index
        self.x = x
        self.z = z

        self.entry_var = ctk.StringVar(value="")

        self.widget_frame = None

        # store canvas IDs so we can delete later
        self.canvas_items = []  

        # Append to List
        if (STRONGHOLDS_RING_START[ring] + index) in STRONGHOLDS_RING_START:
            self.status_var = ctk.StringVar(value="Active")
            self.create_widget(parent=self.app.active_list)
        else:
            self.status_var = ctk.StringVar(value="Remaining")
            self.create_widget(parent=self.app.remaining_list)

        self.draw_on_canvas()



    # Create widget in given parent container
    def create_widget(self, parent):
        # Store previous entry content if it exists
        entered_name_on_widget = ""

        # Destroy old widget and get data from it
        if self.widget_frame is not None:
            try:
                # Try to get existing entry value
                entry_widget = self.widget_frame.nametowidget(self.widget_frame.winfo_children()[-2])
                entered_name_on_widget = entry_widget.get()
            except Exception:
                pass

            try:
                self.widget_frame.destroy()
            except Exception:
                pass


        frame = ctk.CTkFrame(parent)
        self.widget_frame = frame

        # layout config
        frame.grid_columnconfigure(0, minsize=48)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        # ID label
        ctk.CTkLabel(
            frame,
            text=str(STRONGHOLDS_RING_START[self.ring] + self.index),
            font=("Arial", 20)
        ).grid(row=0, column=0, rowspan=3, padx=5, pady=5)

        # Overworld
        ctk.CTkLabel(frame, text="Overworld").grid(row=1, column=1, sticky="w", padx=5)
        ctk.CTkLabel(frame, text=str(self.x)).grid(row=1, column=2, sticky="e")
        ctk.CTkLabel(frame, text=str(self.z)).grid(row=1, column=3, padx=(0, 5), sticky="e")

        # Nether
        ctk.CTkLabel(frame, text="Nether").grid(row=2, column=1, sticky="w", padx=5)
        ctk.CTkLabel(frame, text=str(round(self.x / 8))).grid(row=2, column=2, sticky="e")
        ctk.CTkLabel(frame, text=str(round(self.z / 8))).grid(row=2, column=3, padx=(0, 5), sticky="e")

        # Player field
        self.entry_var = ctk.StringVar(value=entered_name_on_widget)

        ctk.CTkEntry(frame, textvariable=self.entry_var, placeholder_text="Enter Name").grid(
            row=3, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w"
        )

        # Status combo
        status_box = ctk.CTkComboBox(
            frame,
            values=["Active", "Remaining", "Complete"],
            state="readonly",
            variable=self.status_var,
            command=self.on_status_change
        )
        status_box.grid(row=3, column=2, columnspan=2, padx=5, pady=(0, 5), sticky="ew")

        frame.pack(fill="x", pady=2, padx=2)
        self.app.update_counts()



    # Update on status change
    def on_status_change(self, *args):
        new_status = self.status_var.get()
        target = {
            "Active": self.app.active_list,
            "Remaining": self.app.remaining_list,
            "Complete": self.app.completed_list,
        }[new_status]

        self.app.update_counts()
        self.create_widget(parent=target)
        self.draw_on_canvas()



    # Draw on canvas
    def draw_on_canvas(self):

        # Size of Image Frame - minus 10 for padding
        frame_size_x = int((self.app.image_frame.winfo_width()/2) - 10) * 2
        frame_size_y = int((self.app.image_frame.winfo_height()/2) - 10) * 2

        # Position of stronghold
        img_x = int((self.x - WORLD_MIN) / WORLD_RANGE * frame_size_x)
        img_y = int((self.z - WORLD_MIN) / WORLD_RANGE * frame_size_y)

        # Determine color based on status
        color_map = {
            "Active": "blue",
            "Remaining": "red",
            "Complete": "green"
        }
        dot_color = color_map.get(self.status_var.get(), "red")

        # Delete previous canvas items if any
        for item in self.canvas_items:
            try:
                self.app.canvas.delete(item)
            except Exception:
                pass

        # Draw new dot and text
        dot = self.app.canvas.create_oval(img_x-5, img_y-5, img_x+5, img_y+5, fill=dot_color, outline="")
        text = self.app.canvas.create_text(
            img_x + 10,
            img_y,
            text=str(STRONGHOLDS_RING_START[self.ring] + self.index),
            fill="black",
            anchor="w",
            font=("Arial", 18)
        )

        self.canvas_items = [dot, text]



    # Clean up everything for this stronghold
    def destroy(self):
        # delete canvas items
        for item in self.canvas_items:
            try:
                self.app.canvas.delete(item)
            except Exception:
                pass

        # destroy widget
        if self.widget_frame is not None:
            try:
                self.widget_frame.destroy()
            except Exception:
                pass
        self.widget_frame = None
        self.canvas_items = []
        self.app.update_counts()

