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

        self.canvas_items = []

        # Append to Remaning on Default
        self.draw_on_canvas()


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

        # Change color depending on ring stronghold or not.
        if self.number in STRONGHOLDS_RING_START:
            dot_color  = "#43A047"
        else:
            dot_color  = "#DC8D8C"

        font_size  = 18
        dot_radius = 18
        

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

        self.canvas_items = []

