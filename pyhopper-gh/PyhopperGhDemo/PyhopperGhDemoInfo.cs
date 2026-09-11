using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace PyhopperGhDemo;

public sealed class PyhopperGhDemoInfo : GH_AssemblyInfo
{
    public override string Name => "Pyhopper GH Demo";
    public override Bitmap? Icon => null;
    public override string Description =>
        "Starter components demonstrating logging, custom canvas controls, context menus, and Eto UI.";
    public override Guid Id => new("8fd8e754-7cd7-4f86-b7b9-b872ef31420e");
    public override string AuthorName => "Pyhopper";
    public override string AuthorContact => "https://pyhopper.dev";
}
