#!/usr/bin/env python

import sys
import importlib.util
from pathlib import Path

import yaml
from html_to_docx import add_html
from markdown import markdown

from docx import Document
from docx.shared import Inches
from docx.shared import Pt
from docx.shared import Mm
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_ORIENTATION


def create_dvm(test_file_py):
    spec = importlib.util.spec_from_file_location("req_test", test_file_py)
    req_test = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(req_test)
    reqdata = yaml.safe_load(req_test.__doc__)
    reqdata.setdefault('reqprod', '')
    reqdata.setdefault('version', '')
    reqdata.setdefault('title', '')
    reqdata.setdefault('purpose', '')
    reqdata.setdefault('description', '')
    reqdata.setdefault('precondition', 'Default session')
    reqdata.setdefault('postcondition', 'Default session')
    reqdata.setdefault('details', '')

    steps = []
    for step_name in dir(req_test):
        if step_name.startswith("step_"):
            step = getattr(req_test, step_name)
            d = yaml.safe_load(step.__doc__)
            d.setdefault('action', '')
            d.setdefault('expected_result', '')
            d.setdefault('result', '')
            d.setdefault('comment', '')
            steps.append(d)

    dvm = Document()

    section = dvm.sections[-1]
    section.orientation = WD_ORIENTATION.LANDSCAPE

    # let's make the document A4 and not letter
    section = dvm.sections[0]
    section.page_height = Mm(210)
    section.page_width = Mm(297)
    section.left_margin = Mm(25.4)
    section.right_margin = Mm(25.4)
    section.top_margin = Mm(25.4)
    section.bottom_margin = Mm(25.4)
    section.header_distance = Mm(12.7)
    section.footer_distance = Mm(12.7)

    styles = dvm.styles
    heading = styles.add_style('Heading', WD_STYLE_TYPE.PARAGRAPH)
    heading.font.name = 'Calibri Light'
    heading.font.size = Pt(28)

    body = styles.add_style('Body', WD_STYLE_TYPE.PARAGRAPH)
    body.font.name = 'Calibri'
    body.font.size = Pt(11)
    body.font.bold = True

    normal_body = styles.add_style('Body Normal', WD_STYLE_TYPE.PARAGRAPH)
    normal_body.font.name = 'Calibri'
    normal_body.font.size = Pt(11)

    table_body = styles.add_style('Table Body', WD_STYLE_TYPE.TABLE)
    table_body.font.name = 'Calibri'
    table_body.font.size = Pt(11)

    border_table_body = styles['Table Grid']
    border_table_body.font.name = 'Calibri'
    border_table_body.font.size = Pt(11)

    dvm.styles.default(normal_body)

    dvm_heading = f'REQPROD {reqdata["reqprod"]} / MAIN ; {reqdata["version"]}'

    p = dvm.add_paragraph(dvm_heading)
    p.style = dvm.styles['Heading']

    p = dvm.add_paragraph('Tprocedure:')
    p.style = dvm.styles['Heading']

    records = (
        ('General:', dvm_heading),
        ('Title:', reqdata['title']),
        ('Purpose:', reqdata['purpose']),
    )

    table = dvm.add_table(rows=0, cols=2)
    table.style = table_body

    for title, content in records:
        row = table.add_row()
        p = row.cells[0].paragraphs[0]
        p.style = body
        p.text = title
        row.cells[0].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        p = row.cells[1].paragraphs[0]
        p.text = content

    row = table.add_row()
    p = row.cells[0].paragraphs[0]
    p.style = body
    p.text = 'Description:'
    p = row.cells[1].paragraphs[0]
    description = reqdata['description']
    for paragraph in description.split('\n'):
        html = markdown(paragraph)
        if html:
            p = add_html(p, html)

    table.columns[0].width = Mm(26)
    table.columns[1].width = Mm(218.4)

    table = dvm.add_table(rows=1, cols=2)
    table.style = table_body
    row = table.rows[0]
    p = row.cells[0].paragraphs[0]
    p.style = body
    p.text = "Precondition:"
    p = row.cells[1].paragraphs[0]
    p.text = reqdata["precondition"]
    table.columns[0].width = Mm(27)
    table.columns[1].width = Mm(216)

    dvm.add_page_break()

    p = dvm.add_paragraph("Test execution:")
    p.style = body

    table = dvm.add_table(rows=1, cols=5)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Test Step'
    hdr_cells[1].text = 'Action (client)'
    hdr_cells[2].text = 'Expected Result (ECU)'
    hdr_cells[3].text = 'Result'
    hdr_cells[4].text = 'Comment'

    for step, d in enumerate(steps, 1):
        row = table.add_row()
        row.cells[0].text = str(step)
        row.cells[1].text = d["action"]
        row.cells[2].text = d["expected_result"]
        row.cells[3].text = d["result"]
        row.cells[4].text = d["comment"]

    table.columns[0].width = Mm(19)
    table.columns[1].width = Mm(71.3)
    table.columns[2].width = Mm(32.5)
    table.columns[3].width = Mm(14.8)
    table.columns[4].width = Mm(101.2)

    records = (
        ('Postcondition:', reqdata['postcondition']),
        ('Details:', reqdata['details']),
        ('Path:', '-'),
    )

    table = dvm.add_table(rows=0, cols=2)
    table.style = table_body

    for title, content in records:
        row = table.add_row()
        p = row.cells[0].paragraphs[0]
        p.style = body
        p.text = title
        row.cells[0].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        row.cells[1].text = content

    table.columns[0].width = Mm(27)
    table.columns[1].width = Mm(216)

    docx_filename = Path(test_file_py).with_suffix('.docx').name
    docx_filename = docx_filename.replace("BSW_REQPROD_", "REQ_")
    print("Generated file: ", docx_filename)

    dvm.save(docx_filename)


if __name__ == '__main__':
    if len(sys.argv) != 2:
           sys.exit("Usage: dvm.py <test_file.py>")
    create_dvm(sys.argv[1])
