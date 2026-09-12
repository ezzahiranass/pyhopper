"""Rhino 8 Grasshopper Python 3 component demo.

Inputs:
    message: Text, item access
    count: Integer, item access
    show_ui: Boolean, item access

Outputs:
    lines: Text, list access
    points: Point, list access
    status: Text, item access
"""

import System
import Eto.Drawing as drawing
import Eto.Forms as forms
import Grasshopper.Kernel as ghk
import Rhino
import Rhino.Geometry as rg


def show_demo_dialog(initial_message, initial_count):
    dialog = forms.Dialog()
    dialog.Title = "Pyhopper Python Demo"
    dialog.ClientSize = drawing.Size(440, 300)
    dialog.Padding = drawing.Padding(12)
    dialog.Resizable = True

    message_box = forms.TextBox(Text=initial_message)
    count_slider = forms.Slider(MinValue=1, MaxValue=20, Value=initial_count)
    enabled_box = forms.CheckBox(Text="Enable output", Checked=True)
    progress = forms.ProgressBar(MinValue=1, MaxValue=20, Value=initial_count)
    log = forms.TextArea(ReadOnly=True, Height=100)

    def slider_changed(sender, event):
        progress.Value = count_slider.Value

    def print_clicked(sender, event):
        line = "{} | count={} | enabled={}".format(
            message_box.Text,
            count_slider.Value,
            enabled_box.Checked,
        )
        Rhino.RhinoApp.WriteLine("[Pyhopper Python Demo] " + line)
        log.Append(line + System.Environment.NewLine, True)

    def close_clicked(sender, event):
        dialog.Close()

    count_slider.ValueChanged += slider_changed

    print_button = forms.Button(Text="Print to Rhino")
    print_button.Click += print_clicked

    close_button = forms.Button(Text="Close")
    close_button.Click += close_clicked
    dialog.AbortButton = close_button

    layout = forms.DynamicLayout(Spacing=drawing.Size(8, 8))
    layout.AddRow(forms.Label(Text="Message"), message_box)
    layout.AddRow(forms.Label(Text="Count"), count_slider)
    layout.AddRow(enabled_box)
    layout.AddRow(progress)
    layout.AddRow(log)
    layout.AddSeparateRow(print_button, None, close_button)
    dialog.Content = layout
    dialog.ShowModal()


message = message or "Hello from Pyhopper Python"
count = max(0, int(count or 0))

if count > 100:
    ghenv.Component.AddRuntimeMessage(
        ghk.GH_RuntimeMessageLevel.Warning,
        "Count was limited to 100.",
    )
    count = 100

lines = ["{}: {}".format(index + 1, message) for index in range(count)]
points = [rg.Point3d(index * 2.0, 0.0, 0.0) for index in range(count)]
status = "Generated {} line(s) and point(s).".format(count)

ghenv.Component.Message = "{} item(s)".format(count)
Rhino.RhinoApp.WriteLine("[Pyhopper Python Demo] " + status)

if show_ui:
    show_demo_dialog(message, max(1, min(count, 20)))
