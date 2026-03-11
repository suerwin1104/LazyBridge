import sys; import os; sys.path.append(os.getcwd())
from services.shield import redact_sensitive_data
text='Here is my Anthropic key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_abcdefghij'
print("REDACTED:", redact_sensitive_data(text))
