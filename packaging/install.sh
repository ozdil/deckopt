#!/usr/bin/env bash
# deckopt kurulum betigi. Yalnizca Steam Deck. Root gerektirmez.
set -euo pipefail

REPO="${DECKOPT_REPO:-ozdil/deckopt}"
BASE="https://github.com/${REPO}/releases/latest/download"
APP_DIR="$HOME/Applications/deckopt"
ASSET="deckopt-linux-x86_64.tar.gz"

die() { echo "HATA: $*" >&2; exit 1; }

product=$(tr '[:upper:]' '[:lower:]' < /sys/devices/virtual/dmi/id/product_name 2>/dev/null || true)
case "$product" in
  jupiter|galileo) ;;
  *) die "deckopt yalnizca Steam Deck uzerinde kurulabilir (tespit edilen: ${product:-bilinmiyor})." ;;
esac

[ "$(id -u)" -ne 0 ] || die "Bu betigi sudo ile calistirmayin."
command -v curl >/dev/null || die "curl bulunamadi."
command -v sha256sum >/dev/null || die "sha256sum bulunamadi."

tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT

echo "[1/4] Indiriliyor..."
curl -fsSL --proto '=https' --tlsv1.2 -o "$tmp/$ASSET" -- "$BASE/$ASSET"
curl -fsSL --proto '=https' --tlsv1.2 -o "$tmp/SHA256SUMS" -- "$BASE/SHA256SUMS"

echo "[2/4] Saglama toplami dogrulaniyor..."
(cd "$tmp" && grep -E "  ${ASSET}\$" SHA256SUMS | sha256sum -c --quiet -) || die "Saglama toplami uyusmuyor; kurulum iptal edildi."

echo "[3/4] Kuruluyor: $APP_DIR"
[ ! -L "$APP_DIR" ] || die "$APP_DIR sembolik baglanti; reddedildi."
mkdir -p "$tmp/x"
tar -xzf "$tmp/$ASSET" -C "$tmp/x" --no-same-owner
[ -f "$tmp/x/deckopt/deckopt.x86_64" ] || die "Paket icerigi beklenmedik."
rm -rf -- "$APP_DIR"
mkdir -p "$(dirname "$APP_DIR")"
mv "$tmp/x/deckopt" "$APP_DIR"
chmod 0755 "$APP_DIR/deckopt.x86_64"

echo "[4/4] Steam kutuphanesine ekleniyor..."
if command -v steamos-add-to-steam >/dev/null; then
  steamos-add-to-steam "$APP_DIR/deckopt.x86_64" || true
  echo "Steam'de onay penceresi acildiysa 'Ekle'ye basin."
else
  echo "Otomatik ekleme araci bulunamadi. Steam > Oyun Ekle > Steam Disi Oyun Ekle ile"
  echo "  $APP_DIR/deckopt.x86_64"
  echo "dosyasini secin."
fi

echo
echo "Kurulum tamamlandi. Game Mode'a donun; deckopt kutuphanenizde 'Steam Disi' altinda."
