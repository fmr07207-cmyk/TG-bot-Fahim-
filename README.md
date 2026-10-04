# NEXORAX Telegram Panel — Safe Mock/Test Build

## Included
- Telegram inline-keyboard user menu
- Super-admin ID from environment variable
- Multi-admin add/remove
- Required-channel join verification ON/OFF
- Admin channel add/remove
- Notice and broadcast
- Mock test number, mock SMS event and test ranges
- Test-event leaderboard and wallet balance
- Withdrawal requests with admin approve/reject
- SQLite database and Render persistent disk configuration
- Referral link generation and referrer capture (commission payout is not enabled)

## Important limitations
This build intentionally does NOT connect to the supplied live number/OTP API and
does not collect or forward real third-party verification codes. The provider is
mock-only and uses placeholder numbers/test codes.
Telegram bots do not receive a user's IP address, so IP-based duplicate-account
approval cannot be reliably implemented by a Telegram bot alone.
This is a starter deployment build, not a regulated payment processor.

## Deploy from Android
1. Extract this ZIP.
2. Upload the contents of this folder to a new GitHub repository.
3. In Render, choose New + > Blueprint and connect the repository.
4. Render reads `render.yaml`; set `BOT_TOKEN` to a NEW token from BotFather.
5. Deploy. Open Logs and confirm the worker starts.
6. Open the bot and send `/start`.

## Admin
Super Admin ID is configured as `6882165252` in render.yaml.
Use `/admin` for the admin keyboard.
Commands:
- `/addadmin USER_ID`
- `/deladmin USER_ID`
- `/addchannel @channel Title https://t.me/channel`
- `/delchannel @channel`
- `/notice Your notice`
- `/broadcast Your message`
- `/approve WITHDRAWAL_ID`
- `/reject WITHDRAWAL_ID`

Make the bot an administrator in each required channel so membership checks work.

## Security
The previously shared bot token and API key should be revoked and replaced.
Never upload `.env`, bot tokens, or API keys to GitHub. Keep secrets in Render
Environment Variables.
