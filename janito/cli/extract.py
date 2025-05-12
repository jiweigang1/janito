"""
Response extraction/normalization for janito CLI (shared).
"""
def extract_content(response):
    try:
        if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
            return response.choices[0].message.content
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        return part.text
                return str(response)
            else:
                return str(response)
        else:
            return str(response)
    except Exception:
        return str(response)
