from flask import Flask
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7 successfully!"

# دالة لتشغيل السكربت أو البوت الخاص بك في الخلفية
def run_my_script():
    while True:
        print("Script is running...")
        # ضع هنا كود السكربت أو البوت الخاص بك
        time.sleep(60) # ينتظر دقيقة بين كل دورة

if __name__ == '__main__':
    # بدء السكربت في خيط منفصل بالتوازي مع السيرفر
    t = threading.Thread(target=run_my_script)
    t.daemon = True
    t.start()

    # تشغيل سيرفر الويب على بورت 10000 (المخصص في Render)
    app.run(host='0.0.0.0', port=10000)
