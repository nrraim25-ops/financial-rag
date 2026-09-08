"""
Generates a synthetic mutual fund factsheet PDF used to test the RAG pipeline.
This is fictional data for demo purposes only - not a real fund.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample_fund_factsheet.pdf")

doc = SimpleDocTemplate(OUT_PATH, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=18)
h2 = styles["Heading2"]
body = styles["Normal"]

story = []

story.append(Paragraph("Bluepeak Flexicap Fund", title_style))
story.append(Paragraph("Scheme Information Document (Fictional Sample Data for Testing)", body))
story.append(Spacer(1, 16))

story.append(Paragraph("Fund Overview", h2))
overview_text = (
    "Bluepeak Flexicap Fund is an open-ended equity scheme investing across large cap, "
    "mid cap and small cap stocks. The scheme aims to generate long-term capital appreciation "
    "by investing in a diversified portfolio of equity and equity-related instruments. "
    "The fund was launched on 14 March 2015 and is benchmarked against the Nifty 500 TRI."
)
story.append(Paragraph(overview_text, body))
story.append(Spacer(1, 12))

story.append(Paragraph("Key Fund Facts", h2))
facts_data = [
    ["Attribute", "Value"],
    ["Fund Manager", "Ananya Krishnan"],
    ["Launch Date", "14 March 2015"],
    ["Benchmark", "Nifty 500 TRI"],
    ["Fund Category", "Equity - Flexi Cap"],
    ["Minimum Investment (Lumpsum)", "Rs. 5,000"],
    ["Minimum SIP Amount", "Rs. 500 per month"],
    ["Exit Load", "1% if redeemed within 365 days"],
    ["Expense Ratio (Direct Plan)", "0.68%"],
    ["Expense Ratio (Regular Plan)", "1.94%"],
    ["AUM (as of 31 Jul 2026)", "Rs. 18,432 crore"],
    ["Riskometer", "Very High"],
]
facts_table = Table(facts_data, colWidths=[2.8 * inch, 3.2 * inch])
facts_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
]))
story.append(facts_table)
story.append(Spacer(1, 16))

story.append(Paragraph("Performance (Trailing Returns, as of 31 Jul 2026)", h2))
perf_data = [
    ["Period", "Fund Return (%)", "Benchmark Return (%)"],
    ["1 Year", "18.42", "16.05"],
    ["3 Years (CAGR)", "21.10", "18.77"],
    ["5 Years (CAGR)", "19.85", "17.32"],
    ["Since Inception (CAGR)", "16.94", "14.20"],
]
perf_table = Table(perf_data, colWidths=[2.2 * inch, 2 * inch, 2.2 * inch])
perf_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
]))
story.append(perf_table)
story.append(Spacer(1, 16))

story.append(Paragraph("Top 10 Holdings (as of 31 Jul 2026)", h2))
holdings_data = [
    ["Company", "Sector", "% of Net Assets"],
    ["HDFC Bank Ltd", "Financial Services", "8.21"],
    ["ICICI Bank Ltd", "Financial Services", "6.94"],
    ["Infosys Ltd", "Information Technology", "5.87"],
    ["Reliance Industries Ltd", "Energy", "5.42"],
    ["Larsen & Toubro Ltd", "Construction", "4.16"],
    ["Tata Consultancy Services", "Information Technology", "3.98"],
    ["Bharti Airtel Ltd", "Telecom", "3.55"],
    ["Axis Bank Ltd", "Financial Services", "3.21"],
    ["Sun Pharmaceutical Industries", "Healthcare", "2.87"],
    ["Titan Company Ltd", "Consumer Durables", "2.64"],
]
hold_table = Table(holdings_data, colWidths=[2.6 * inch, 2.2 * inch, 1.6 * inch])
hold_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
]))
story.append(hold_table)
story.append(Spacer(1, 16))

story.append(Paragraph("Risk Factors", h2))
risk_text = (
    "Mutual fund investments are subject to market risks. The value of investments may go up "
    "or down depending on market conditions. Past performance is not indicative of future "
    "returns. Investors are advised to read the Scheme Information Document and Statement of "
    "Additional Information carefully before investing. The fund carries concentration risk "
    "due to sector allocation and mid/small cap volatility risk."
)
story.append(Paragraph(risk_text, body))

doc.build(story)
print(f"Wrote sample PDF to {OUT_PATH}")
