import base64
import json
import os

import requests
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def combine_dicts(*dicts):
    return {k: v for d in dicts for k, v in d.items()}


class OmeApi:
    def __init__(self):
        with open(os.path.join(SCRIPT_DIR, "config.yaml"), 'r') as f:
            self.config = yaml.safe_load(f)
        ome_config = self.config["ovenMediaEngine"]
        self.ome_api = ome_config["apiUrl"]
        self.ome_password = ome_config["apiPassword"]
        self.ome_headers = self.create_ome_headers()
        self.base_webrtc = ome_config["webRtcPublishUrl"]
        self.base_llhls = ome_config["llHlsPublishUrl"]
        self.base_thumbs = ome_config["thumbnailPublishUrl"]

    def handle(self, environ, start_response):
        try:
            path = environ['PATH_INFO']
            if path.endswith('/'):
                path = path[:-1]

            if path == '/v1/streams':
                result = self.get_streams()
            elif path == '':
                result = self.old_api()
            else:
                result = path

            start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8')])
            return json.dumps(result).encode('utf-8')
        except Exception as e:
            start_response('500 oops', [('Content-Type', 'application/json; charset=utf-8')])
            return json.dumps({"message": str(e)}).encode('utf-8')

    def ome_get(self, path):
        return requests.get(f"{self.ome_api}/v1/{path}", headers=self.ome_headers).json().get('response')

    def old_api(self):
        r = self.ome_get("vhosts/default/apps/bam/streams")
        r2 = self.ome_get("vhosts/default/apps/app/streams")
        return [f"bam/{stream}" for stream in r] + ["app/twitch" for stream in r2]

    def get_streams(self):
        dbg = []
        result = {}

        def get_outputs(app, stream, publisher):
            return {
                    "webrtc": {
                        "webrtc-udp": f"{self.base_webrtc}/{app}/{stream}",
                        "webrtc-tcp": f"{self.base_webrtc}/{app}/{stream}?transport=tcp",
                    },
                    "llhls": {"llhls": f"{self.base_llhls}/{app}/{stream}/llhls.m3u8"}
            }.get(publisher, {})

        apps = self.ome_get("vhosts/default/apps")
        for app in apps:
            app_details = self.ome_get(f"vhosts/default/apps/{app}")
            publishers = list(app_details["publishers"].keys())
            streams = self.ome_get(f"vhosts/default/apps/{app}/streams")
            for stream in streams:
                try:
                    stream_details = self.ome_get(f"vhosts/default/apps/{app}/streams/{stream}")
                    video_track = [t for t in stream_details["input"]["tracks"] if "video" in t][0]["video"]
                    audio_track = [t for t in stream_details["input"]["tracks"] if "audio" in t][0]["audio"]
                    stream_result = {
                            "name": stream,
                            "streams": {"main": {"protocols": combine_dicts(*(get_outputs(app, stream, p) for p in publishers))}},
                            "created": stream_details["input"]["createdTime"],
                            "video": {
                                "width": video_track.get("width"),
                                "height": video_track.get("height"),
                                "codec": video_track.get("codec"),
                                "bitrate": video_track.get("bitrate"),
                                "framerate": video_track.get("framerate"),
                            },
                            "audio": {
                                "bitrate": audio_track.get("bitrate"),
                                "codec": audio_track.get("codec"),
                                "channels": audio_track.get("channels"),
                                "samplerate": audio_track.get("samplerate"),
                            },
                    }
                    if "thumbnail" in publishers:
                        stream_result["thumbnail"] = f"{self.base_thumbs}/{app}/{stream}/thumb.png"
                    result[f"{app}/{stream}"] = stream_result
                except Exception as e:
                    dbg.append(f"{app}/{stream} error: {str(e)}")

        return {"streams": result, "dbg": dbg}

    def create_ome_headers(self):
        return {"Authorization": f"Basic {base64.b64encode(self.ome_password).decode()}"}


API = OmeApi()


def application(environ, start_response):
    return API.handle(environ, start_response)
