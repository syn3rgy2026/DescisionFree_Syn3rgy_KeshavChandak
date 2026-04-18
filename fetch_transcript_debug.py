
from youtube_transcript_api import YouTubeTranscriptApi
import sys

print("Available attributes of YouTubeTranscriptApi:")
print(dir(YouTubeTranscriptApi))

video_id = "3iWMzUXBsAk"
try:
    # Attempting the standard method again with a check
    if hasattr(YouTubeTranscriptApi, 'get_transcript'):
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([item['text'] for item in transcript_list])
        with open("output/transcript.txt", "w", encoding="utf-8") as f:
            f.write(full_transcript)
        print("Success")
    else:
        print("Error: get_transcript method not found in YouTubeTranscriptApi")
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
