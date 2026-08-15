# StegoCrypt

LSB (Least Significant Bit) steganografi ile AES-256 sifrelemeyi birlestiren bir Python araci. Bir mesaj/dosya once AES-256 ile sifrelenir, ardindan sifreli veri bir gorsele piksel bitleri seviyesinde gizlenir.

## Proje Yapisi

```
StegoCrypt/
├── core/
│   ├── __init__.py
│   ├── crypto.py        # AES-256 sifreleme ve anahtar turetme fonksiyonlari
│   ├── stego.py         # LSB algoritmasi, bit manipulasyonu, encode/decode
│   └── exceptions.py    # Ozel exception siniflari
├── utils/
│   ├── __init__.py
│   └── helpers.py       # Binary-String donusumleri, dogrulama, resim format kontrolu
├── tests/                # Birim testler
│   ├── test_crypto.py
│   └── test_stego.py
├── examples/
│   ├── images/           # Ornek kaynak gorseller
│   └── output/           # Uretilen cikti gorselleri
├── docs/                 # Dokumantasyon
├── main.py               # Giris noktasi (cli.main() cagirir)
├── cli.py                # Terminalden komut satiri ile kullanim (argparse)
├── requirements.txt      # Gerekli kutuphaneler (Pillow, cryptography, numpy, pytest)
└── README.md
```

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
