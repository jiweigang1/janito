from prompt_toolkit.styles import Style

toolbar_style = Style.from_dict({
    'role': 'bg:#a83265 #ffffff', # updated distinct background for role
    'model': 'bold #6fbf73',
    'msg_count': 'bold #a67007',
    'tokens_in': 'bold #407992',
    'tokens_out': 'bold #b85873',
    'tokens_total': 'bold #bb8300',
    'session_id': 'italic #999',
    'prompt': 'bg:#2323af #ffffff bold', # prompt text
    'input': 'bg:#191970 #fafafa',   # input style legacy, just in case
    'input-field': 'bg:#444400 #ffffff', # <-- ACTUAL input area
})
