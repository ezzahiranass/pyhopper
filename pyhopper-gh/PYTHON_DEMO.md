# Grasshopper Python Demo

This demo requires Rhino 8 and does not require a .NET SDK.

## Run It

1. Open Rhino 8 and run `Grasshopper`.
2. Add a **Python 3 Script** component from `Maths > Script`.
3. Create and rename its inputs:

   | Name | Type hint | Access |
   | --- | --- | --- |
   | `message` | `str` | Item |
   | `count` | `int` | Item |
   | `show_ui` | `bool` | Item |

4. Create and rename its outputs:

   | Name | Access |
   | --- | --- |
   | `lines` | List |
   | `points` | List |
   | `status` | Item |

5. Open [python_demo_component.py](python_demo_component.py), paste it into the component editor, and run it.
6. Connect a Button component to `show_ui` to open the Eto dialog on demand.

The script prints to Rhino's command history, creates points, emits text, displays
Grasshopper runtime warnings, updates its component message, and opens an Eto UI.

## Publish It

Once the script works, run Rhino's `ScriptEditor` command and create a project to
publish it as a reusable Grasshopper component or `.gha` plugin.
