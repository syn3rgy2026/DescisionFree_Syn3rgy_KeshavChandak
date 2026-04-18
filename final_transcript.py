
from youtube_transcript_api import YouTubeTranscriptApi

video_id = '0-6ZIy9ebys'
try:
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)
    
    try:
        transcript = transcript_list.find_transcript(['en'])
    except:
        transcript = transcript_list[0]

    data = transcript.fetch()
    
    # Since it's a list of objects, let's try to get the text attribute
    texts = []
    for item in data:
        if hasattr(item, 'text'):
            texts.append(item.text)
        elif isinstance(item, dict):
            texts.append(item.get('text', ''))
        else:
            # Fallback: string representation
            texts.append(str(item))
            
    print(' '.join(texts))
except Exception as e:
    print(f"Error: {e}")
