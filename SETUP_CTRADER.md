# cTrader FIX API সেটআপ গাইড (Bengali)

## ধাপ ১: cTrader এ FIX API পাসওয়ার্ড সেট করুন

1. cTrader ওপেন করুন
2. Settings → FIX API → Change Password এ যান
3. একটি নতুন পাসওয়ার্ড সেট করুন (শুধু ইংরেজি অক্ষর ও নম্বর ব্যবহার করুন)
4. পাসওয়ার্ডটি মনে রাখুন

## ধাপ ২: .env ফাইল কনফিগার করুন

`.env` ফাইল খুলে আপনার পাসওয়ার্ড বসান:

```
FIX_PASSWORD=আপনার_পাসওয়ার্ড
```

**গুরুত্বপূর্ণ:** পাসওয়ার্ডে `#` থাকলে কোটেশন ব্যবহার করুন:
```
FIX_PASSWORD="আমার_পাস#123"
```

## ধাপ ৩: বট চালু করুন

```bash
cd AtikulBank
python3 live_gate.py
```

## TUI ড্যাশবোর্ড

বট চালু হলে একটি TUI ড্যাশবোর্ড দেখাবে যেখানে:
- লাইভ প্রাইস দেখা যাবে
- ট্রেড সিগন্ল দেখা যাবে
- পজিশন সাইজ দেখা যাবে
- রিস্ক ম্যানেজার স্ট্যাটাস দেখা যাবে

## FIX API কানেকশন স্ট্যাটাস

```
[CONNECT] Attempting connection to demo-uk-eqx-01.p.c-trader.com:5222...
[CONNECT] TCP connected to demo-uk-eqx-01.p.c-trader.com:5222
[CONNECT] SSL handshake completed
[LOGON] Sending logon message...
[LOGON] Login successful!
```

## ট্রেডিং শুরু করুন

বট স্বয়ংক্রিয়ভাবে:
1. মার্কেট ডেটা সংগ্রহ করবে
2. 84টি মডেল দিয়ে বিশ্লেষণ করবে
3. সিগন্ল জেনারেট করবে
4. রিস্ক ম্যানেজার দিয়ে যাচাই করবে
5. ট্রেড এক্সিকিউট করবে

## সমস্যা সমাধান

### "FIX_PASSWORD not set" এরর
- `.env` ফাইলে `FIX_PASSWORD` সেট করুন

### "Connection failed" এরর
- ইন্টারনেট সংযোগ চেক করুন
- cTrader সার্ভার স্ট্যাটাস চেক করুন

### "Login failed" এরর
- পাসওয়ার্ড সঠিক আছে কিনা চেক করুন
- পাসওয়ার্ডে ইংরেজি অক্ষর ও নম্বর ব্যবহার করুন

## ডেমো অ্যাকাউন্ট

ডেমো অ্যাকাউন্টে টেস্ট করতে:
```
FIX_HOST=demo-uk-eqx-01.p.c-trader.com
SENDER_COMP_ID=demo.ctrader.5832984
```

## লাইভ অ্যাকাউন্ট

লাইভ অ্যাকাউন্টে ট্রেড করতে `.env` ফাইলে পরিবর্তন করুন:
```
FIX_HOST=live-uk-eqx-01.p.c-trader.com
SENDER_COMP_ID=live.ctrader.YOUR_ACCOUNT_ID
```

## সাহায্য প্রয়োজন?

- cTrader FIX API ডকুমেন্টেশন: https://connect.ctrader.com/apps/fix-api
- সমস্যা হলে লগ ফাইল চেক করুন
