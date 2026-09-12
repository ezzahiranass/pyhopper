# Usage: show_window.ps1 -Handle 856864 [-Cmd 5]   (5=SW_SHOW, 9=SW_RESTORE, 0=SW_HIDE)
param([int64]$Handle, [int]$Cmd = 5)
Add-Type -Name SW -Namespace U -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c); [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);'
[void][U.SW]::ShowWindow([IntPtr]$Handle, $Cmd); Write-Output ("ShowWindow({0},{1}) -> visible={2}" -f $Handle, $Cmd, [U.SW]::IsWindowVisible([IntPtr]$Handle))
