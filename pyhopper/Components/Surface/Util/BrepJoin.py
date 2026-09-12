"""BrepJoin - Join a number of Breps together (Grasshopper "Brep Join")."""

from __future__ import annotations

from pyhopper.Core.Atoms import AtomicBrep
from pyhopper.Core.Component import Access, Component, InputParam, OutputParam
from pyhopper.Utils.Boxes import shell_is_closed


class BrepJoin(Component):
    """Join a number of Breps together.

    Inputs:
        breps: Breps to join (Grasshopper Breps [list]).

    Outputs:
        breps: Joined Breps (Grasshopper Breps).
        closed: Closed flag for each resulting Brep (Grasshopper Closed).

    Notes:
        Grasshopper: Surface > Util > Brep Join (Join).
        pyhopper decisions: pyhopper Breps carry faces without edge topology, so joining concatenates
        every face into one Brep; ``closed`` is true when each face boundary is shared with another
        face (pole rows compared, either direction) — exact for boxes and other patch shells.
    """

    display_name = "Brep Join"
    nickname = "Join"
    gh_guid = "1addcc85-b04e-46e6-bd4a-6f6c93bf7efd"

    inputs = [
        InputParam("breps", AtomicBrep, Access.LIST),
    ]
    outputs = [
        OutputParam("breps", AtomicBrep, access=Access.LIST),
        OutputParam("closed", bool, access=Access.LIST),
    ]

    def generate(self, breps=None):
        faces = []
        for brep in (breps or []):
            faces.extend(brep.faces if isinstance(brep, AtomicBrep) else [brep])
        if not faces:
            return [], []
        joined = AtomicBrep(tuple(faces))
        return [joined], [shell_is_closed(joined)]
