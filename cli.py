"""StegoCrypt komut satiri arayuzu."""

import argparse
import getpass
import sys

from core import crypto, stego
from core.exceptions import StegoCryptError
from utils import helpers


def _prompt_new_password() -> str:
    password = getpass.getpass("Parola: ")
    confirm = getpass.getpass("Parola (tekrar): ")
    if password != confirm:
        print("Hata: Parolalar eslesmiyor.", file=sys.stderr)
        sys.exit(1)
    return password


def encode_command(args: argparse.Namespace) -> None:
    if not args.output.lower().endswith(".png"):
        print(
            "Hata: --output dosyasi '.png' uzantili olmalidir (cikti her zaman PNG olarak yazilir).",
            file=sys.stderr,
        )
        sys.exit(1)

    message = args.message if args.message is not None else input("Gizlenecek mesaj: ")

    try:
        capacity = helpers.calculate_capacity(args.image)
    except StegoCryptError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        sys.exit(1)

    needed = crypto.encrypted_length(len(message.encode("utf-8")))
    if needed > capacity:
        print(
            f"Hata: Gorsel yetersiz kapasiteye sahip: sifrelenmis mesaj {needed} bayt, "
            f"gorsel en fazla {capacity} bayt tasiyabilir.",
            file=sys.stderr,
        )
        sys.exit(1)

    password = args.password if args.password is not None else _prompt_new_password()

    try:
        token = crypto.encrypt(message, password)
        stego.encode(args.image, token, args.output)
    except StegoCryptError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Mesaj '{args.output}' dosyasina gizlendi.")


def decode_command(args: argparse.Namespace) -> None:
    password = args.password if args.password is not None else getpass.getpass("Parola: ")

    try:
        token = stego.decode(args.image)
        message = crypto.decrypt(token, password)
    except StegoCryptError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        sys.exit(1)

    print(message)


def main() -> None:
    parser = argparse.ArgumentParser(prog="stegocrypt", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="Veriyi sifrele ve goruntuye gizle")
    encode_parser.add_argument("--image", required=True, help="Kaynak goruntu dosyasi")
    encode_parser.add_argument(
        "--message", help="Gizlenecek mesaj (verilmezse interaktif olarak sorulur)"
    )
    encode_parser.add_argument("--output", required=True, help="Cikti goruntu dosyasi")
    encode_parser.add_argument(
        "--password", help="AES-256 parolasi (verilmezse interaktif olarak sorulur ve dogrulama istenir)"
    )
    encode_parser.set_defaults(func=encode_command)

    decode_parser = subparsers.add_parser("decode", help="Goruntuden veriyi cikar ve sifresini coz")
    decode_parser.add_argument("--image", required=True, help="Sifreli veri iceren goruntu")
    decode_parser.add_argument(
        "--password", help="AES-256 parolasi (verilmezse interaktif olarak sorulur)"
    )
    decode_parser.set_defaults(func=decode_command)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:
        print(f"Beklenmeyen hata: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
