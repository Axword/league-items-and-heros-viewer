from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import json
import requests
from PIL import Image
import io
import re


class LeagueViewer:
    def __init__(self):
        self.app = Flask(__name__)
        self.cache_dir = "cache"
        self.image_cache_dir = os.path.join(self.cache_dir, "images")
        self.version_dir = os.path.join(self.cache_dir)
        self.language = "pl_PL"
        self.latest_version = self.get_latest_version()
        self.sorted_unique_items = {"en_US": None, 'pl_PL': None}
        self.heores = {"en_US": None, 'pl_PL': None}
        os.makedirs(self.image_cache_dir, exist_ok=True)

        self.setup_routes()
        self.translations = {
            'en_US': {
                'back_to_champions': 'Back to champions',
                'back_to_items': 'Back to items',
                'welcome': 'Welcome to League Viewer',
                'champions': 'Champions',
                'items': 'Items',
                'language': "Language",
                "polish": "Polish",
                "english": "English",
                'stats': "Stats",
                'tags': "Tags",
                'skins': "Skins",
                'skills': "Skills",
                'description': "Description",
                'builds_into': "Builds Into",
                'cost': "Cost",
            },
            'pl_PL': {
                'back_to_champions': 'Powrót do bohaterów',
                'back_to_items': 'Powrót do przedmiotów',
                'welcome': 'Witamy w League Viewer',
                'champions': 'Bohaterowie',
                'items': 'Przedmioty',
                'language': "Język",
                "polish": "Polski",
                "english": "Angielski",
                'stats': "Statystyki",
                'tags': "Tagi",
                'skins': "Skiny",
                'skills': "Umiejętności",
                'description': "Opis",
                "builds_into": "Buduje się w",
                "cost": 'Koszt'
            }
        }

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html', language=self.language, translations=self.translations[self.language])

        @self.app.route('/set_language', methods=['POST'])
        def set_language():
            self.language = request.form.get('language')
            return redirect(request.referrer)

        @self.app.route('/champions')
        def champions():
            champions_data = self.get_data("championFull")
            if not self.heores[self.language]:
                for champion_id, champion in champions_data.items():
                    image_url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/champion/{champion_id}.png"
                    self.fetch_image(image_url, f"{champion_id}.png")
                self.heores[self.language] = champions_data
            return render_template('champions.html', language=self.language, champions=champions_data, translations=self.translations[self.language])

        @self.app.route('/items')
        def items():
            items_data = self.get_data("item")
            if not self.sorted_unique_items[self.language]:
                unique_items = {}
                for item_id, item in items_data.items():
                    if item['maps'].get('11', False) and item["name"] not in unique_items:
                        unique_items[item["name"]] = item
                        unique_items[item["name"]]["id"] = item_id
                        unique_items[item["name"]]["name"] = self.strip_html_tags(item['name'])
                        image_url = f"https://ddragon.leagueoflegends.com/cdn/{self.latest_version}/img/item/{item_id}.png"
                        self.fetch_image(image_url, f"{item_id}.png")
                
                self.sorted_unique_items[self.language] = sorted(unique_items.items(), key=lambda x: x[1]['gold']['total'])

            return render_template('items.html', items=self.sorted_unique_items[self.language], language=self.language, fetch_image=self.fetch_image, translations=self.translations[self.language])

        @self.app.route('/champion/<champion_id>')
        def champion_details(champion_id):
            champions_data = self.get_data("championFull")
            champion = champions_data.get(champion_id, None)
            if not champion:
                return "Champion not found", 404
            for spell in champion['spells']:
                spell['description'] = self.strip_html_tags(spell['description'])
            return render_template('champion_details.html', champion=champion, language=self.language, translations=self.translations[self.language], fetch_image=self.fetch_image)

        @self.app.route('/item/<item_id>')
        def item_details(item_id):
            item_data = self.get_data("item")
            item = item_data.get(item_id, None)
            if not item:
                return "Champion not found", 404
            item['description'] = self.strip_html_tags(item['description'])
            return render_template('item_details.html', item_data=item_data, language=self.language, item=item, item_id=item_id, translations=self.translations[self.language], fetch_image=self.fetch_image)


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

    def strip_html_tags(self, text):
        text = text.replace('<br>', '\n').replace('<br />', '\n').replace('<br/>', '\n')
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

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
