import time
import json
import urllib.request
import subprocess

TOKEN = "8280934172:AAHhKIf_laLcBuw2m0jGqsorO-okztez3Es"
CHAT_ID = "1908525665"
BUILD_ID = "6703c46b-065c-4546-8e35-d4bcc844ed13"

def send_telegram(text, qr_url=None):
    if qr_url:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        data = json.dumps({"chat_id": CHAT_ID, "photo": qr_url, "caption": text, "parse_mode": "HTML"}).encode('utf-8')
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)

print("Watcher started for build:", BUILD_ID)
while True:
    try:
        cmd = ["npx", "eas-cli@latest", "build:list", "--platform", "android", "--limit", "1", "--json", "--non-interactive"]
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=r"C:\Users\sanat\Desktop\Солнышко\Vela\mobile")
        if res.returncode == 0:
            builds = json.loads(res.stdout)
            if builds and len(builds) > 0:
                b = builds[0]
                status = b.get("status")
                print(f"Current build status: {status}")
                if status == "finished":
                    apk_url = b.get("artifacts", {}).get("buildUrl")
                    if apk_url:
                        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={urllib.parse.quote(apk_url)}"
                        msg = (
                            "🎉 <b>ПОЛНАЯ ВЕРСИЯ VELA ГОТОВА!</b>\n\n"
                            "📱 <b>Все 4 экрана на месте:</b>\n"
                            "1️⃣ <b>Home:</b> Live-лента, баланс месяца, 50/30/20 и NFC перехват\n"
                            "2️⃣ <b>Analytics:</b> Net Surplus, сейфы-накопления (Vaults) и стратегия долгов\n"
                            "3️⃣ <b>AI Advisor:</b> Мульти-агенты и советы по тратам\n"
                            "4️⃣ <b>Academy:</b> Daily Bite, страйки и квизы\n\n"
                            f"📲 <b>Скачать APK:</b> <a href=\"{apk_url}\"><b>НАЖМИ ДЛЯ СКАЧИВАНИЯ</b></a>\n\n"
                            "Устанавливай и пользуйся! 🚀✨"
                        )
                        send_telegram(msg, qr)
                        print("Telegram notification sent successfully!")
                        break
                elif status == "errored" or status == "canceled":
                    send_telegram(f"⚠️ <b>Билд завершился со статусом: {status}</b>\nПроверь логи: https://expo.dev/accounts/dizbalanser/projects/vela-advisor/builds/{BUILD_ID}")
                    break
    except Exception as e:
        print("Error in watcher:", e)
    time.sleep(20)
