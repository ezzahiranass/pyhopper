# Usage: close_window.ps1 -TitleMatch "Rhino Options" [-Pid 33380]   -> posts WM_CLOSE to matching visible top-level window(s)
param([string]$TitleMatch, [int]$OwnerPid = 0)
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text; using System.Collections.Generic;
public class WC {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  public static int Close(string match, int pid) { int n=0; EnumWindows((h,l)=>{ if(!IsWindowVisible(h)) return true; var sb=new StringBuilder(512); GetWindowText(h,sb,512); uint p; GetWindowThreadProcessId(h,out p); if(sb.ToString().Contains(match) && (pid==0 || p==pid)) { PostMessage(h,0x0010,IntPtr.Zero,IntPtr.Zero); n++; } return true; }, IntPtr.Zero); return n; }
}
"@
Write-Output ("closed {0} window(s) matching '{1}'" -f [WC]::Close($TitleMatch, $OwnerPid), $TitleMatch)
