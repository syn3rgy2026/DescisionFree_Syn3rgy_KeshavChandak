
from youtube_transcript_api import YouTubeTranscriptApi

video_id = '0-6ZIy9ebys'

def try_call(name, func, *args):
    try:
        print(f"Trying {name}...")
        return func(*args)
    except Exception as e:
        print(f"Failed {name}: {e}")
        return None

# Try static
res1 = try_call("Static get_transcript", getattr(YouTubeTranscriptApi, 'get_transcript', None), video_id)
res2 = try_call("Static list", getattr(YouTubeTranscriptApi, 'list', None), video_id)

# Try instance
try:
    api = YouTubeTranscriptApi()
    res3 = try_call("Instance get_transcript", getattr(api, 'get_transcript', None), video_id)
    res4 = try_call("Instance list", getattr(api, 'list', None), video_id)
except Exception as e:
    print(f"Instantiation failed: {e}")

if res1:
    print("Success with res1")
    print(' '.join([i['text'] for i in res1]))
elif res2:
    print("Success with res2")
    # res2 is likely a TranscriptList, we need to fetch
    try:
        t = res2.find_transcript(['en'])
        print(' '.join([i['text'] for i in t.fetch()]))
    except Exception as e:
        print(f"Fetch failed: {e}")
elif res3:
    print("Success with res3")
    print(' '.join([i['text'] for i in res3]))
elif res4:
    print("Success with res4")
    try:
        t = res4.find_transcript(['en'])
        print(' '.join([i['text'] for i in t.fetch()]))
    except Exception as e:
        print(f"Fetch failed: {e}")
