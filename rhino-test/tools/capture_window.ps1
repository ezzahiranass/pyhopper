# Usage: powershell -File capture_window.ps1 -Out out.png [-TitleMatch "Rhinoceros"] [-Scale 0.6]
# Captures a top-level window by title substring using PrintWindow (works when the window is behind others).
param([string]$Out, [string]$TitleMatch = "Rhinoceros", [double]$Scale = 0.6, [switch]$ListOnly)
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text; using System.Collections.Generic;
public class W {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr h);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint f);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  public static List<string> Titles = new List<string>(); public static List<IntPtr> Handles = new List<IntPtr>();
  public static void Enum() { Titles.Clear(); Handles.Clear(); EnumWindows((h,l)=>{ if(!IsWindowVisible(h)) return true; int n=GetWindowTextLength(h); if(n==0) return true; var sb=new StringBuilder(n+1); GetWindowText(h,sb,n+1); uint pid; GetWindowThreadProcessId(h,out pid); Titles.Add(pid+"|"+sb.ToString()); Handles.Add(h); return true; }, IntPtr.Zero); }
}
"@
[W]::Enum()
if ($ListOnly) { [W]::Titles | ForEach-Object { $_ }; exit 0 }
$idx = -1
for ($i=0; $i -lt [W]::Titles.Count; $i++) { if ([W]::Titles[$i] -match $TitleMatch) { $idx = $i; break } }
if ($idx -lt 0) { Write-Output "no window matching '$TitleMatch'"; exit 1 }
$h = [W]::Handles[$idx]; $r = New-Object W+RECT; [void][W]::GetWindowRect($h, [ref]$r)
$w = $r.R - $r.L; $hh = $r.B - $r.T
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp); $dc = $g.GetHdc()
[void][W]::PrintWindow($h, $dc, 2)   # 2 = PW_RENDERFULLCONTENT
$g.ReleaseHdc($dc); $g.Dispose()
if ($Scale -ne 1) { $sw=[int]($w*$Scale); $sh=[int]($hh*$Scale); $s = New-Object System.Drawing.Bitmap $sw,$sh; $g2=[System.Drawing.Graphics]::FromImage($s); $g2.InterpolationMode='HighQualityBicubic'; $g2.DrawImage($bmp,0,0,$sw,$sh); $g2.Dispose(); $s.Save($Out,[System.Drawing.Imaging.ImageFormat]::Png); $s.Dispose() } else { $bmp.Save($Out,[System.Drawing.Imaging.ImageFormat]::Png) }
$bmp.Dispose()
Write-Output "captured '$([W]::Titles[$idx])' ${w}x${hh} -> $Out"
