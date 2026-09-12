using System;
using System.Collections.Generic;
using System.Drawing;
using Grasshopper.Kernel;
using Rhino;

namespace PyhopperGhDemo.Components;

public sealed class PrintMessageComponent : GH_Component
{
    public PrintMessageComponent()
        : base(
            "Print Message",
            "Print",
            "Print text to the Rhino command history and return repeated output lines.",
            "Pyhopper",
            "Demo")
    {
    }

    public override Guid ComponentGuid => new("81db336f-1457-41f3-87fb-b19c7024a47d");
    protected override Bitmap? Icon => null;

    protected override void RegisterInputParams(GH_InputParamManager parameters)
    {
        parameters.AddTextParameter("Text", "T", "Text to print.", GH_ParamAccess.item, "Hello from Pyhopper");
        parameters.AddIntegerParameter("Count", "C", "Number of lines to emit.", GH_ParamAccess.item, 1);
        parameters.AddBooleanParameter("Uppercase", "U", "Convert the text to uppercase.", GH_ParamAccess.item, false);
    }

    protected override void RegisterOutputParams(GH_OutputParamManager parameters)
    {
        parameters.AddTextParameter("Lines", "L", "Generated output lines.", GH_ParamAccess.list);
        parameters.AddIntegerParameter("Length", "N", "Length of the transformed text.", GH_ParamAccess.item);
    }

    protected override void SolveInstance(IGH_DataAccess data)
    {
        var text = "Hello from Pyhopper";
        var count = 1;
        var uppercase = false;

        if (!data.GetData(0, ref text) || !data.GetData(1, ref count) || !data.GetData(2, ref uppercase))
            return;

        count = Math.Max(0, count);
        if (count > 100)
        {
            AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "Count was limited to 100.");
            count = 100;
        }

        var transformed = uppercase ? text.ToUpperInvariant() : text;
        var lines = new List<string>(count);
        for (var index = 0; index < count; index++)
            lines.Add($"{index + 1}: {transformed}");

        RhinoApp.WriteLine($"[Pyhopper GH Demo] {transformed} ({count} line(s))");
        Message = $"{count} line{(count == 1 ? string.Empty : "s")}";

        data.SetDataList(0, lines);
        data.SetData(1, transformed.Length);
    }
}
