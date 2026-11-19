#!/usr/bin/env bash
# Build + install the Clonk Goblin VST3 (and AU) on macOS with Camomile.
#
#   ./build_mac.sh /path/to/unzipped/Camomile
#
# Get Camomile from https://github.com/pierreguillot/Camomile/releases
# (use v1.0.8-beta10 or newer for native Apple Silicon / M-series support).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CAMO="${1:-}"
if [[ -z "$CAMO" || ! -d "$CAMO" ]]; then
  echo "usage: $0 /path/to/Camomile-folder   (the folder that contains the 'camomile' script)"
  exit 1
fi
CAMO="$(cd "$CAMO" && pwd)"
OUT="$HERE/build"
rm -rf "$OUT" && mkdir -p "$OUT"

echo "==> clearing quarantine on the Camomile download"
xattr -dr com.apple.quarantine "$CAMO" 2>/dev/null || true

echo "==> generating plugins with Camomile"
SCRIPT=""
for s in camomile Camomile camomile.sh; do
  [[ -f "$CAMO/$s" ]] && SCRIPT="$s" && break
done
if [[ -z "$SCRIPT" ]]; then
  echo "!! could not find the 'camomile' script in $CAMO"
  echo "   Manual route: see README.md -> 'Manual Camomile build'"
  exit 1
fi
chmod +x "$CAMO/$SCRIPT"
( cd "$CAMO" && "./$SCRIPT" -f "$HERE/ClonkGoblin" -o "$OUT" )

VST3="$(find "$OUT" -maxdepth 3 -name 'ClonkGoblin.vst3' -print -quit)"
AU="$(find "$OUT" -maxdepth 3 -name 'ClonkGoblin.component' -print -quit)"
[[ -n "$VST3" ]] || { echo "!! no ClonkGoblin.vst3 produced - check the Camomile output above"; exit 1; }

echo "==> installing"
DEST_VST3="$HOME/Library/Audio/Plug-Ins/VST3"
DEST_AU="$HOME/Library/Audio/Plug-Ins/Components"
mkdir -p "$DEST_VST3" "$DEST_AU"
rm -rf "$DEST_VST3/ClonkGoblin.vst3"
cp -R "$VST3" "$DEST_VST3/"
if [[ -n "$AU" ]]; then
  rm -rf "$DEST_AU/ClonkGoblin.component"
  cp -R "$AU" "$DEST_AU/"
fi

for b in "$DEST_VST3/ClonkGoblin.vst3" ${AU:+"$DEST_AU/ClonkGoblin.component"}; do
  echo "==> un-quarantine + ad-hoc sign: $b"
  xattr -dr com.apple.quarantine "$b" 2>/dev/null || true
  codesign --force --deep --sign - "$b"
  BIN="$(find "$b/Contents/MacOS" -type f -perm -u+x -print -quit 2>/dev/null || true)"
  if [[ -n "$BIN" ]]; then
    ARCHS="$(lipo -archs "$BIN" 2>/dev/null || echo unknown)"
    echo "    architectures: $ARCHS"
    if [[ "$ARCHS" != *arm64* ]]; then
      echo "    !! not arm64: this Camomile build is Intel-only. Use Camomile v1.0.8-beta10+"
      echo "       or run your DAW under Rosetta (or use the plugdata route in README.md)."
    fi
  fi
done

if [[ -n "$AU" ]]; then
  killall -9 AudioComponentRegistrar 2>/dev/null || true   # make Logic re-scan AUs
fi
echo
echo "Done! Rescan plugins in your DAW and look for 'ClonkGoblin' (instrument)."
echo "The goblin is waiting."
