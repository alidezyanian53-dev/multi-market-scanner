import pandas as pd
import requests
import yfinance as yf

# تنظیمات ربات تلگرام
TELEGRAM_BOT_TOKEN = "9289658285:AAHf6dBjBaJjUYP3CjOsWIdJb0ZvqHzyG-c"
TELEGRAM_CHAT_ID = 5150997629

# لیست دارایی‌ها برای اسکن (فارکس، طلا، کریپتو)
MARKET_ASSETS = {
    "Gold (Commodity)": "GC=F",
    "EUR/USD (Forex)": "EURUSD=X",
    "Bitcoin (Crypto)": "BTC-USD",
    "Ethereum (Crypto)": "ETH-USD",
    "GBP/USD (Forex)": "GBPUSD=X",
}


def send_telegram_message(message):
  """ارسال پیام به تلگرام از طریق Bot API بدون نیاز به پروکسی روی سرور ابری"""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(url, json=payload, timeout=15)
    if response.status_code == 200:
      print("گزارش با موفقیت به تلگرام ارسال شد.")
    else:
      print(f"خطا در ارسال پیام به تلگرام: {response.text}")
  except Exception as e:
    print(f"خطا در اتصال به تلگرام: {e}")


def calculate_rsi(series, period=14):
  """محاسبه اندیکاتور RSI"""
  delta = series.diff()
  gain = delta.where(delta > 0, 0).rolling(window=period).mean()
  loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
  rs = gain / loss
  return 100 - (100 / (1 + rs))


def scan_markets():
  """اسکن و امتیازدهی به بازارها"""
  print("=" * 50)
  print("در حال اسکن بازارها...")
  print("=" * 50)

  results = []

  for asset_name, ticker in MARKET_ASSETS.items():
    try:
      df = yf.download(ticker, period="100d", interval="1d", progress=False)

      if df.empty or len(df) < 50:
        continue

      if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

      close_prices = df["Close"]
      current_price = close_prices.iloc[-1]

      # محاسبات تکنیکال
      ema_50 = close_prices.ewm(span=50, adjust=False).mean().iloc[-1]
      rsi_series = calculate_rsi(close_prices)
      current_rsi = rsi_series.iloc[-1]

      # موتور امتیازدهی
      score = 0
      signals = []

      if current_price > ema_50:
        score += 50
        signals.append("بالای میانگین (روند صعودی)")
      else:
        signals.append("پایین میانگین (روند نزولی)")

      if 50 <= current_rsi <= 70:
        score += 50
        signals.append(f"مومنتوم قوی (RSI: {current_rsi:.1f})")
      elif current_rsi > 70:
        score += 20
        signals.append(f"اشباع خرید (RSI: {current_rsi:.1f})")
      else:
        signals.append(f"مومنتوم ضعیف (RSI: {current_rsi:.1f})")

      results.append({
          "Asset": asset_name,
          "Price": round(current_price, 4),
          "Score": score,
          "Analysis": " | ".join(signals),
      })

    except Exception as e:
      print(f"خطا در پردازش {asset_name}: {e}")

  report_df = pd.DataFrame(results)
  if not report_df.empty:
    report_df = (
        report_df.sort_values(by="Score", ascending=False)
        .reset_index(drop=True)
    )

  return report_df


if __name__ == "__main__":
  # اجرای اسکنر
  report_df = scan_markets()

  if not report_df.empty:
    # فرمت‌بندی گزارش برای ارسال به تلگرام
    message_text = "🚨 *گزارش هوشمند اسکنر چندبازاری*\n\n"

    for idx, row in report_df.iterrows():
      message_text += (
          f"*{idx+1}. {row['Asset']}*\n"
          f"💰 قیمت: `{row['Price']}` | 🏆 امتیاز: `{row['Score']}`\n"
          f"📊 تحلیل: {row['Analysis']}\n"
          "-----------------------------------\n"
      )

    # ارسال گزارش نهایی به تلگرام
    send_telegram_message(message_text)
  else:
    print("هیچ داده‌ای برای گزارش‌دهی یافت نشد.")