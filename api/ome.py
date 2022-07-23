import base64

import requests


class OmeApi:
    def __init__(self, api_url, api_password):
        self.ome_api = api_url
        self.ome_password = api_password
        self.ome_headers = self.create_ome_headers()

    def create_ome_headers(self):
        return {"Authorization": f"Basic {base64.b64encode(self.ome_password.encode()).decode()}"}

    def get(self, path):
        return requests.get(f"{self.ome_api}/v1/{path}", headers=self.ome_headers).json().get('response')
