FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all files from Github to Server
COPY . .

# Install normal requirements
RUN pip install --no-cache-dir -r requirements.txt

# Force update yt-dlp to latest pre-release to bypass youtube blocks
RUN pip install -U --pre yt-dlp

# Make sure downloads folder is there
RUN mkdir -p downloads

CMD ["python", "bot.py"]
