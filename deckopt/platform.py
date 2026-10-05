"""Steam Deck donanim ve platform dogrulama modulu."""
import os
import sys
from pathlib import Path

from .store import read_limited

# Steam Deck DMI product_name degerleri:
# LCD: Jupiter
# OLED: Galileo
STEAM_DECK_PRODUCTS = {"jupiter", "galileo"}


def get_product_name() -> str:
    path = Path("/sys/devices/virtual/dmi/id/product_name")
    if not path.exists():
        return ""
    try:
        return read_limited(path).strip().lower()
    except Exception:
        return ""


def is_steamos() -> bool:
    os_rel = Path("/etc/os-release")
    if not os_rel.exists():
        return False
    try:
        content = read_limited(os_rel).lower()
        return "steamos" in content or 'id="steamos"' in content
    except Exception:
        return False


def is_steam_deck() -> bool:
    prod = get_product_name()
    if prod in STEAM_DECK_PRODUCTS:
        return True
    # Test veya override amaciyla zorlama bayragi (sadece gelistirici testi icin)
    if os.environ.get("DECKOPT_ALLOW_ANY_DEVICE") == "1":
        return True
    return False


def enforce_steam_deck():
    """Yazilimin yalnizca Steam Deck uzerinde calismasini zorunlu kilar."""
    if not is_steam_deck():
        sys.exit(
            "HATA: Bu yazilim yalnizca Valve Steam Deck (LCD/OLED) uzerinde calisacak sekilde tasarlanmistir.\n"
            f"Tespit edilen donanim: {get_product_name() or 'Bilinmiyor'}\n"
            "Islem durduruldu."
        )
