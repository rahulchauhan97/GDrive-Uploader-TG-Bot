# Deployment Guide for Optimized Google Drive Bot

## Prerequisites

1. **Python 3.8+** installed
2. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
3. **Telegram API credentials** from [my.telegram.org](https://my.telegram.org)
4. **Google Drive API credentials** from [Google Cloud Console](https://console.cloud.google.com)
5. **PostgreSQL database** (can use free Heroku Postgres)

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the example file and fill in your credentials:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```bash
# Required: Get from @BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Required: Get from my.telegram.org/apps
APP_ID=1234567
API_HASH=abcdefghijklmnopqrstuvwxyz123456

# Required: Your PostgreSQL database URL
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Required: Get from Google Cloud Console
GDRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your-client-secret
```

### 3. Set Environment Variables
#### For Linux/macOS:
```bash
export $(cat .env | xargs)
```

#### For Windows:
```cmd
set BOT_TOKEN=your_token_here
set APP_ID=your_app_id
rem ... (set all variables)
```

### 4. Run the Bot
```bash
python bot.py
```

## Docker Deployment (Recommended)

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

### 2. Build and Run
```bash
# Build image
docker build -t gdrive-bot .

# Run with environment file
docker run --env-file .env gdrive-bot
```

## Heroku Deployment

### 1. Create Heroku App
```bash
heroku create your-bot-name
```

### 2. Set Environment Variables
```bash
heroku config:set BOT_TOKEN=your_token
heroku config:set APP_ID=your_app_id
heroku config:set API_HASH=your_api_hash
heroku config:set GDRIVE_CLIENT_ID=your_client_id
heroku config:set GDRIVE_CLIENT_SECRET=your_client_secret
```

### 3. Add PostgreSQL Addon
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

### 4. Deploy
```bash
git add .
git commit -m "Deploy optimized bot"
git push heroku main
```

## Security Notes

⚠️ **Important**: Never commit your `.env` file or expose your credentials!

- Add `.env` to your `.gitignore`
- Use environment variables in production
- Regularly rotate your API keys
- Monitor your Google Drive API usage

## Troubleshooting

### Common Issues

1. **"Environment variable required" error**
   - Ensure all required variables are set
   - Check for typos in variable names

2. **Database connection errors**
   - Verify DATABASE_URL format
   - Ensure database is accessible

3. **Google Drive authentication fails**
   - Check GDRIVE_CLIENT_ID and GDRIVE_CLIENT_SECRET
   - Verify Google Drive API is enabled

### Logs and Monitoring

The bot will show detailed error messages. For production, consider:
- Using structured logging
- Setting up error monitoring (Sentry)
- Implementing health checks

## Performance Tips

- Use SSD storage for better file I/O
- Consider using Redis for caching
- Monitor memory usage for large files
- Set up horizontal scaling if needed