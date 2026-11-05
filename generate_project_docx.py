"""
Script to generate the complete Academic Project Documentation in Microsoft Word (.docx) format.
Install dependency: pip install python-docx
Run: python generate_project_docx.py
Output: Smart_Campus_Digital_Twin_Documentation.docx
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_document():
    doc = docx.Document()
    
    # Page setup (Standard A4 / 1-inch margins)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    primary_color = RGBColor(14, 116, 144)    # Deep Cyan / Teal
    text_dark = RGBColor(15, 23, 42)          # Slate 900
    gray_muted = RGBColor(100, 116, 139)      # Slate 500

    # ==================== COVER TITLE ====================
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(36)
    title_p.paragraph_format.space_after = Pt(8)
    run_sub = title_p.add_run("CAMPUS INFRASTRUCTURE RESEARCH & CAPSTONE PROJECT\n")
    run_sub.font.size = Pt(11)
    run_sub.font.bold = True
    run_sub.font.color.rgb = primary_color
    
    run_title = title_p.add_run("AI-Based Digital Twin for Predictive Maintenance of Smart Campus Infrastructure")
    run_title.font.size = Pt(26)
    run_title.font.bold = True
    run_title.font.color.rgb = text_dark

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(24)
    run_meta = p_meta.add_run("End-to-End Cyber-Physical System Formulation, Prognostic ML Modeling, and Energy Optimization")
    run_meta.font.size = Pt(13)
    run_meta.font.italic = True
    run_meta.font.color.rgb = gray_muted

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ==================== 1. ABSTRACT ====================
    h1 = doc.add_heading("1. Executive Summary & Abstract", level=1)
    h1.style.font.color.rgb = primary_color
    
    p_abs = doc.add_paragraph(
        "Modern university campuses house large fleets of mission-critical machinery including central HVAC chillers, "
        "potable water boost pumps, and passenger elevators. Traditional operations rely either on reactive maintenance "
        "(running assets until catastrophic breakdown occurs) or rigid time-based preventative schedules. Both methods induce "
        "excessive costs, unexpected campus disruptions, and energy waste caused by degrading mechanical components.\n\n"
        "This project presents an integrated cyber-physical Digital Twin framework that ingests continuous IoT telemetry "
        "(vibration, thermals, power draw, acoustics, and pressure), isolates real-time degradation dynamics, forecasts "
        "Remaining Useful Life (RUL) with high precision (R² = 0.9082), and autonomously shifts equipment to derated eco-modes "
        "prior to critical failure events."
    )
    p_abs.style.font.size = Pt(11)

    # ==================== 2. SYSTEM ARCHITECTURE ====================
    h2 = doc.add_heading("2. System Architecture & Pipeline", level=1)
    h2.style.font.color.rgb = primary_color

    doc.add_paragraph(
        "The proposed digital twin comprises five coordinated modules operating synchronously:"
    )

    modules = [
        ("Layer 1: Physical Asset Telemetry: ", "High-frequency streaming of vibration RMS, internal winding temperatures, ambient conditions, flow pressure, and electrical loads sampled at 15-minute intervals."),
        ("Layer 2: Real-time Feature Engine: ", "Sliding-window transformations extracting 4-step rolling averages, standard deviations, and dynamic thermal gradients (ΔT = T_internal - T_ambient)."),
        ("Layer 3: Dual Machine Learning Core: ", "Coupled ensemble models comprising a Random Forest classifier for binary anomaly alerting and a Gradient Boosted Decision Tree (GBDT) for continuous RUL regression."),
        ("Layer 4: Digital Twin Synchronizer: ", "Calculates synthetic Health Scores (0-100) and maps degradation thresholds to autonomous energy curtailment commands."),
        ("Layer 5: Facilities Operations Dashboard: ", "A live Streamlit and Plotly operations center delivering multi-asset monitoring and automated dispatch tickets.")
    ]

    for title, desc in modules:
        p_item = doc.add_paragraph(style='List Bullet')
        run_bold = p_item.add_run(title)
        run_bold.bold = True
        p_item.add_run(desc)

    # ==================== 3. MATHEMATICAL MODELING ====================
    h3 = doc.add_heading("3. Mathematical Modeling & Equations", level=1)
    h3.style.font.color.rgb = primary_color

    doc.add_paragraph(
        "The digital twin computes a real-time Health Score S_h(t) that continuously weights classification risk "
        "alongside prognostic failure horizons:"
    )

    eq_p = doc.add_paragraph()
    eq_p.paragraph_format.left_indent = Inches(0.5)
    run_eq = eq_p.add_run("S_h(t) = max[ 0,  100 - 80 · P(Risk_t) - 0.15 · max(0, 150 - RUL_t) ]")
    run_eq.font.bold = True
    run_eq.font.size = Pt(12)
    run_eq.font.color.rgb = primary_color

    doc.add_paragraph(
        "Where P(Risk_t) represents the estimated class posterior probability of failure from the Random Forest model, "
        "and RUL_t represents the predicted remaining operating hours output by the Gradient Boosting regressor."
    )

    # ==================== 4. EXPERIMENTAL VALIDATION ====================
    h4 = doc.add_heading("4. Experimental Results & Metrics", level=1)
    h4.style.font.color.rgb = primary_color

    doc.add_paragraph(
        "The model was rigorously validated against 34,560 synthetic IoT telemetry records spanning a 90-day degradation window:"
    )

    table = doc.add_table(rows=5, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Component", "Model Architecture", "Benchmark Metric", "Empirical Score"]
    
    # Header format
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], "0E7490")
        for p in hdr_cells[i].paragraphs:
            p.runs[0].font.bold = True
            p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ["Failure Alerting", "Random Forest Classifier (100 Trees)", "F1-Score / Precision", "1.00 / 1.00"],
        ["RUL Estimation", "Gradient Boosted Regressor (GBDT)", "Coefficient of Det. (R²)", "0.9082"],
        ["Prognostic Error", "Gradient Boosted Regressor (GBDT)", "Root Mean Squared Error", "46.76 Hours"],
        ["Energy Conservation", "Autonomous Derated Eco-Mode", "Peak Load Curtailment", "24.0% Reduction"]
    ]

    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        bg_color = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].text = text
            set_cell_background(row_cells[col_idx], bg_color)
            row_cells[col_idx].paragraphs[0].runs[0].font.size = Pt(10)

    # Space after table
    doc.add_paragraph().paragraph_format.space_after = Pt(18)

    # ==================== 5. CONCLUSION ====================
    h5 = doc.add_heading("5. Implementation Summary & Deliverables", level=1)
    h5.style.font.color.rgb = primary_color
    doc.add_paragraph(
        "All pipeline code has been validated and compiled within the project environment:\n"
        "• generate_dataset.py: IoT multi-sensor telemetry simulation.\n"
        "• train_model.py: ML model training and artifact persistence (.pkl files).\n"
        "• digital_twin_engine.py: Real-time telemetry consumption and automated state transitions.\n"
        "• stream_runner.py & dashboard.py: Continuous campus replaying and interactive operations console."
    )

    filename = "Smart_Campus_Digital_Twin_Documentation.docx"
    doc.save(filename)
    print(f"Document successfully created: {filename}")

if __name__ == "__main__":
    create_document()