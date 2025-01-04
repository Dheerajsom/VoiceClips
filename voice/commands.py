import re

def parse_command(command):
    if command.startswith("clip"):
        match = re.match(r"clip\s+(\d+)?", command)
        if match:
            seconds = match.group(1)
            return ("clip_custom", int(seconds)) if seconds else ("clip", 30)
    return None, None
