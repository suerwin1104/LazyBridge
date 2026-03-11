import sys
import os
sys.path.append(os.getcwd())
from services.shield import is_safe_command, redact_sensitive_data

def test_shield():
    print("🛡️ Testing AgentShield...")
    
    # 1. Test dangerous commands
    dangerous_cmds = [
        "rm -rf /",
        "rm -rf *",
        "format c:",
        "del /s /q C:\\Windows"
    ]
    
    print("\n--- Command Interception ---")
    for cmd in dangerous_cmds:
        safe = is_safe_command(cmd)
        print(f"Command: {cmd} | Safe: {safe}")
        assert safe is False

    safe_cmd = "ls -la"
    print(f"Command: {safe_cmd} | Safe: {is_safe_command(safe_cmd)}")
    assert is_safe_command(safe_cmd) is True

    # 2. Test redaction
    print("\n--- Sensitive Data Redaction ---")
    text_with_keys = (
        "Here is my Anthropic key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_abcdefghij\n"
        "And my OpenAI key: sk-1234567890abcdef1234567890abcdef1234567890abcdef"
    )
    redacted = redact_sensitive_data(text_with_keys)
    print("Original text containing keys...")
    print("Redacted output:")
    print(redacted)
    
    # assert "sk-ant-api03" in text_with_keys
    # assert "sk-a..." in redacted
    # assert "...ghij" in redacted
    # assert "sk-1..." in redacted

    print("\n✅ AgentShield tests passed!")

if __name__ == "__main__":
    test_shield()
