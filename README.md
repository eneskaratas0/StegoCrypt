# StegoCrypt

LSB (Least Significant Bit) steganografi ile AES-256 sifrelemeyi birlestiren bir Python araci. Bir mesaj/dosya once AES-256 ile sifrelenir, ardindan sifreli veri bir gorsele piksel bitleri seviyesinde gizlenir. Hem komut satirindan hem de tarayici uzerinden bir web arayuzuyle kullanilabilir.

## Proje Yapisi

```
StegoCrypt/
├── core/
│   ├── __init__.py
│   ├── crypto.py        # AES-256-CBC + HMAC-SHA256 sifreleme ve PBKDF2 anahtar turetme (tamamlandi)
│   ├── stego.py         # LSB algoritmasi, bit manipulasyonu, encode/decode (tamamlandi)
│   └── exceptions.py    # Ozel exception siniflari (CapacityError, DecryptionError, StegoDataError)
├── utils/
│   ├── __init__.py
│   └── helpers.py       # Gorsel kapasite hesaplama (tamamlandi)
├── api/
│   ├── __init__.py
│   ├── app.py            # FastAPI uygulamasi: hata yakalayicilar, statik frontend sunumu
│   └── routes.py         # /api/capacity, /api/encode, /api/decode uc noktalari
├── frontend/
│   ├── index.html         # Tek sayfa web arayuzu (Sifrele & Gizle / Cikar & Coz)
│   ├── tailwind.config.js # Onceden derlenmis Tailwind CSS icin yapilandirma
│   ├── tailwind-src.css   # Tailwind derleme girdisi
│   └── static/
│       ├── app.js         # Arayuz mantigi (fetch cagrilari, dogrulama, onizleme)
│       └── app.css        # Onceden derlenmis Tailwind CSS ciktisi (repoya dahil)
├── tests/                # Birim testler
│   ├── test_crypto.py
│   ├── test_stego.py
│   ├── test_helpers.py
│   └── test_cli.py
├── examples/
│   ├── images/           # Ornek kaynak gorseller
│   └── output/           # Uretilen cikti gorselleri
├── docs/                 # Dokumantasyon
├── main.py               # CLI giris noktasi (cli.main() cagirir)
├── cli.py                # Terminalden komut satiri ile kullanim (argparse; tamamlandi)
├── run_server.py         # Web arayuzu giris noktasi (uvicorn ile api.app:app calistirir)
├── requirements.txt      # Gerekli kutuphaneler (Pillow, cryptography, numpy, pytest, fastapi, uvicorn, python-multipart)
└── README.md
```

## Durum

- ✅ `core/crypto.py` — AES-256-CBC sifreleme, PBKDF2HMAC ile anahtar turetme, Encrypt-then-MAC (HMAC-SHA256) dogrulama
- ✅ `core/stego.py` — LSB tabanli encode/decode, 32-bit uzunluk basligi, kapasite kontrolu
- ✅ `utils/helpers.py` — `calculate_capacity`, gorselin tasiyabilecegi azami veri miktarini hesaplar
- ✅ `cli.py` — `encode`/`decode` komutlari `core` ve `utils` modullerine bagli; parola/mesaj verilmezse interaktif sorulur
- ✅ `api/` — `core`/`utils` uzerine FastAPI katmani; goruntuler/parolalar/mesajlar sadece bellekte islenir, diske veya loga yazilmaz
- ✅ `frontend/` — CLI'dan bagimsiz, vanilla HTML/JS tek sayfa web arayuzu (build adimi/Node gerekmez)

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Kullanim

Parola ve mesaj CLI argumani olarak verilmezse interaktif olarak (parola ekrana yazilmadan) sorulur — bu, parolanin islem listesinde veya kabuk gecmisinde duz metin olarak kalmasini onler:

```bash
python main.py encode --image examples/images/sample_cover.png --output examples/output/cikti.png
# Gizlenecek mesaj: ...
# Parola: (gizli girilir)
# Parola (tekrar): (gizli girilir)

python main.py decode --image examples/output/cikti.png
# Parola: (gizli girilir)
```

Betikleme/otomasyon icin `--message` ve `--password` dogrudan da verilebilir (bu durumda duz metin olarak sizma riski kullanicinin sorumlulugundadir):

```bash
python main.py encode --image examples/images/sample_cover.png --message "gizli mesaj" --output examples/output/cikti.png --password "guclu-parola"
python main.py decode --image examples/output/cikti.png --password "guclu-parola"
```

`examples/images/sample_cover.png` (256x256, rastgele piksellerden uretilmis) yaklasik 24 KB'a kadar mesaj tasiyabilir; kendi kapak gorselinizi kullanmak icin herhangi bir Pillow'un acabildigi formati (`--image`) verebilirsiniz.

Notlar:
- `--output` her zaman `.png` uzantili olmalidir (cikti her zaman kayipsiz PNG olarak yazilir).
- Kapak gorselinin tasiyamayacagi kadar uzun bir mesaj verilirse, PBKDF2 anahtar turetmesi (600k iterasyon) hic calistirilmadan erken ve acik bir hata verilir.

## Web Arayuzu

CLI'a alternatif olarak, ayni islevi tarayicidan sunan bir web arayuzu de mevcuttur (`cli.py`/`main.py`'dan tamamen bagimsiz, ikisi birlikte kullanilabilir):

```bash
python run_server.py
# http://127.0.0.1:8000 adresini tarayicida acin
```

- **Sifrele & Gizle** sekmesi: kapak gorseli yuklenir (kapasite anlik hesaplanir), mesaj yazilir (bayt sayaci sifrelenmis boyutu da gosterir), parola girilip onaylanir; sonuc PNG hem indirilir hem onizlenir.
- **Cikar & Coz** sekmesi: stego goruntu ve parola ile gizli mesaj cikarilip goruntulenir.
- Goruntuler, parolalar ve mesajlar yalnizca istek sirasinda bellekte islenir; sunucu hicbir seyi diske veya loga yazmaz.
- Arayuz derleme adimi gerektirmeyen duz HTML/JS'tir; Tailwind CSS onceden derlenip `frontend/static/app.css` olarak repoya dahil edilmistir (runtime'da CDN script'i calismaz). `frontend/index.html` veya `frontend/static/app.js`'e yeni bir Tailwind sinifi eklenirse yeniden derlemek gerekir:
  ```bash
  # https://github.com/tailwindlabs/tailwindcss/releases adresinden Node/npm gerektirmeyen
  # standalone CLI'yi indirin (ör. tailwindcss-windows-x64.exe), sonra:
  tailwindcss.exe -i frontend/tailwind-src.css -o frontend/static/app.css --config frontend/tailwind.config.js --minify
  ```

## Test

```bash
pytest
```
