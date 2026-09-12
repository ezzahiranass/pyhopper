using System;
using System.Drawing;
using System.Windows.Forms;
using Grasshopper.Kernel;
using PyhopperGhDemo.Ui;

namespace PyhopperGhDemo.Components;

public sealed class UiPlaygroundComponent : GH_Component
{
    public UiPlaygroundComponent()
        : base(
            "UI Playground",
            "UI",
            "Open an Eto dialog containing several common UI controls.",
            "Pyhopper",
            "Demo")
    {
    }

    public override Guid ComponentGuid => new("c4addc10-c8d9-482d-a5b3-76af29eca2dc");
    protected override Bitmap? Icon => null;

    protected override void RegisterInputParams(GH_InputParamManager parameters)
    {
    }

    protected override void RegisterOutputParams(GH_OutputParamManager parameters)
    {
        parameters.AddTextParameter("Instructions", "I", "How to open the UI.", GH_ParamAccess.item);
    }

    protected override void SolveInstance(IGH_DataAccess data)
    {
        data.SetData(0, "Right-click this component and choose “Open UI playground…”");
    }

    protected override void AppendAdditionalComponentMenuItems(ToolStripDropDown menu)
    {
        base.AppendAdditionalComponentMenuItems(menu);
        Menu_AppendSeparator(menu);
        Menu_AppendItem(menu, "Open UI playground…", (_, _) => PyhopperDemoDialog.ShowDialog());
    }
}
