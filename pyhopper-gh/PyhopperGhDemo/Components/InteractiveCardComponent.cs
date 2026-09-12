using System;
using System.Drawing;
using System.Windows.Forms;
using Grasshopper.GUI;
using Grasshopper.GUI.Canvas;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Attributes;
using Rhino;
using PyhopperGhDemo.Ui;

namespace PyhopperGhDemo.Components;

public sealed class InteractiveCardComponent : GH_Component
{
    internal bool IsEnabled { get; private set; } = true;
    internal int ClickCount { get; private set; }

    public InteractiveCardComponent()
        : base(
            "Interactive Card",
            "Card",
            "Custom canvas button and toggle with additional context-menu actions.",
            "Pyhopper",
            "Demo")
    {
    }

    public override Guid ComponentGuid => new("82f15ffd-e3ea-4716-9201-cff88112105c");
    protected override Bitmap? Icon => null;

    public override void CreateAttributes()
    {
        m_attributes = new InteractiveCardAttributes(this);
    }

    protected override void RegisterInputParams(GH_InputParamManager parameters)
    {
    }

    protected override void RegisterOutputParams(GH_OutputParamManager parameters)
    {
        parameters.AddTextParameter("Status", "S", "Current interactive-card status.", GH_ParamAccess.item);
        parameters.AddIntegerParameter("Clicks", "C", "Number of canvas-button clicks.", GH_ParamAccess.item);
        parameters.AddBooleanParameter("Enabled", "E", "Current toggle state.", GH_ParamAccess.item);
    }

    protected override void SolveInstance(IGH_DataAccess data)
    {
        data.SetData(0, IsEnabled ? "Interactive card is enabled" : "Interactive card is disabled");
        data.SetData(1, ClickCount);
        data.SetData(2, IsEnabled);
        Message = IsEnabled ? $"On · {ClickCount}" : $"Off · {ClickCount}";
    }

    internal void RegisterCanvasClick()
    {
        RecordUndoEvent("Click interactive card");
        ClickCount++;
        RhinoApp.WriteLine($"[Pyhopper GH Demo] Interactive card clicked {ClickCount} time(s).");
        ExpireSolution(true);
    }

    internal void ToggleEnabled()
    {
        RecordUndoEvent("Toggle interactive card");
        IsEnabled = !IsEnabled;
        RhinoApp.WriteLine($"[Pyhopper GH Demo] Interactive card enabled: {IsEnabled}");
        ExpireSolution(true);
    }

    internal void ResetClicks()
    {
        RecordUndoEvent("Reset interactive card");
        ClickCount = 0;
        ExpireSolution(true);
    }

    protected override void AppendAdditionalComponentMenuItems(ToolStripDropDown menu)
    {
        base.AppendAdditionalComponentMenuItems(menu);
        Menu_AppendSeparator(menu);
        Menu_AppendItem(menu, "Open UI playground…", (_, _) => PyhopperDemoDialog.ShowDialog());
        Menu_AppendItem(menu, "Reset click count", (_, _) => ResetClicks(), true, ClickCount == 0);
        Menu_AppendItem(menu, "Enabled", (_, _) => ToggleEnabled(), true, IsEnabled);
    }
}

internal sealed class InteractiveCardAttributes : GH_ComponentAttributes
{
    private RectangleF _buttonBounds;
    private RectangleF _toggleBounds;

    private InteractiveCardComponent Component => (InteractiveCardComponent)Owner;

    public InteractiveCardAttributes(InteractiveCardComponent owner)
        : base(owner)
    {
    }

    protected override void Layout()
    {
        base.Layout();
        var bounds = Bounds;
        bounds.Height += 54f;
        Bounds = bounds;

        _buttonBounds = new RectangleF(bounds.X + 6f, bounds.Bottom - 48f, bounds.Width - 12f, 20f);
        _toggleBounds = new RectangleF(bounds.X + 6f, bounds.Bottom - 24f, bounds.Width - 12f, 18f);
    }

    protected override void Render(GH_Canvas canvas, Graphics graphics, GH_CanvasChannel channel)
    {
        base.Render(canvas, graphics, channel);
        if (channel != GH_CanvasChannel.Objects)
            return;

        using (var button = GH_Capsule.CreateTextCapsule(
                   _buttonBounds,
                   _buttonBounds,
                   GH_Palette.Black,
                   $"Click me ({Component.ClickCount})",
                   2,
                   0))
        {
            button.Render(graphics, Selected, Owner.Locked, false);
        }

        using (var toggle = GH_Capsule.CreateTextCapsule(
                   _toggleBounds,
                   _toggleBounds,
                   Component.IsEnabled ? GH_Palette.Normal : GH_Palette.Hidden,
                   Component.IsEnabled ? "Enabled" : "Disabled",
                   2,
                   0))
        {
            toggle.Render(graphics, Selected, Owner.Locked, false);
        }
    }

    public override GH_ObjectResponse RespondToMouseDown(GH_Canvas sender, GH_CanvasMouseEvent e)
    {
        if (e.Button == MouseButtons.Left && _buttonBounds.Contains(e.CanvasLocation))
        {
            Component.RegisterCanvasClick();
            return GH_ObjectResponse.Handled;
        }

        if (e.Button == MouseButtons.Left && _toggleBounds.Contains(e.CanvasLocation))
        {
            Component.ToggleEnabled();
            return GH_ObjectResponse.Handled;
        }

        return base.RespondToMouseDown(sender, e);
    }
}
