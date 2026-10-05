#!/usr/bin/env bash
# deckopt kaldirma betigi. Profiller ve API anahtari istege bagli silinir.
set -euo pipefail

APP_DIR="$HOME/Applications/deckopt"
DATA_DIR="$HOME/.local/share/godot/app_userdata/deckopt"

[ "$(id -u)" -ne 0 ] || { echo "HATA: Bu betigi sudo ile calistirmayin." >&2; exit 1; }

FORCE_YES=0
for arg in "$@"; do
  if [ "$arg" = "-y" ] || [ "$arg" = "--yes" ]; then
    FORCE_YES=1
  fi
done

if [ -L "$APP_DIR" ]; then
  echo "HATA: $APP_DIR sembolik baglanti; reddedildi." >&2
  exit 1
fi
rm -rf -- "$APP_DIR"
echo "Uygulama silindi."

ans="h"
if [ "$FORCE_YES" -eq 1 ]; then
  ans="e"
elif [ -t 0 ]; then
  read -r -p "Profiller ve API anahtari da silinsin mi? [e/H] " ans
fi

if [ "${ans,,}" = "e" ] && [ ! -L "$DATA_DIR" ]; then
  rm -rf -- "$DATA_DIR"
  echo "Kullanici verileri silindi."
fi

echo "Steam kutuphanesindeki kisayolu: oyun > Yonet > Kisayolu kaldir ile silebilirsiniz."

