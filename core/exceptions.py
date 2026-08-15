"""StegoCrypt icin ozel exception siniflari."""


class StegoCryptError(Exception):
    """Taban hata sinifi."""


class CapacityError(StegoCryptError):
    """Gorsel, verinin tamamini gizlemek icin yeterli kapasiteye sahip degil."""


class DecryptionError(StegoCryptError):
    """Sifre cozme basarisiz (yanlis parola veya bozuk veri)."""
