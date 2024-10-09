import requests
import json
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import io

class LeagueViewer:
    def __init__(self, root):
        self.cache_dir = "cache"
        self.champion_images = {}
        self.item_images = {}
        self.image_cache_dir = os.path.join(self.cache_dir, "images")
        self.version_dir = os.path.join(self.cache_dir)
        self.language_var = tk.StringVar(value="pl_PL")
        self.current_language = "pl_PL"
        self.latest_version = self.get_latest_version()
        self.version_dir = os.path.join(self.cache_dir, self.latest_version)
        self.data_dir = os.path.join(self.version_dir, self.current_language)
        self.tags = set()
        self.tag_vars = {}
        self.map_11_var = tk.BooleanVar(value=True)
        self.language_texts = {
            "choose_language": {"pl_PL": "Wybierz język:", "en_US": "Choose Language:"},
            "search": {"pl_PL": "Wyszukaj bohatera:", "en_US": "Search for Champion:"},
            "skills": {"pl_PL": "Umiejętności", "en_US": "Skills"},
            "skins": {"pl_PL": "Skórki", "en_US": "Skins"},
            "error_message": {"pl_PL": "Nie udało się pobrać danych!", "en_US": "Failed to fetch data!"},
            "champions_tab": {"pl_PL": "Bohaterowie", "en_US": "Champions"},
            "items_tab": {"pl_PL": "Przedmioty", "en_US": "Items"}
        }
        self.create_cache_dirs()
        self.champions = self.load_or_fetch_data("championFull")
        self.items = self.load_or_fetch_data("item")
        self.setup_gui(root)
        self.update_champion_grid()
        self.update_item_list()

    def create_cache_dirs(self):
        os.makedirs(self.image_cache_dir, exist_ok=True)

    def get_latest_version(self):
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            return requests.get(url).json()[0]
        except:
            return "12.6.1"

    def save_to_cache(self, data_type, data):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(os.path.join(self.data_dir, f"{data_type}.json"), "w") as file:
            json.dump(data, file)

    def load_from_cache(self, data_type):
        print(self.data_dir)
        path = os.path.join(self.data_dir, f"{data_type}.json")
        if os.path.exists(path):
            with open(path, "r") as file:
                return json.load(file)
        return None

    def load_or_fetch_data(self, data_type):
        data = self.load_from_cache(data_type)
        if not data:
            url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/data/{self.current_language}/{data_type}.json"
            response = requests.get(url)
            data = response.json()["data"]
            self.save_to_cache(data_type, data)
        return data

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

    def setup_gui(self, root):
        root.title("League of Legends Viewer")

        # Language selection
        self.language_label =ttk.Label(root,text=self.language_texts["choose_language"][self.current_language])
        self.language_label.pack(pady=5)
        lang_frame = tk.Frame(root)
        lang_frame.pack()
        ttk.Radiobutton(lang_frame, text="Polski", variable=self.language_var, value="pl_PL", command=self.update_language).pack(side=tk.LEFT)
        ttk.Radiobutton(lang_frame, text="English", variable=self.language_var, value="en_US", command=self.update_language).pack(side=tk.LEFT)

        # Tab Control
        self.tab_control = ttk.Notebook(root)
        self.champions_tab = ttk.Frame(self.tab_control)
        self.items_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.champions_tab, text=self.language_texts["champions_tab"][self.current_language])
        self.tab_control.add(self.items_tab, text=self.language_texts["items_tab"][self.current_language])
        self.tab_control.pack(expand=True, fill="both")

        # Search and Listbox for champions
        self.search_var = tk.StringVar()
        self.search_label = ttk.Label(self.champions_tab, text=self.language_texts["search"][self.current_language])
        self.search_label.pack(pady=5)
        search_entry = ttk.Entry(self.champions_tab, textvariable=self.search_var)
        search_entry.pack(pady=5)
        search_entry.bind("<KeyRelease>", self.filter_champions)  # Keep this for search filtering

        # Create a frame to hold the champion grid
        self.champion_grid_frame = tk.Frame(self.champions_tab)
        self.champion_grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Listbox for items
        self.item_list_frame = tk.Frame(self.items_tab)
        self.item_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_tag_checkboxes(self.item_list_frame)

    def update_champion_grid(self):
        """Update the grid of champions displayed as images based on the search filter."""
        # Clear existing widgets in the frame if any
        for widget in self.champions_tab.winfo_children():
            widget.destroy()  # Clear existing images

        # Get the current search term
        search_term = self.search_var.get().lower()
        filtered_champions = {champion_id: champion for champion_id, champion in self.champions.items() if search_term in champion["name"].lower()}

        # Create a grid of images for filtered champions
        for index, (champion_id, champion) in enumerate(filtered_champions.items()):
            img = self.fetch_image(f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/champion/{champion_id}.png", f"{champion_id}.png")
            self.champion_images[champion["name"]] = ImageTk.PhotoImage(img)

            # Create a button for each image
            name_label = tk.Label(self.champions_tab, text=champion["name"], wraplength=72)
            name_label.grid(row=index // 20, column=(index % 20), padx=3, pady=(0, 20))
            btn = tk.Button(self.champions_tab, image=self.champion_images[champion["name"]], command=lambda champ=champion: self.show_champion_details(champ))
            btn.grid(row=index // 20, column=index % 20, padx=5, pady=(60, 0))  # Arrange in a grid of 10 per row



    def update_item_list(self):
        for widget in self.items_tab.winfo_children():
            widget.destroy()

        unique_items = {}
        for item_id, item in self.items.items():
            if self.is_item_visible(item) and (not self.map_11_var.get() or item['maps'].get('11', False)):
                if item["name"] not in unique_items:
                    unique_items[item["name"]] = item
                    unique_items[item["name"]]["id"] = item_id

        sorted_unique_items = sorted(unique_items.items(), key=lambda x: x[1]['gold']['total'])

        for index, (item_name, item) in enumerate(sorted_unique_items):
            img = self.fetch_image(f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/item/{item['id']}.png", f"{item['id']}.png")
            if img:
                self.item_images[item["name"]] = ImageTk.PhotoImage(img)

                name_label = tk.Label(self.items_tab, text=item["name"], wraplength=72)
                name_label.grid(row=index // 20, column=(index % 20) * 2, padx=3, pady=(0, 20))
                btn = tk.Button(self.items_tab, image=self.item_images[item["name"]],
                                command=lambda item=item: self.show_item_details(item))
                btn.grid(row=index // 20, column=(index % 20) * 2, padx=3, pady=(60, 0))


    def filter_champions(self, event=None):
        self.update_champion_grid()

    def is_item_visible(self, item):
        """Check if the item is visible based on selected tags."""
        # Check if item has any of the tags stored in tag_vars
        return any(self.tag_vars.get(tag, False).get() for tag in item['tags'])

    def create_tag_checkboxes(self, tag_frame):
        """Create checkboxes for each tag in the item data."""
        for item_id, item_data in self.items.items():
            print(item_id)
            print(self.tags)
            print(item_data)
            self.tags.update(item_data['tags'])

        self.tag_vars = {tag: tk.BooleanVar(value=True) for tag in self.tags}

        max_per_row = 10
        row_index = 0

        for index, (tag, var) in enumerate(self.tag_vars.items()):
            cb = tk.Checkbutton(tag_frame, text=tag, variable=var, command=self.update_item_list)
            cb.grid(row=row_index, column=index % max_per_row, padx=5, pady=2, sticky='w')
            
            if (index + 1) % max_per_row == 0:
                row_index += 1

    def on_champion_select(self, event):
        selected_index = self.champion_list.curselection()
        if selected_index:  # Check if there is a selection
            champion_name = self.champion_list.get(selected_index)
            champion_image = self.champion_images.get(champion_name)

            # Create or update the label to show the selected champion's image
            if champion_image:  # Ensure the image exists
                if hasattr(self, 'champion_image_label'):
                    self.champion_image_label.config(image=champion_image)
                else:
                    self.champion_image_label = tk.Label(self.champions_tab, image=champion_image)
                    self.champion_image_label.pack(pady=10)

    def on_item_select(self, event):
        selected = self.item_list.get(self.item_list.curselection())
        item = next((itm for itm in self.items.values() if itm["name"] == selected), None)
        if item:
            self.show_item_details(item)

    def show_champion_details(self, champion):
        details_window = tk.Toplevel()
        details_window.title(champion["name"])

        skills_frame = ttk.LabelFrame(details_window, text="Skills")
        skills_frame.pack(fill="both", expand=True, padx=10, pady=10)
        for spell in champion["spells"]:
            ttk.Label(skills_frame, text=f"{spell['name']}: {spell['description']}").pack(anchor="w")

        skins_frame = ttk.LabelFrame(details_window, text="Skins")
        skins_frame.pack(fill="both", expand=True, padx=10, pady=10)
        for skin in champion["skins"]:
            ttk.Label(skins_frame, text=skin["name"]).pack(anchor="w")

    def show_item_details(self, item):
        details_window = tk.Toplevel()
        details_window.title(item["name"])
        ttk.Label(details_window, text=item.get("description", "No description")).pack(padx=10, pady=10)

    def update_language(self):
        self.current_language = self.language_var.get()
        self.data_dir = os.path.join(self.version_dir, self.current_language)
        self.champions = self.load_or_fetch_data("championFull")
        self.items = self.load_or_fetch_data("item")
        self.update_champion_grid()
        self.update_item_list()
        self.update_gui_language()

    def update_gui_language(self):
        self.search_label.config(text=self.language_texts["search"][self.current_language])
        self.language_label.config(text=self.language_texts["choose_language"][self.current_language])
        self.tab_control.tab(0, text=self.language_texts["champions_tab"][self.current_language])
        self.tab_control.tab(1, text=self.language_texts["items_tab"][self.current_language])

if __name__ == "__main__":
    root = tk.Tk()
    app = LeagueViewer(root)
    root.mainloop()
