using Eto.Drawing;
using Eto.Forms;
using Rhino;

namespace PyhopperGhDemo.Ui;

internal sealed class PyhopperDemoDialog : Dialog
{
    private readonly TextArea _log;

    private PyhopperDemoDialog()
    {
        Title = "Pyhopper GH Demo · UI Playground";
        ClientSize = new Size(520, 430);
        Resizable = true;
        Padding = 12;

        var name = new TextBox { PlaceholderText = "Type a message" };
        var mode = new DropDown
        {
            DataStore = new[] { "Development", "Staging", "Production" },
            SelectedIndex = 0,
        };
        var enabled = new CheckBox { Text = "Enable live synchronization", Checked = true };
        var slider = new Slider { MinValue = 0, MaxValue = 100, Value = 35 };
        var progress = new ProgressBar { MinValue = 0, MaxValue = 100, Value = slider.Value };
        _log = new TextArea { ReadOnly = true, Height = 130 };

        slider.ValueChanged += (_, _) => progress.Value = slider.Value;

        var printButton = new Button { Text = "Print to Rhino" };
        printButton.Click += (_, _) =>
        {
            var message = string.IsNullOrWhiteSpace(name.Text) ? "Hello from the Eto dialog" : name.Text;
            var line = $"[{mode.SelectedValue}] {message} · enabled={enabled.Checked} · value={slider.Value}";
            RhinoApp.WriteLine($"[Pyhopper GH Demo] {line}");
            _log.Append(line + System.Environment.NewLine, true);
        };

        var messageButton = new Button { Text = "Show Message" };
        messageButton.Click += (_, _) => MessageBox.Show(
            this,
            "This is an Eto message box opened by a Grasshopper plugin.",
            "Pyhopper GH Demo",
            MessageBoxButtons.OK,
            MessageBoxType.Information);

        var closeButton = new Button { Text = "Close" };
        closeButton.Click += (_, _) => Close();
        DefaultButton = printButton;
        AbortButton = closeButton;

        var layout = new DynamicLayout { Spacing = new Size(8, 8) };
        layout.AddRow(new Label { Text = "Message" }, name);
        layout.AddRow(new Label { Text = "Environment" }, mode);
        layout.AddRow(enabled);
        layout.AddRow(new Label { Text = "Progress" }, slider);
        layout.AddRow(progress);
        layout.AddRow(new Label { Text = "Event log" });
        layout.AddRow(_log);
        layout.AddSeparateRow(printButton, messageButton, null, closeButton);
        Content = layout;
    }

    internal static void ShowDialog()
    {
        using var dialog = new PyhopperDemoDialog();
        dialog.ShowModal();
    }
}
