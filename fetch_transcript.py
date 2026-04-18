
from youtube_transcript_api import YouTubeTranscriptApi
import sys

video_id = "3iWMzUXBsAk"
try:
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    full_transcript = " ".join([item['text'] for item in transcript_list])
    with open("output/transcript.txt", "w", encoding="utf-8") as f:
        f.write(full_transcript)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
