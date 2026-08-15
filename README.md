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
│   └── helpers.py       # Binary-String donusumleri, dogrulama, resim format kontrolu (planlanan)
├── tests/                # Birim testler
│   ├── test_crypto.py
│   └── test_stego.py
├── examples/
│   ├── images/           # Ornek kaynak gorseller
│   └── output/           # Uretilen cikti gorselleri
├── docs/                 # Dokumantasyon
├── main.py               # Giris noktasi (cli.main() cagirir)
├── cli.py                # Terminalden komut satiri ile kullanim (argparse; encode/decode planlanan)
├── requirements.txt      # Gerekli kutuphaneler (Pillow, cryptography, numpy, pytest)
└── README.md
```

## Durum

- ✅ `core/crypto.py` — AES-256-CBC sifreleme, PBKDF2HMAC ile anahtar turetme, Encrypt-then-MAC (HMAC-SHA256) dogrulama
- ✅ `core/stego.py` — LSB tabanli encode/decode, 32-bit uzunluk basligi, kapasite kontrolu
- 🚧 `utils/helpers.py` — bit/byte donusumleri ve format dogrulama fonksiyonlari henuz uygulanmadi
- 🚧 `cli.py` — `encode`/`decode` komutlari henuz `core` ve `utils` modullerine baglanmadi

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Kullanim (planlanan)

```bash
python main.py encode --image kaynak.png --message "gizli mesaj" --output cikti.png --password "guclu-parola"
python main.py decode --image cikti.png --password "guclu-parola"
```

## Test

```bash
pytest
```
