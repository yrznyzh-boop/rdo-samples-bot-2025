# RDO Sample Distribution Bot

## What it does
- Reply to your own message with `توزيع` to start.
- Members reply to that original message with their ID.
- `قائمة` displays registered requests.
- `وقف توزيع` stops requests and publishes a report.
- Reply to a member's registered ID message with any number; the bot replies to that member's message that their turn arrived.

## FadeHost setup
1. Upload `main.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. Choose **Your own repository** in FadeHost and paste the repository URL.
3. Add environment variable `TELEGRAM_BOT_TOKEN` with your BotFather token (do not put it in GitHub).
4. Run command, if requested: `python main.py`.
5. Add the bot to your group as admin. In BotFather use `/setprivacy` then choose your bot and `Disable`.

## Optional genuine Telegram stickers
Set these environment variables to Telegram sticker file IDs:
`STICKER_START`, `STICKER_REQUEST`, `STICKER_TURN`, `STICKER_STOP`, `STICKER_LIST`.
If not set, the bot uses text/emoji fallbacks.

## Notes
This is a starter version. Back up `data.json` because free hosting may not preserve local files through redeployments. Never publish or share your bot token.
