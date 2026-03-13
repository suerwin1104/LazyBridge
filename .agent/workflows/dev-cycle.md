---
description: 自動化開發、測試與驗證循環 (Dev Cycle)
---

// turbo-all

## Development Cycle

1. Review the code changes and run any necessary scripts
2. Run `python -c "import bot.commands; import worker; print('✅ All modules OK')"` to verify imports
3. Run `python -m services.report_service` to generate the usage report
4. Run `python main.py` to start the bot
5. Check terminal output for errors and fix as needed
