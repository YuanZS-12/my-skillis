"""Lightweight preflight for STEP artifacts returned from manual NX runs."""

from pathlib import Path


STEP_GEOMETRY_ENTITIES = (
    "MANIFOLD_SOLID_BREP",
    "BREP_WITH_VOIDS",
    "FACETED_BREP",
    "TESSELLATED_SOLID",
    "SHELL_BASED_SURFACE_MODEL",
)


def step_has_geometry(step: Path) -> bool:
    """Return true when a STEP DATA section names a supported geometry entity."""
    try:
        text = step.read_text(encoding="utf-8", errors="ignore").upper()
    except OSError:
        return False
    return any(entity in text for entity in STEP_GEOMETRY_ENTITIES)
