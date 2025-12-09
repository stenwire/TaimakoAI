import re

def recursive_character_text_splitter(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:])
            break
            
        # Try to find a natural break point (newline, period, space)
        # Look back from 'end' to find the best split point
        split_point = -1
        for char in ['\n\n', '\n', '. ', ' ']:
            pos = text.rfind(char, start, end)
            if pos != -1:
                split_point = pos + len(char)
                break
        
        if split_point != -1:
            chunks.append(text[start:split_point])
            # Ensure we make progress to avoid infinite loops
            next_start = split_point - chunk_overlap
            if next_start <= start:
                next_start = start + 1
            start = next_start
        else:
            # Hard split if no natural break found
            chunks.append(text[start:end])
            start = end - chunk_overlap
            
    return chunks
