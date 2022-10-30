from api.ome import OmeApi
from auth.discordauth import DiscordAuth
from sprong import SprongController, mapping, json_endpoint, sprongbean, Request


def combine_dicts(*dicts):
    return {k: v for d in dicts for k, v in d.items()}


@sprongbean
class StreamsController(SprongController):
    def __init__(self, ome_config, ome_api: OmeApi, discord_auth: DiscordAuth):
        super().__init__()
        self.ome_api = ome_api
        self.discord_auth = discord_auth
        self.base_webrtc = ome_config["webRtcPublishUrl"]
        self.base_llhls = ome_config["llHlsPublishUrl"]
        self.base_thumbs = ome_config["thumbnailPublishUrl"]

    @mapping('^/v1/streams/?$')
    @json_endpoint
    def serve(self, req: Request, start_response):
        auth = self.discord_auth.authenticate(req)
        token_str = f"token={auth.testmerrie_token}"

        dbg = []
        result = {}

        def get_outputs(app, stream, publisher):
            return {
                "webrtc": {
                    # "webrtc-udp": f"{self.base_webrtc}/{app}/{stream}?{token_str}",
                    # "webrtc-tcp": f"{self.base_webrtc}/{app}/{stream}?transport=tcp&{token_str}",
                    "webrtc-udp": f"{self.base_webrtc}/{app}/{stream}/abr?{token_str}",
                    "webrtc-tcp": f"{self.base_webrtc}/{app}/{stream}/abr?transport=tcp&{token_str}",
                },
                "llhls": {"llhls": f"{self.base_llhls}/{app}/{stream}/llhls.m3u8?{token_str}"},
                "hls": {"hls": f"{self.base_llhls}/{app}/{stream}/playlist.m3u8?{token_str}"}
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
                        stream_result["thumbnail"] = f"{self.base_thumbs}/{app}/{stream}/thumb.png?{token_str}"
                    result[f"{app}/{stream}"] = stream_result
                except Exception as e:
                    dbg.append(f"{app}/{stream} error: {str(e)}")

        return {"streams": result, "dbg": dbg}
