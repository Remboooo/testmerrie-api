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
        self.base_hls = ome_config["hlsPublishUrl"]
        self.base_thumbs = ome_config["thumbnailPublishUrl"]

    @mapping('^/v1/streams/?$')
    @json_endpoint
    def serve(self, req: Request, start_response):
        auth = self.discord_auth.authenticate(req)
        token_str = f"token={auth.testmerrie_token}"

        dbg = []
        result = {}

        def get_outputs(app, stream, publisher, playlist):
            return {
                "webrtc": {
                    "webrtc-udp": f"{self.base_webrtc}/{app}/{stream}/{playlist['fileName']}?{token_str}",
                    "webrtc-tcp": f"{self.base_webrtc}/{app}/{stream}/{playlist['fileName']}?transport=tcp&{token_str}",
                },
                "llhls": {"llhls": f"{self.base_hls}/{app}/{stream}/{playlist['fileName']}.m3u8?{token_str}"},
            }.get(publisher, {})

        def get_streams(app, app_details, stream, stream_details, publishers):
            video_in_track = [t for t in stream_details["input"]["tracks"] if "video" in t][0]["video"]
            video_in_height = video_in_track["height"]
            result = {}
            for output in stream_details["outputs"]:
                name = output["name"]
                #video_out_heights = {t["name"]: t.get("video", {}).get("height", video_in_height) for t in output["tracks"] if "video" in t}
                for playlist in app_details["outputProfiles"]["outputProfile"][0]["playlists"]:
                    #video_heights = set(video_out_heights[rendition["video"]] for rendition in playlist["renditions"])
                    #name = f"{list(video_heights)[0]}p" if len(video_heights) == 1 else "abr"
                    result[playlist["name"]] = {}
                    for publisher in publishers:
                        # second param: stream name or output name?
                        result[playlist["name"]].update(get_outputs(app, stream, publisher, playlist))
            return result

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
                        "streams": get_streams(app, app_details, stream, stream_details, publishers),
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