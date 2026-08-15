"""StegoCrypt komut satiri arayuzu."""

import argparse

from core import crypto, stego
from utils import helpers


def encode_command(args: argparse.Namespace) -> None:
    raise NotImplementedError


def decode_command(args: argparse.Namespace) -> None:
    raise NotImplementedError


def main() -> None:
    parser = argparse.ArgumentParser(prog="stegocrypt", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="Veriyi sifrele ve goruntuye gizle")
    encode_parser.add_argument("--image", required=True, help="Kaynak goruntu dosyasi")
    encode_parser.add_argument("--message", required=True, help="Gizlenecek mesaj veya dosya")
    encode_parser.add_argument("--output", required=True, help="Cikti goruntu dosyasi")
    encode_parser.add_argument("--password", required=True, help="AES-256 parolasi")
    encode_parser.set_defaults(func=encode_command)

    decode_parser = subparsers.add_parser("decode", help="Goruntuden veriyi cikar ve sifresini coz")
    decode_parser.add_argument("--image", required=True, help="Sifreli veri iceren goruntu")
    decode_parser.add_argument("--password", required=True, help="AES-256 parolasi")
    decode_parser.set_defaults(func=decode_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
