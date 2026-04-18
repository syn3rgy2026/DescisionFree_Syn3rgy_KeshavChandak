
from youtube_transcript_api import YouTubeTranscriptApi

video_id = '9LO-bj1jyz4'
try:
    api = YouTubeTranscriptApi()
    try:
        data = api.fetch(video_id, languages=['hi'])
    except TypeError:
        data = api.fetch(video_id)
    
    # The error suggests 'data' is a list of objects, not dicts.
    # Let's try accessing .text attribute.
    texts = []
    for item in data:
        try:
            texts.append(item.text)
        except AttributeError:
            # Fallback to dict if some are dicts
            texts.append(item['text'])
            
    transcript_text = ' '.join(texts)
    with open('transcript.txt', 'w', encoding='utf-8') as f:
        f.write(transcript_text)
    print("Transcript successfully saved to transcript.txt")
except Exception as e:
    print(f"Error: {e}")
