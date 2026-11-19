"""Timeslice names. EPS 5.0 renamed the six timeslices (eps-us issue #413); the clustering code keeps its own names."""

CANONICAL = ['Winter', 'Spring', 'Summer', 'Fall', 'Summer Peak', 'Winter Peak']       # state_pipeline SLICE_NAMES
V5_LABELS = ['Representative Day 1', 'Representative Day 2', 'Representative Day 3', 'Representative Day 4',
             'Net Peak Summer Day', 'Net Peak Winter Day']
V5_TAGS = ['repday1', 'repday2', 'repday3', 'repday4', 'netpeaksummer', 'netpeakwinter']   # used in file names


def labels(version: str) -> list[str]:
    return list(V5_LABELS) if version == '5.0' else list(CANONICAL)
