import wsgiref.util
import requests
import base64
import json

OME_API_BASE = "http://127.0.0.1:48081"
AUTH_HEADER = {"Authorization": f"Basic {base64.b64encode(b'juanbetaler74382947823932fyssfdghr87').decode()}"}
PUBLISH_BASE = "bam.bad-bit.net/ome"

def application(environ, start_response):
    try:
        path = environ['PATH_INFO']
        if path.endswith('/'):
            path = path[:-1]
        
        start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8')])
        if path == '/v1/streams':
            result = get_streams()
        elif path == '':
            result = old_api()
        else:
            result = path 

        return json.dumps(result).encode('utf-8')
    except Exception as e:
        start_response('500 oops', [('Content-Type', 'application/json; charset=utf-8')])
        return json.dumps({"message": str(e)}).encode('utf-8')

def ome_get(path):
    return requests.get(f"{OME_API_BASE}/v1/{path}", headers=AUTH_HEADER).json().get('response')


def old_api():
    r = ome_get("vhosts/default/apps/bam/streams")
    r2 = ome_get("vhosts/default/apps/app/streams")
    return [f"bam/{stream}" for stream in r] + ["app/twitch" for stream in r2]


def combine_dicts(*dicts):
    return {k: v for d in dicts for k, v in d.items()}


def get_streams():
    dbg = []
    result = {}

    def get_outputs(app, stream, publisher):
        return {
                "webrtc": {
                    "webrtc-udp": f"wss://{PUBLISH_BASE}/{app}/{stream}",
                    "webrtc-tcp": f"wss://{PUBLISH_BASE}/{app}/{stream}?transport=tcp",
                },
                "llhls": {"llhls": f"https://{PUBLISH_BASE}/{app}/{stream}/llhls.m3u8"}
        }.get(publisher, {})

    apps = ome_get("vhosts/default/apps")
    for app in apps:
        app_details = ome_get(f"vhosts/default/apps/{app}")
        publishers = list(app_details["publishers"].keys())
        streams = ome_get(f"vhosts/default/apps/{app}/streams")
        for stream in streams:
            try:
                stream_details = ome_get(f"vhosts/default/apps/{app}/streams/{stream}")
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
                    stream_result["thumbnail"] = f"https://{PUBLISH_BASE}/{app}/{stream}/thumb.png"
                result[f"{app}/{stream}"] = stream_result
            except Exception as e:
                dbg.append(f"{app}/{stream} error: {str(e)}")

    return {"streams": result, "dbg": dbg}

