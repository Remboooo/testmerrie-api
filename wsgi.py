import logging
import os

import yaml

from api.ome import OmeApi
from sprong import mapping, json_endpoint, Controller, SprongApplication
from util.singletonrepo import SingletonRepo

LOGGER = logging.getLogger()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def combine_dicts(*dicts):
    return {k: v for d in dicts for k, v in d.items()}


class LegacyApi(Controller):
    def __init__(self, repo: SingletonRepo):
        super().__init__()
        self.ome_api = repo.get(OmeApi)

    @mapping('^/?$')
    @json_endpoint
    def serve(self, env, start_response):
        r = self.ome_api.get("vhosts/default/apps/bam/streams")
        r2 = self.ome_api.get("vhosts/default/apps/app/streams")
        return [f"bam/{stream}" for stream in r] + ["app/twitch" for stream in r2]


class StreamsController(Controller):
    def __init__(self, ome_config, repo):
        super().__init__()
        self.ome_api = repo.get(OmeApi)
        self.base_webrtc = ome_config["webRtcPublishUrl"]
        self.base_llhls = ome_config["llHlsPublishUrl"]
        self.base_thumbs = ome_config["thumbnailPublishUrl"]

    @mapping('^/v1/streams/?$')
    @json_endpoint
    def serve(self, env, start_response):
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

        apps = self.ome_api.get("vhosts/default/apps")
        for app in apps:
            app_details = self.ome_api.get(f"vhosts/default/apps/{app}")
            publishers = list(app_details["publishers"].keys())
            streams = self.ome_api.get(f"vhosts/default/apps/{app}/streams")
            for stream in streams:
                try:
                    stream_details = self.ome_api.get(f"vhosts/default/apps/{app}/streams/{stream}")
                    video_track = [t for t in stream_details["input"]["tracks"] if "video" in t][0]["video"]
                    audio_track = [t for t in stream_details["input"]["tracks"] if "audio" in t][0]["audio"]
                    stream_result = {
                        "name": stream,
                        "streams": {
                            "main": {"protocols": combine_dicts(*(get_outputs(app, stream, p) for p in publishers))}},
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


class Bami(SprongApplication):
    def __init__(self):
        super().__init__()

        with open(os.path.join(SCRIPT_DIR, "config.yaml"), 'r') as f:
            self.config = yaml.safe_load(f)

        self.repo = SingletonRepo()
        ome_config = self.config["ovenMediaEngine"]
        self.ome_api = OmeApi(ome_config["apiUrl"], ome_config["apiPassword"])
        self.repo.register(self.ome_api)
        self.add_controller(LegacyApi(self.repo))
        self.add_controller(StreamsController(ome_config, self.repo))


application = Bami()

if __name__ == '__main__':
    print(application({"PATH_INFO": "/v1/streams"}, lambda *args: print(args)))
