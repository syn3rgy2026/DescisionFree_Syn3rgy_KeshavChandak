"""
transcript_tool.py
------------------
Tool to extract and clean transcripts from YouTube videos.
"""
import os
import re
import urllib.parse
from smolagents import tool

@tool
def extract_youtube_transcript(url: str, save_to_file: bool = False) -> str:
    """
    Extracts the transcript from a YouTube video URL, cleans it into readable paragraphs, 
    and optionally saves it to a file.

    Args:
        url: A valid YouTube video URL.
        save_to_file: If True, saves the output to a text file in the output/ directory.

    Returns:
        Structured string containing the Title and Transcript.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    except ImportError:
        return "Error: youtube-transcript-api is not installed. Please install it using: pip install youtube-transcript-api"

    # 1. Extract Video ID
    video_id = None
    if "v=" in url:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if "v" in query_params:
            video_id = query_params["v"][0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        
    if not video_id:
        return "Error: Invalid YouTube URL provided. Could not extract Video ID."

    # 2. Extract Title (Optional enhancement via simple HTML scraping)
    title = f"Video_{video_id}"
    try:
        import requests
        res = requests.get(url, timeout=5)
        title_match = re.search(r'<title>(.*?)</title>', res.text)
        if title_match:
            title = title_match.group(1).replace(" - YouTube", "").strip()
    except Exception:
        pass

    # 3. Retrieve Transcript
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find English first
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except Exception:
                # Fallback to anything available (most relevant if multiple)
                transcript = next(iter(transcript_list))
                
        transcript_data = transcript.fetch()
        
    except TranscriptsDisabled:
        return "Error: Transcript not available for this video (Captions are disabled)."
    except NoTranscriptFound:
        return "Error: No suitable transcript format could be found for this video."
    except Exception as e:
        return f"Error: Failed to retrieve transcript. Details: {str(e)}"

    if not transcript_data:
        return "Error: Transcript is empty."

    # 4. Clean and Format Transcript
    # Remove newlines, weird spaces, and group into readable paragraphs
    text_chunks = [re.sub(r'\s+', ' ', item['text']).strip() for item in transcript_data]
    
    formatted_transcript = ""
    current_paragraph = []
    word_count = 0
    
    for chunk in text_chunks:
        # Check against pure music / sound tags for cleaner reading
        if re.fullmatch(r'\[.*?\]', chunk):
            continue
            
        current_paragraph.append(chunk)
        word_count += len(chunk.split())
        
        # Create a new paragraph after roughly 80 words if it ends with punctuation
        if word_count > 80 and chunk and chunk[-1] in ".!?":
            formatted_transcript += " ".join(current_paragraph) + "\n\n"
            current_paragraph = []
            word_count = 0
            
    if current_paragraph:
        formatted_transcript += " ".join(current_paragraph) + "\n"

    # Check if empty after cleaning
    formatted_transcript = formatted_transcript.strip()
    if not formatted_transcript:
        return "Error: Transcript is empty after cleaning."

    final_output = f"Title: {title}\n\nTranscript:\n{formatted_transcript}"

    # 5. Save to file if requested
    if save_to_file:
        output_folder = "output"
        os.makedirs(output_folder, exist_ok=True)
        
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)[:50]
        filename = f"{safe_title}.txt"
        file_path = os.path.join(output_folder, filename)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_output)
            final_output += f"\n\n[Success: Transcript saved to {os.path.abspath(file_path)}]"
        except Exception as e:
            final_output += f"\n\n[Warning: Failed to save file. Details: {str(e)}]"

    return final_output

ALL_TOOLS = [
    extract_youtube_transcript
]
