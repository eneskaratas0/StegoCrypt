# StegoCrypt

LSB (Least Significant Bit) steganografi ile AES-256 sifrelemeyi birlestiren bir Python araci. Bir mesaj/dosya once AES-256 ile sifrelenir, ardindan sifreli veri bir gorsele piksel bitleri seviyesinde gizlenir.

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
├── tests/                # Birim testler
│   ├── test_crypto.py
│   ├── test_stego.py
│   ├── test_helpers.py
│   └── test_cli.py
├── examples/
│   ├── images/           # Ornek kaynak gorseller
│   └── output/           # Uretilen cikti gorselleri
├── docs/                 # Dokumantasyon
├── main.py               # Giris noktasi (cli.main() cagirir)
├── cli.py                # Terminalden komut satiri ile kullanim (argparse; tamamlandi)
├── requirements.txt      # Gerekli kutuphaneler (Pillow, cryptography, numpy, pytest)
└── README.md
```

## Durum

- ✅ `core/crypto.py` — AES-256-CBC sifreleme, PBKDF2HMAC ile anahtar turetme, Encrypt-then-MAC (HMAC-SHA256) dogrulama
- ✅ `core/stego.py` — LSB tabanli encode/decode, 32-bit uzunluk basligi, kapasite kontrolu
- ✅ `utils/helpers.py` — `calculate_capacity`, gorselin tasiyabilecegi azami veri miktarini hesaplar
- ✅ `cli.py` — `encode`/`decode` komutlari `core` ve `utils` modullerine bagli; parola/mesaj verilmezse interaktif sorulur

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

## Test

```bash
pytest
```
