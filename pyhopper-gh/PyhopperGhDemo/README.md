# Pyhopper GH Demo

A production-shaped starter Grasshopper plugin for Rhino 8.

## Included Components

- **Print Message**: standard inputs/outputs, runtime warnings, component message, and Rhino command-line logging.
- **Interactive Card**: custom-rendered canvas button and toggle, undo support, outputs, and context-menu actions.
- **UI Playground**: opens an Eto dialog containing text input, dropdown, checkbox, slider, progress bar, log area, message box, and buttons.

All components appear under `Pyhopper > Demo`.

## Prerequisites

- Rhino 8
- Visual Studio 2022 with the `.NET desktop development` workload, or the .NET 8 SDK
- Grasshopper, included with Rhino

The project targets `.NET Framework 4.8` and references the Rhino 8 assemblies installed under:

```text
C:\Program Files\Rhino 8\System
C:\Program Files\Rhino 8\Plug-ins\Grasshopper
```

Override `RhinoSystemDir` or `GrasshopperDir` when building if Rhino is installed elsewhere.

## Build

From PowerShell:

```powershell
cd D:\Apps\pyhopper\pyhopper-gh\PyhopperGhDemo
.\build.ps1
```

Or open `PyhopperGhDemo.csproj` in Visual Studio and build it.

The output is:

```text
bin\Debug\net48\PyhopperGhDemo.gha
```

## Install

Close Rhino, then run:

```powershell
.\install.ps1
```

Or build and install together:

```powershell
.\build-and-install.ps1
```

The installer copies the plugin to:

```text
%APPDATA%\Grasshopper\Libraries\PyhopperGhDemo\PyhopperGhDemo.gha
```

Restart Rhino, run `Grasshopper`, then find the components under `Pyhopper > Demo`.

If Windows blocks the plugin, right-click the `.gha`, open **Properties**, and select **Unblock**. The install script already calls `Unblock-File`.

## Run

1. Open Rhino 8.
2. Run the `Grasshopper` command.
3. Open the `Pyhopper` tab and `Demo` panel.
4. Place **Print Message**, connect inputs, and inspect Rhino's command history.
5. Place **Interactive Card**, click its custom button/toggle, and right-click it for more actions.
6. Place **UI Playground**, right-click it, and choose **Open UI playground…**.

## Debug

Open the project in Visual Studio, attach the debugger to `Rhino.exe`, set breakpoints, and then interact with the components in Grasshopper. After rebuilding, restart Rhino before loading the changed `.gha`.
