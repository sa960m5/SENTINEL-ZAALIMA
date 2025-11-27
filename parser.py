import re

# Matches Apache/Nginx style logs like:
# 10.0.0.45 - - [26/Nov/2025:13:08:12] "POST /login HTTP/1.1" 302
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) - - \[(?P<timestamp>[^\]]+)\] "(?P<method>[A-Z]+) (?P<url>[^\s]+)[^"]*" (?P<status>\d{3})'
)

def parse_log_line(line: str):
    match = LOG_PATTERN.search(line)
    if match:
        return match.groupdict()
    else:
        print(f"[WARN] Could not parse line: {line.strip()}")
        return None
