"""StegoCrypt icin ozel exception siniflari."""


class StegoCryptError(Exception):
    """Taban hata sinifi."""


class CapacityError(StegoCryptError):
    """Gorsel, verinin tamamini gizlemek icin yeterli kapasiteye sahip degil."""


class DecryptionError(StegoCryptError):
    """Sifre cozme basarisiz (yanlis parola veya bozuk veri)."""


class StegoDataError(StegoCryptError):
    """Gorselde gecerli bir gizli veri bulunamadi (bozuk veya eksik LSB baslik)."""
