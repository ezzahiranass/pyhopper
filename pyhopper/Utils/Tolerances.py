"""Tolerance policy shared by the geometry kernels.

Grasshopper decides coincidence ("is this point on the curve?", "does the ray
hit?") with the Rhino document's absolute tolerance; pyhopper has no document,
so it uses Rhino's default of 0.01 model units. Exact comparisons of computed
numbers keep using the much tighter ``ZERO_TOLERANCE``.
"""

ABSOLUTE_TOLERANCE = 0.01
ZERO_TOLERANCE = 1e-12
