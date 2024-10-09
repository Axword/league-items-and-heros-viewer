from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import requests
from PIL import Image
import io

class LeagueViewer:
    def __init__(self):
        self.app = Flask(__name__)
        self.cache_dir = "cache"
        self.image_cache_dir = os.path.join(self.cache_dir, "images")
        self.version_dir = os.path.join(self.cache_dir)
        self.language = "pl_PL"
        self.latest_version = self.get_latest_version()

        # Create cache directories if they do not exist
        os.makedirs(self.image_cache_dir, exist_ok=True)

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
    
        @self.app.route('/champions')
        def champions():
            champions_data = self.get_data("championFull")
            for champion_id, champion in champions_data.items():
                image_url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/champion/{champion_id}.png"
                self.fetch_image(image_url, f"{champion_id}.png")  # Pre-fetch images
            return render_template('champions.html', champions=champions_data)


        @self.app.route('/items')
        def items():
            items_data = self.get_data("item")
            for items_id, item in items_data.items():
                image_url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/item/{items_id}.png"
                self.fetch_image(image_url, f"{items_id}.png")  # Pre-fetch images
            return render_template('items.html', items=items_data, fetch_image=self.fetch_image, latest_version=self.latest_version)

        @self.app.route('/champion/<champion_id>')
        def champion_details(champion_id):
            champions_data = self.get_data("championFull")
            champion = champions_data.get(champion_id, None)
            if not champion:
                return "Champion not found", 404
            return render_template('champion_details.html', champion=champion, fetch_image=self.fetch_image)

        @self.app.route('/images/<path:image_name>')
        def serve_image(image_name):
            return send_from_directory(self.image_cache_dir, image_name)

    def get_latest_version(self):
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            return requests.get(url).json()[0]
        except:
            return "12.6.1"
    
    def get_data(self, data_type):
        version = self.get_latest_version()
        data_path = os.path.join(self.version_dir, self.language, f"{data_type}.json")
        if os.path.exists(data_path):
            with open(data_path, 'r') as file:
                return json.load(file)

        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/{self.language}/{data_type}.json"
        response = requests.get(url).json()['data']

        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, 'w') as file:
            json.dump(response, file)

        return response

    def fetch_image(self, image_url, image_name):
        image_path = os.path.join(self.image_cache_dir, image_name)
        if os.path.exists(image_path):
            return image_name
        try:
            img_data = requests.get(image_url).content
            img = Image.open(io.BytesIO(img_data)).resize((32, 32))
            img.save(image_path)
            return image_name
        except Exception as e:
            print(f"Error fetching image from URL: {image_url}, error: {e}")
            return Image.new('RGB', (32, 32), color='gray')


    def run(self):
        self.app.run(debug=True, host='0.0.0.0', port=10000)

if __name__ == "__main__":
    viewer = LeagueViewer()
    viewer.run()
