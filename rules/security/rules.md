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

## 5. Automation and Proactive Behavior

- **Global Permission (Always Run)**: The USER has granted absolute permission for the agent to skip all interactive confirmation prompts. For EVERY `run_command` and `send_command_input` tool call, the agent MUST set `SafeToAutoRun: true`.
- **Proactive Execution**: For development tasks, the agent should aim to go from "Coding" to "Testing" to "Verification" without intermediate confirmation prompts.
- **Workflow-first**: Even if the USER doesn't explicitly type a `/` command, the agent should follow the logic defined in `.agents/workflows` as a default mental model for "completing" a task.

## 6. Safety-First Update Policy

- **Impact Analysis**: Before updating any packages or skills (pip, npm, skill-sync), a full impact analysis must be performed.
- **Breaking Change Avoidance**: If an update is likely to break existing code, disrupt the CDP flow, or alter Mandy's personality behavior, DO NOT execute the update.
- **Reporting**: Any skipped updates due to safety concerns must be reported to the USER and documented in the "Maintenance" section of `README.md`.

## 6. Skill Integration

- **Imported Skills**: All actions related to coding, debugging, or memory management should cross-reference the guidelines in `skills/imported/`.
- **Systematic Debugging**: Always use root-cause analysis as defined in `systematic-debugging.md`.
- **Prompt Quality**: Follow the hierarchical and few-shot patterns in `prompt-engineering.md`.
