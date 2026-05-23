FROM python:3.10-slim

# စနစ်အတွက် လိုအပ်သော ffmpeg ကိုပါ တစ်ခါတည်း သွင်းပေးခြင်း (ဗီဒီယို ကွန်ဗတ်လုပ်ရန်)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
