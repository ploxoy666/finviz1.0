
import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
import matplotlib.pyplot as plt

class SnapshotService:
    """
    Generates quick PDF/Image snapshots of specific dashboard views.
    """
    
    @staticmethod
    def create_pdf_snapshot(title: str, subtitle: str, data_frames: dict = None, metrics: dict = None, figures: list = None):
        """
        Creates a PDF buffer for a specific view.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#1f4788"))
        normal_style = styles['Normal']
        
        story = []
        
        # 1. Header
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(subtitle, styles['Italic']))
        story.append(Spacer(1, 0.3 * inch))
        
        # 2. Metrics (if any)
        if metrics:
            story.append(Paragraph("Key Metrics", styles['Heading2']))
            m_data = [[k, str(v)] for k, v in metrics.items()]
            m_table = Table(m_data, colWidths=[3*inch, 3*inch])
            m_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f1f8e9")),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(m_table)
            story.append(Spacer(1, 0.2 * inch))

        # 3. DataFrames (if any)
        if data_frames:
            for df_name, df in data_frames.items():
                story.append(Paragraph(df_name, styles['Heading2']))
                # Convert DF to list of lists for Table
                df_data = [df.columns.tolist()] + df.values.tolist()
                # Simple formatting for large numbers
                formatted_data = []
                for row in df_data:
                    formatted_row = []
                    for val in row:
                        if isinstance(val, (int, float)):
                            formatted_row.append(f"{val:,.2f}")
                        else:
                            formatted_row.append(str(val))
                    formatted_data.append(formatted_row)
                
                t = Table(formatted_data, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1f4788")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                story.append(t)
                story.append(Spacer(1, 0.2 * inch))

        # 4. Figures (Matplotlib only for now)
        if figures:
            story.append(Paragraph("Visualizations", styles['Heading2']))
            for fig in figures:
                img_data = io.BytesIO()
                fig.savefig(img_data, format='png', bbox_inches='tight', dpi=150)
                img_data.seek(0)
                rl_img = RLImage(img_data, width=6*inch, height=3*inch)
                story.append(rl_img)
                story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        buffer.seek(0)
        return buffer
