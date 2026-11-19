"""Turn the base workbook written by scripts/build_shelf_workbook.py into the EPS 5.0 workbook.

The base build has already written, with the 5.0 timeslice names: About, Clustering, Annual category totals,
the ResStock / ComStock / EFS / Cambium source tabs, SHELF-days-per-timeslice and one SHELF-<category> tab per
4.0.x category. This module adds what 5.0 needs and puts the tabs in order.
"""
from __future__ import annotations
from openpyxl.styles import Alignment, Font

from . import about_text, industry, names, process_blend

HANDBUILT = ['Other Data & Calcs', 'NREL load shapes', 'EPRI load shapes', 'Ag']
LEFT_TOP_WRAP = Alignment(horizontal='left', vertical='top', wrap_text=True)


def split_datacenters(wb, tab_color: str) -> None:
    """One load shape per data-center end use. IT load ('other') is flat; facility load ('cooling') reads the IT
    tab for now, so a weather-driven cooling shape can be entered on its own tab later."""
    other = wb['SHELF-datacenters']
    other.title = 'SHELF-datacenters-other'
    cool = wb.create_sheet('SHELF-datacenters-cooling')
    cool.sheet_properties.tabColor = tab_color
    for r in range(1, 8):
        for c in range(1, 26):
            cool.cell(r, c, f"='SHELF-datacenters-other'!{other.cell(r, c).coordinate}")


def extend_about(wb, inputs_used: dict[str, str] | None = None, extra_notes: list[tuple[str, str]] | None = None) -> None:
    ws = wb['About']
    assert ws['A37'].value == 'Zero categories' and ws['A41'].value == 'Run metadata', (ws['A37'].value, ws['A41'].value)
    ws['B37'].value = about_text.ZERO_CATEGORIES_NOTE
    if inputs_used:
        ws['B41'].value = (ws['B41'].value.rstrip('.') + '; inputs read from: '
                           + ', '.join(f'{k} = {v}' for k, v in inputs_used.items()) + '.')
    r = about_text.FIRST_ROW
    for a, b in list(about_text.ROWS) + list(extra_notes or []):
        if a is not None:
            ws.cell(r, 1, a).font = Font(bold=True)
        if b is not None:
            c = ws.cell(r, 2, b)
            c.alignment = LEFT_TOP_WRAP
            if isinstance(b, str) and b.startswith('http'):
                c.hyperlink = b
                c.font = Font(color='0563C1', underline='single')
        r += 1


def tab_order(wb) -> list[str]:
    head = ['About', 'Clustering', 'Industry slice weights', 'Industry blend', industry.DAY, industry.BUILD,
            industry.EVID, 'Annual category totals', 'ResStock national source', 'ComStock national source',
            'EFS source', industry.SRC, 'Cambium hourly source'] + HANDBUILT
    outs = [n for n in wb.sheetnames if n.startswith('SHELF-') and not n.startswith('SHELF-indst')]
    outs.remove('SHELF-datacenters-cooling')
    outs.insert(outs.index('SHELF-datacenters-other'), 'SHELF-datacenters-cooling')
    ind = []
    for t in names.V5_TAGS:
        ind += [f'SHELF-indstproc-{t}', f'SHELF-indstcat-{t}']
    order = head + outs + ind + ['SHELF-indstCCS']
    missing, extra = set(order) - set(wb.sheetnames), set(wb.sheetnames) - set(order)
    assert not missing and not extra, (missing, extra)
    return order


def finish(wb, siels_stamps, siels_cols, tab_color: str, inputs_used=None, extra_notes=None) -> None:
    labels, tags = names.V5_LABELS, names.V5_TAGS
    for n in HANDBUILT:
        assert n in wb.sheetnames, f'hand-built tab {n!r} is missing: the 5.0 build starts from the seed workbook'
    process_blend.add_clustering_helpers(wb)
    for cat in ('district-heat-hydrogen', 'geoeng'):
        process_blend.set_system_load_shape(wb, cat)
    split_datacenters(wb, tab_color)
    process_blend.add_blend_and_outputs(wb, labels, tags, tab_color)
    industry.add_all(wb, siels_stamps, siels_cols, labels, tags, tab_color)
    extend_about(wb, inputs_used, extra_notes)
    wb._sheets = [wb[n] for n in tab_order(wb)]
    wb.active = 0
