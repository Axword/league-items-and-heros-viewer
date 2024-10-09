import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import io
import requests
import json


class ItemViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("League of Legends - Item Viewer")
        self.cache_dir = "cache"
        self.image_cache_dir = os.path.join(self.cache_dir, "images")
        self.item_images = {}
        self.items = {}
        self.tags = set()
        self.tag_vars = {}
        self.map_11_var = tk.BooleanVar(value=True)
        self.root.geometry("1680x1000")

        # Initialize GUI elements
        self.latest_version = self.get_latest_version()
        self.items = self.fetch_data("pl_PL", "item")
        self.init_gui()

        self.load_images_from_cache()
        self.update_item_grid()

        self.root.mainloop()

    def init_gui(self):
        # Create a frame for tag filtering
        tag_frame = tk.Frame(self.root)
        tag_frame.pack(pady=5)

        # Create checkboxes for each tag
        self.create_tag_checkboxes(tag_frame)

        # Checkbox for Map 11 filter using grid
        map_checkbox = tk.Checkbutton(tag_frame, text="Show only Map 11 items", variable=self.map_11_var, command=self.update_item_grid)
        map_checkbox.grid(row=len(self.tag_vars) // 10 + 1, column=0, padx=5, pady=5, sticky='w')  # Place it below the last tag row

        # Create a canvas to hold the item grid
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a vertical scrollbar
        self.scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame to hold the item images
        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        # Bind the frame to update the scroll region
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Bind mouse wheel event for scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)


    def create_tag_checkboxes(self, tag_frame):
        """Create checkboxes for each tag in the item data."""
        for item_id, item_data in self.items.items():
            self.tags.update(item_data['tags'])  # Collect tags from items

        # Create a BooleanVar for each tag
        self.tag_vars = {tag: tk.BooleanVar(value=True) for tag in self.tags}

        # Create checkboxes for each tag, arranging them in two rows
        max_per_row = 10  # Maximum checkboxes per row
        row_index = 0     # Current row index

        for index, (tag, var) in enumerate(self.tag_vars.items()):
            cb = tk.Checkbutton(tag_frame, text=tag, variable=var, command=self.update_item_grid)
            cb.grid(row=row_index, column=index % max_per_row, padx=5, pady=2, sticky='w')  # Adjust padding and alignment
            
            # Move to the next row after reaching max_per_row
            if (index + 1) % max_per_row == 0:
                row_index += 1


    def load_images_from_cache(self):
        """Load item images from cache to avoid fetching each time."""
        if not os.path.exists(self.image_cache_dir):
            os.makedirs(self.image_cache_dir)
        for item_id, item in self.items.items():
            image_path = os.path.join(self.image_cache_dir, f"{item_id}.png")
            if os.path.exists(image_path):
                img = Image.open(image_path).resize((72, 72))  # Resize for display
                self.item_images[item["name"]] = ImageTk.PhotoImage(img)

    def update_item_grid(self):
        """Update the grid of items displayed as images based on selected tags and map filter."""
        for widget in self.frame.winfo_children():
            widget.destroy()  # Clear existing images

        # Filter items based on selected tags and map 11, while collecting unique items
        unique_items = {}
        for item_id, item in self.items.items():
            if self.is_item_visible(item) and (not self.map_11_var.get() or item['maps'].get('11', False)):
                if item["name"] not in unique_items:
                    unique_items[item["name"]] = item
                    unique_items[item["name"]]["id"] = item_id

        # Sort unique items by total gold required for purchasing
        sorted_unique_items = sorted(unique_items.items(), key=lambda x: x[1]['gold']['total'])

        # Create a grid of images for unique items
        for index, (item_name, item) in enumerate(sorted_unique_items):
            img = self.fetch_image(f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/item/{item['id']}.png", f"{item['id']}.png")
            if img:
                self.item_images[item["name"]] = ImageTk.PhotoImage(img)

                # Place the item name and button in the grid
                name_label = tk.Label(self.frame, text=item["name"], wraplength=72)
                name_label.grid(row=index // 20, column=(index % 20) * 2, padx=3, pady=(0, 20))  # Offset for item name
                btn = tk.Button(self.frame, image=self.item_images[item["name"]],
                                command=lambda item=item: self.show_item_details(item))
                btn.grid(row=index // 20, column=(index % 20) * 2, padx=3, pady=(60, 0))  # Double space for the name below




    def fetch_image(self, image_url, image_name):
        image_path = os.path.join(self.image_cache_dir, image_name)
        if os.path.exists(image_path):
            return Image.open(image_path)
        try:
            img_data = requests.get(image_url).content
            img = Image.open(io.BytesIO(img_data)).resize((32, 32))
            img.save(image_path)
            return img
        except Exception as e:
            print(f"Error fetching image from URL: {image_url}, error: {e}")
            return Image.new('RGB', (32, 32), color='gray')


    def is_item_visible(self, item):
        """Check if the item is visible based on selected tags."""
        # Check if item has any of the tags stored in tag_vars
        return any(self.tag_vars.get(tag, False).get() for tag in item['tags'])

    def show_item_details(self, item_data):
        """Display item details in a new window."""
        details_window = tk.Toplevel(self.root)
        details_window.title(item_data["name"])
        details_label = tk.Label(details_window, text=f"Name: {item_data['name']}\nDescription: {item_data.get('plaintext', 'No description')}")
        details_label.pack(padx=10, pady=10)

    def get_latest_version(self):
        """Fetch the latest version of the game."""
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()[0]  # Return the latest version
        else:
            messagebox.showerror("Error", "Failed to fetch the latest version!")
            return "12.6.1"  # Default value in case of error

    def fetch_data(self, language="pl_PL", data_type="item"):
        """Fetch data for items."""
        url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/data/{language}/{data_type}.json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            messagebox.showerror("Error", "Failed to fetch data!")
            return {}

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        # Scroll the canvas based on the mouse wheel movement
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# Run the application
if __name__ == "__main__":
    ItemViewer()
