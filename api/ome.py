import base64

import requests

from sprong import sprongbean, SprongBeanRepo


@sprongbean
class OmeApi:
    def __init__(self, ome_config):
        self.ome_api = ome_config["apiUrl"]
        self.ome_password = ome_config["apiPassword"]
        self.ome_headers = self.create_ome_headers()

    def create_ome_headers(self):
        return {"Authorization": f"Basic {base64.b64encode(self.ome_password.encode()).decode()}"}

    def get(self, path):
        return requests.get(f"{self.ome_api}/v1/{path}", headers=self.ome_headers).json().get('response')
