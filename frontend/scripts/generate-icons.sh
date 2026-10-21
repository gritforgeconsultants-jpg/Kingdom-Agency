#!/bin/bash
# Generate PNG icons from SVG for PWA manifest.
# Requires: rsvg-convert (librsvg2-bin) or Inkscape.
# Run from the frontend directory: bash scripts/generate-icons.sh

SIZES="72 96 128 144 152 192 384 512"
SVG="public/icons/icon.svg"
OUT="public/icons"

for size in $SIZES; do
  echo "Generating ${size}x${size}..."
  if command -v rsvg-convert &> /dev/null; then
    rsvg-convert -w "$size" -h "$size" "$SVG" > "${OUT}/icon-${size}.png"
  elif command -v inkscape &> /dev/null; then
    inkscape "$SVG" -w "$size" -h "$size" -o "${OUT}/icon-${size}.png"
  elif command -v convert &> /dev/null; then
    convert -background none -resize "${size}x${size}" "$SVG" "${OUT}/icon-${size}.png"
  else
    echo "No SVG converter found. Install librsvg2-bin, inkscape, or imagemagick."
    exit 1
  fi
done

echo "Done. Icons in ${OUT}/"
