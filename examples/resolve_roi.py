""" Example consumer: resolve a volume's annotated ROI by name, in a specific
consumer's expected axis order (instead of parsing the free-text bbox field)
"""

import lmd_catalog as lmd
from rich import print as pprint

vol = lmd.get("exm-drosophila-flyliconn-matt-260601-60X-B4-1-042/crop-001")
roi = vol.tracked_by[0].roi
pprint(roi)
if roi: pprint(roi.to_order("zyx"))
