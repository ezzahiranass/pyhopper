#!/bin/bash
# Capture the Rhino window (by title substring, default "Rhinoceros") and crop+upscale its command-history strip.
# usage: tools/readcmd.sh [TitleMatch] [out.png] [height_px]
T="${1:-Rhinoceros}"; OUT="${2:-$TEMP/rhino_cmdhist.png}"; H="${3:-90}"
D="$(cd "$(dirname "$0")" && pwd)"
powershell -NoProfile -ExecutionPolicy Bypass -File "$D/capture_window.ps1" -Out "$TEMP/_rh_full.png" -TitleMatch "$T" -Scale 1 >/dev/null || exit 1
powershell -NoProfile -Command "Add-Type -AssemblyName System.Drawing; \$s=[System.Drawing.Image]::FromFile(\"\$env:TEMP\_rh_full.png\"); \$w=[Math]::Min(950,\$s.Width); \$d=New-Object System.Drawing.Bitmap (\$w*2),($H*2); \$g=[System.Drawing.Graphics]::FromImage(\$d); \$g.InterpolationMode='HighQualityBicubic'; \$g.DrawImage(\$s,(New-Object System.Drawing.Rectangle 0,0,(\$w*2),($H*2)),(New-Object System.Drawing.Rectangle 0,38,\$w,$H),[System.Drawing.GraphicsUnit]::Pixel); \$g.Dispose(); \$d.Save('$OUT'); \$s.Dispose(); 'ok'" >/dev/null
echo "$OUT"
