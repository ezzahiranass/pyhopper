# Usage: powershell -File screenshot.ps1 <out.png> [scale]
param([string]$Out, [double]$Scale = 0.5)
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
$g.Dispose()
if ($Scale -ne 1) {
  $w = [int]($b.Width * $Scale); $h = [int]($b.Height * $Scale)
  $small = New-Object System.Drawing.Bitmap $w, $h
  $g2 = [System.Drawing.Graphics]::FromImage($small)
  $g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g2.DrawImage($bmp, 0, 0, $w, $h); $g2.Dispose()
  $small.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png); $small.Dispose()
} else { $bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png) }
$bmp.Dispose()
Write-Output "saved $Out ($($b.Width)x$($b.Height) @ $Scale)"
