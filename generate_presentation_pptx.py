import sys
import collections
import collections.abc
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Academic Tech Palette
    C_BG = RGBColor(15, 23, 42)          # Slate 900
    C_CARD = RGBColor(30, 41, 59)        # Slate 800
    C_TEAL = RGBColor(45, 212, 191)      # Teal 400
    C_CYAN = RGBColor(56, 189, 248)      # Sky 400
    C_WHITE = RGBColor(248, 250, 252)    # Slate 50
    C_MUTED = RGBColor(148, 163, 184)    # Slate 400
    C_BORDER = RGBColor(51, 65, 85)      # Slate 700

    def apply_bg(slide):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = C_BG

    def add_slide_header(slide, title, category="SMART CAMPUS INFRASTRUCTURE • AI DIGITAL TWIN"):
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.5), Inches(0.35))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        p_c = tf_cat.paragraphs[0]
        p_c.text = category.upper()
        p_c.font.size = Pt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = C_TEAL

        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.7))
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        p_t = tf_title.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(24)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE

    blank_layout = prs.slide_layouts[6]

    # ---------------- SLIDE 1: Title ----------------
    s1 = prs.slides.add_slide(blank_layout)
    apply_bg(s1)

    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(4.2), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = C_CARD
    badge.line.color.rgb = C_TEAL
    p_b = badge.text_frame.paragraphs[0]
    p_b.text = "RESEARCH PROJECT DEFENSE"
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = C_TEAL
    p_b.alignment = PP_ALIGN.CENTER

    tb_t = s1.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(11.5), Inches(2.5))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "AI-Based Digital Twin for\nPredictive Maintenance"
    p1.font.size = Pt(40)
    p1.font.bold = True
    p1.font.color.rgb = C_WHITE

    p2 = tf_t.add_paragraph()
    p2.text = "Real-Time Telemetry Analytics, Fault Prognostics, and Dynamic Load Optimization"
    p2.font.size = Pt(18)
    p2.font.color.rgb = C_MUTED
    p2.space_before = Pt(14)

    tb_f = s1.shapes.add_textbox(Inches(0.8), Inches(5.8), Inches(11.5), Inches(0.8))
    p_f = tb_f.text_frame.paragraphs[0]
    p_f.text = "Smart Campus Infrastructure  |  Dual ML Modeling (RF + GBDT)  |  Closed-Loop Edge Control"
    p_f.font.size = Pt(12)
    p_f.font.color.rgb = C_TEAL

    # ---------------- SLIDE 2: Problem & Motivation ----------------
    s2 = prs.slides.add_slide(blank_layout)
    apply_bg(s2)
    add_slide_header(s2, "Executive Context & Research Motivation")

    s2_cards = [
        ("Traditional Facility Dilemma", [
            "Run-to-failure triggers costly outages & halts critical campus activities",
            "Fixed calendar maintenance replaces functional parts prematurely",
            "Zero multi-sensor cross-correlation across legacy facilities"
        ], Inches(0.8)),
        ("The Digital Twin Solution", [
            "Continuous physical-to-virtual bidirectional state tracking",
            "Synthesizes multi-sensor vibration, thermal, and acoustic signals",
            "Dynamic health scoring & automated failure alerts before catastrophic drift"
        ], Inches(4.7)),
        ("Core Project Deliverables", [
            "Zero unplanned downtime via 48-hour failure prediction window",
            "Dual ML architecture: binary risk classifier + RUL regressor",
            "Autonomous closed-loop derating & maintenance dispatch directives"
        ], Inches(8.6))
    ]
    for title, pts, left in s2_cards:
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.8), Inches(3.7), Inches(4.8))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD
        card.line.color.rgb = C_BORDER
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left, tf.margin_right, tf.margin_top = Inches(0.25), Inches(0.25), Inches(0.25)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = C_TEAL
        for pt in pts:
            p_pt = tf.add_paragraph()
            p_pt.text = f"• {pt}"
            p_pt.font.size = Pt(13)
            p_pt.font.color.rgb = C_WHITE
            p_pt.space_before = Pt(12)

    # ---------------- SLIDE 3: System Architecture ----------------
    s3 = prs.slides.add_slide(blank_layout)
    apply_bg(s3)
    add_slide_header(s3, "End-to-End Cyber-Physical Architecture")

    steps = [
        ("1. Campus Assets", "HVAC chillers, water pumps, elevator hoisting motors, backup power.", Inches(0.8)),
        ("2. IoT Telemetry", "15-min interval sampling: Vibration RMS, acoustics, pressure, ΔT, kW.", Inches(3.2)),
        ("3. Feature Pipeline", "Rolling window stats (1h), thermal dissipation gradient, occupancy flag.", Inches(5.6)),
        ("4. Dual ML Core", "Random Forest (Failure alert) + Gradient Boosted Regressor (RUL hours).", Inches(8.0)),
        ("5. Digital Twin Engine", "Health scoring (0-100), automated derating & dispatch actions.", Inches(10.4))
    ]
    for st_title, st_desc, left in steps:
        box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(2.2), Inches(2.2), Inches(3.8))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD
        box.line.color.rgb = C_TEAL
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left, tf.margin_right, tf.margin_top = Inches(0.15), Inches(0.15), Inches(0.2)
        p = tf.paragraphs[0]
        p.text = st_title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = C_TEAL
        p_d = tf.add_paragraph()
        p_d.text = st_desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = C_WHITE
        p_d.space_before = Pt(12)

    # ---------------- SLIDE 4: Dataset & Degradation ----------------
    s4 = prs.slides.add_slide(blank_layout)
    apply_bg(s4)
    add_slide_header(s4, "IoT Telemetry Dataset & Synthetic Degradation Modeling")

    card_l = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    card_l.fill.solid()
    card_l.fill.fore_color.rgb = C_CARD
    card_l.line.color.rgb = C_BORDER
    tf_l = card_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left, tf_l.margin_top = Inches(0.3), Inches(0.3)
    p_l_t = tf_l.paragraphs[0]
    p_l_t.text = "Dataset Synthesis Specifications"
    p_l_t.font.size = Pt(17)
    p_l_t.font.bold = True
    p_l_t.font.color.rgb = C_TEAL

    specs = [
        ("Total Records Generated", "34,560 time-series observations"),
        ("Monitoring Duration", "90 Continuous Days at 15-minute intervals"),
        ("Simulated Assets", "HVAC Chiller 01 & 02, Central Pump, Tower Elevator"),
        ("Diurnal Ambient Variation", "Sinusoidal outdoor cycle (18°C – 34°C)"),
        ("Occupancy Profile", "Campus load distribution (Peak 08:00-18:00 vs Idle)")
    ]
    for label, val in specs:
        p = tf_l.add_paragraph()
        p.text = f"{label}: {val}"
        p.font.size = Pt(13)
        p.font.color.rgb = C_WHITE
        p.space_before = Pt(8)

    card_r = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    card_r.fill.solid()
    card_r.fill.fore_color.rgb = C_CARD
    card_r.line.color.rgb = C_BORDER
    tf_r = card_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left, tf_r.margin_top = Inches(0.3), Inches(0.3)
    p_r_t = tf_r.paragraphs[0]
    p_r_t.text = "Physics Degradation Injection"
    p_r_t.font.size = Pt(17)
    p_r_t.font.bold = True
    p_r_t.font.color.rgb = C_TEAL

    degrads = [
        ("Wear Dynamics (w)", "Quadratic wear acceleration initiated 800 steps prior to failure"),
        ("Vibration RMS (mm/s)", "Base 1.2 mm/s escalating exponentially to >6.5 mm/s"),
        ("Thermal Dissipation", "Core motor temp spikes from 40°C nominal to >75°C under strain"),
        ("Fluid Flow & Pressure", "Booster pumps experience drop from 60 PSI down to 38 PSI"),
        ("Acoustic Signature", "Sound intensity spikes from 55 dB ambient to >85 dB rattling")
    ]
    for label, val in degrads:
        p = tf_r.add_paragraph()
        p.text = f"• {label}: {val}"
        p.font.size = Pt(13)
        p.font.color.rgb = C_WHITE
        p.space_before = Pt(8)

    # ---------------- SLIDE 5: ML Modeling & Validation ----------------
    s5 = prs.slides.add_slide(blank_layout)
    apply_bg(s5)
    add_slide_header(s5, "Predictive ML Modeling & Performance Verification")

    kpis = [
        ("Risk Classifier F1", "1.00", "Zero missed failures / alerts", Inches(0.8)),
        ("RUL Regressor R²", "0.9082", "Explains 90.8% variance", Inches(3.8)),
        ("RUL RMSE", "46.76 hrs", "< 2 working days prediction error", Inches(6.8)),
        ("Validation Pool", "6,912", "Stratified test instances", Inches(9.8))
    ]
    for title, val, sub, left in kpis:
        box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.8), Inches(2.7), Inches(1.6))
        box.fill.solid()
        box.fill.fore_color.rgb = C_CARD
        box.line.color.rgb = C_TEAL
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_top = Inches(0.15)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(12)
        p.font.color.rgb = C_MUTED
        pv = tf.add_paragraph()
        pv.text = val
        pv.font.size = Pt(28)
        pv.font.bold = True
        pv.font.color.rgb = C_TEAL
        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = Pt(10)
        ps.font.color.rgb = C_WHITE

    box_b = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(3.7), Inches(11.7), Inches(2.9))
    box_b.fill.solid()
    box_b.fill.fore_color.rgb = C_CARD
    box_b.line.color.rgb = C_BORDER
    tf_b = box_b.text_frame
    tf_b.word_wrap = True
    tf_b.margin_left, tf_b.margin_top = Inches(0.3), Inches(0.2)
    p_b_t = tf_b.paragraphs[0]
    p_b_t.text = "Mathematical Model Specifications"
    p_b_t.font.size = Pt(16)
    p_b_t.font.bold = True
    p_b_t.font.color.rgb = C_TEAL

    ml_notes = [
        "Random Forest Classifier: 100 decision trees, max depth = 8, stratified splits on imbalanced failure sequences.",
        "Gradient Boosting Regressor: 120 stages, learning rate = 0.08, max depth = 5, trained on degradation horizons.",
        "Dynamic Health Equation: Health = max(0, 100 - (P_risk * 80) - max(0, 150 - RUL_hours) * 0.15).",
        "Sliding Window Dynamics: 4-step rolling window (1 hour) captures acceleration in wear rather than static peaks."
    ]
    for n in ml_notes:
        p = tf_b.add_paragraph()
        p.text = f"• {n}"
        p.font.size = Pt(13)
        p.font.color.rgb = C_WHITE
        p.space_before = Pt(6)

    # ---------------- SLIDE 6: Live Verification ----------------
    s6 = prs.slides.add_slide(blank_layout)
    apply_bg(s6)
    add_slide_header(s6, "Autonomous Decision Engine & Live State Verification")

    col_l = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    col_l.fill.solid()
    col_l.fill.fore_color.rgb = C_CARD
    col_l.line.color.rgb = C_TEAL
    tf_col_l = col_l.text_frame
    tf_col_l.word_wrap = True
    tf_col_l.margin_left, tf_col_l.margin_top = Inches(0.3), Inches(0.25)
    p_col_l = tf_col_l.paragraphs[0]
    p_col_l.text = "Live Degraded Scenario (HVAC Chiller 01)"
    p_col_l.font.size = Pt(16)
    p_col_l.font.bold = True
    p_col_l.font.color.rgb = C_TEAL

    degraded_items = [
        "Input Vibration: 4.82 mm/s (Baseline: 1.20 mm/s)",
        "Internal Temp: 68.4°C | Ambient: 32.5°C (High Gradient)",
        "Power Draw: 54.3 kW (Surge above 45 kW nominal)",
        "Inferred Health Score: 29.2 / 100.0",
        "Operational Status: CRITICAL (Failure Risk = 70.0%)",
        "Predicted RUL: 51.6 Hours remaining (~2.1 days)",
        "Prescribed Directive: Immediate technician dispatch; derate to ECO."
    ]
    for it in degraded_items:
        p = tf_col_l.add_paragraph()
        p.text = f"▶ {it}"
        p.font.size = Pt(12)
        p.font.color.rgb = C_WHITE
        p.space_before = Pt(7)

    col_r = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    col_r.fill.solid()
    col_r.fill.fore_color.rgb = C_CARD
    col_r.line.color.rgb = C_BORDER
    tf_col_r = col_r.text_frame
    tf_col_r.word_wrap = True
    tf_col_r.margin_left, tf_col_r.margin_top = Inches(0.3), Inches(0.25)
    p_col_r = tf_col_r.paragraphs[0]
    p_col_r.text = "Healthy Baseline Scenario (HVAC Chiller 02)"
    p_col_r.font.size = Pt(16)
    p_col_r.font.bold = True
    p_col_r.font.color.rgb = C_TEAL

    healthy_items = [
        "Input Vibration: 1.25 mm/s (Smooth mechanical run)",
        "Internal Temp: 42.1°C | Ambient: 26.0°C (Nominal ΔT)",
        "Power Draw: 46.2 kW (Stable nominal operation)",
        "Inferred Health Score: 98.4 / 100.0",
        "Operational Status: HEALTHY (Failure Risk = 0.0%)",
        "Predicted RUL: > 500 Hours (Long-term stability)",
        "Prescribed Directive: Autonomous monitoring; efficiency optimized."
    ]
    for it in healthy_items:
        p = tf_col_r.add_paragraph()
        p.text = f"✔ {it}"
        p.font.size = Pt(12)
        p.font.color.rgb = C_WHITE
        p.space_before = Pt(7)

    # ---------------- SLIDE 7: Deliverables & Conclusion ----------------
    s7 = prs.slides.add_slide(blank_layout)
    apply_bg(s7)
    add_slide_header(s7, "Campus Impact & Complete Deliverables")

    s7_cards = [
        ("Software Architecture Deliverables", [
            "generate_dataset.py: 34,560-record IoT telemetry synthesizer",
            "train_model.py: ML pipeline producing classifier & regressor models",
            "digital_twin_engine.py: Real-time synchronization state class",
            "stream_runner.py & dashboard.py: Live continuous stream & dashboard"
        ], Inches(0.8)),
        ("Campus Infrastructure ROI", [
            "Zero unplanned downtime via 48-hour proactive scheduling window",
            "18% - 35% thermal peak power reduction through dynamic derating",
            "Extended mechanical asset lifespan by avoiding cascade stress",
            "Direct integration ready for campus BMS & MQTT sensor brokers"
        ], Inches(6.8))
    ]
    for title, pts, left in s7_cards:
        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.8), Inches(5.7), Inches(4.8))
        card.fill.solid()
        card.fill.fore_color.rgb = C_CARD
        card.line.color.rgb = C_BORDER
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left, tf.margin_top = Inches(0.3), Inches(0.25)
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = C_TEAL
        for pt in pts:
            p_pt = tf.add_paragraph()
            p_pt.text = f"• {pt}"
            p_pt.font.size = Pt(13)
            p_pt.font.color.rgb = C_WHITE
            p_pt.space_before = Pt(10)

    prs.save("Smart_Campus_Digital_Twin_Defense.pptx")
    print("SUCCESS: Smart_Campus_Digital_Twin_Defense.pptx generated successfully!")

if __name__ == "__main__":
    create_deck()
