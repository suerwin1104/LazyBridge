# AgentShield Security Rules

To ensure the safety and integrity of the system, all agent actions must adhere to these security rules.

## 1. Command Execution

- **Strict Blocklist**: Never execute commands that can cause recursive deletion, system formatting, or mass permission changes (e.g., `rm -rf /`, `mkfs`, `chmod -R 777` on sensitive dirs).
- **Least Privilege**: Always prefer specific file operations over broad wildcards.
- **Interactive Prompts**: Avoid commands that require interactive user input, as they may hang the worker.

## 2. Data Protection

- **API Key Redaction**: Never output raw API keys (Anthropic, OpenAI, Gemini, etc.) to logs or Discord. Any string matching `sk-ant-`, `sk-`, or `AIza` should be carefully handled.
- **Sensitive Files**: Prevent reading `/etc/shadow`, `.env` (unless absolutely necessary for the task), or SSH private keys.

## 3. Network Safety

- **Untrusted Downloads**: Do not download and execute scripts from unknown or untrusted URLs.
- **Data Exfiltration**: Monitor for unusual outgoing network requests that might indicate data exfiltration.

## 4. Hook Enforcement

- Use `ECC_HOOK_PROFILE=strict` when performing high-risk operations to ensure maximum auditing.
