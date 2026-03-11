import re
from core.config import log

# Regex for sensitive patterns (API Keys)
SENSITIVE_PATTERNS = [
    r"sk-ant-api03-[a-zA-Z0-9\-_]{90,100}", # Anthropic
    r"sk-[a-zA-Z0-9]{48}",                 # OpenAI
    r"AIzaSy[a-zA-Z0-9\-_]{33}",           # Gemini (Google Cloud API Key)
    r"xox[baprs]-[0-9a-zA-Z\-]{10,48}"    # Slack (Example)
]

# Blocklist for dangerous commands
DANGEROUS_COMMANDS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"mkfs",
    r"format\s+[a-z]:",
    r"del\s+/s\s+/q",
    r"rd\s+/s\s+/q\s+c:\\",
    r"chmod\s+-R\s+777",
    r"chown\s+-R"
]

def is_safe_command(command: str) -> bool:
    """Checks if a shell command is safe to execute."""
    for pattern in DANGEROUS_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            log(f"🚨 [AgentShield] Dangerous command intercepted: {command}")
            return False
    return True

def redact_sensitive_data(text: str) -> str:
    """Redacts API keys and other sensitive data from a string."""
    redacted_text = text
    for pattern in SENSITIVE_PATTERNS:
        matches = re.findall(pattern, redacted_text)
        for match in matches:
            # Keep first 4 and last 4 characters
            placeholder = f"{match[:4]}...{match[-4:]}"
            redacted_text = redacted_text.replace(match, placeholder)
            log(f"🛡️ [AgentShield] Redacted sensitive data pattern.")
    return redacted_text
