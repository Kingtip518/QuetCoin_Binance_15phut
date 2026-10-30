# Báo về Telegram các đồng coin tăng mạnh trên Binance (giao ngay, cặp USDT)
# GitHub tự chạy tệp này mỗi 15 phút (xem tệp .github/workflows/thongbao.yml)

import json, os, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

# ====== TÚ CHỈNH Ở ĐÂY ======
MUC_TANG = 10          # chỉ báo đồng tăng trên mức này (%) trong 24 giờ
SO_DONG_TOP = 5        # mỗi tin nhắn kèm danh sách bao nhiêu đồng tăng mạnh nhất
BAO_LAI_SAU_GIO = 24   # một đồng đã báo rồi thì sau bao nhiêu giờ mới báo lại
# ============================

TOKEN = os.environ["TELEGRAM_TOKEN"]      # lấy từ mục bí mật của kho GitHub, không ghi trong mã
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TEP_DA_BAO = "da_bao.json"                # ghi nhớ đồng nào đã báo để không báo trùng
GIO_VN = timezone(timedelta(hours=7))

def lay_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def lay_du_lieu():
    loi = None
    for may in ("https://data-api.binance.vision", "https://api.binance.com"):
        try:
            return lay_json(may + "/api/v3/ticker/24hr")
        except Exception as e:
            loi = e
    raise loi

def gui_telegram(noi_dung):
    du_lieu = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": noi_dung, "parse_mode": "HTML",
                                      "disable_web_page_preview": "true"}).encode()
    urllib.request.urlopen("https://api.telegram.org/bot" + TOKEN + "/sendMessage", du_lieu, timeout=30)

def so_tien(v):
    return f"{v/1e9:.2f} tỷ" if v >= 1e9 else f"{v/1e6:.1f} triệu"

def main():
    bay_gio = time.time()
    try:
        da_bao = json.load(open(TEP_DA_BAO, encoding="utf-8"))
    except Exception:
        da_bao = {}
    # bỏ các đồng đã quá thời gian chờ báo lại
    da_bao = {ma: t for ma, t in da_bao.items() if bay_gio - t < BAO_LAI_SAU_GIO * 3600}

    tk = lay_du_lieu()
    ds = [t for t in tk
          if t["symbol"].endswith("USDT")
          and bay_gio * 1000 - t["closeTime"] < 3600e3            # bỏ mã đã ngừng giao dịch
          and float(t["priceChangePercent"]) > MUC_TANG]
    ds.sort(key=lambda t: float(t["priceChangePercent"]), reverse=True)

    moi = [t for t in ds if t["symbol"] not in da_bao]
    if not moi:
        print(f"Có {len(ds)} đồng trên {MUC_TANG}%, không có đồng mới, không gửi tin.")
        json.dump(da_bao, open(TEP_DA_BAO, "w", encoding="utf-8"))
        return

    def dong(t, so_thu_tu=None):
        ma = t["symbol"][:-4]
        gia, dinh = float(t["lastPrice"]), float(t["highPrice"])
        dau = f"{so_thu_tu}. " if so_thu_tu else "• "
        return (f'{dau}<a href="https://www.binance.com/vi/trade/{ma}_USDT?type=spot"><b>{ma}</b></a> '
                f'+{float(t["priceChangePercent"]):.1f}%  |  giá {gia:g}  |  cách đỉnh {((gia-dinh)/dinh*100):.1f}%  |  '
                f'giao dịch {so_tien(float(t["quoteVolume"]))} USDT')

    gio = datetime.now(GIO_VN).strftime("%H:%M %d/%m")
    tin = [f"🚀 <b>Coin tăng trên {MUC_TANG}% trong 24 giờ</b> ({gio})", "",
           "<b>Mới vượt mức:</b>"] + [dong(t) for t in moi]
    tin += ["", f"<b>Tăng mạnh nhất hiện tại:</b>"] + [dong(t, i + 1) for i, t in enumerate(ds[:SO_DONG_TOP])]
    gui_telegram("\n".join(tin))
    print("Đã gửi:", ", ".join(t["symbol"] for t in moi))

    for t in moi:
        da_bao[t["symbol"]] = bay_gio
    json.dump(da_bao, open(TEP_DA_BAO, "w", encoding="utf-8"))

if __name__ == "__main__":
    main()
