from prompt_toolkit.styles import Style

toolbar_style = Style([
    ("role",       "bg:#3887b8 #ffffff"), # distinct background for role
    ("model",      "bold #6fbf73"),
    ("msg_count",  "bold #a67007"),
    ("tokens_in",  "bold #407992"),
    ("tokens_out", "bold #b85873"),
    ("tokens_total","bold #bb8300"),
    ("session_id", "italic #999"),
])
