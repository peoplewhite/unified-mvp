"""
Credit Reporter Module - Generates credit reports in various formats
"""

import os
from typing import Dict, Any
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class CreditReporter:
    """Generates credit analysis reports"""
    
    def __init__(self):
        self.temp_dir = "/tmp/unified_mvp"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def to_pdf(self, report: Dict[str, Any], company_name: str) -> str:
        """Generate PDF credit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.temp_dir}/credit_report_{company_name.replace(' ', '_')}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.5*inch)
        elements = []
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c5aa0'),
            spaceBefore=15,
            spaceAfter=10
        )
        
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        # Title
        elements.append(Paragraph("CREDIT RISK ASSESSMENT REPORT", title_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Company name and date
        elements.append(Paragraph(f"<b>{report['company_name']}</b>", styles['Heading2']))
        elements.append(Paragraph(f"Analysis Date: {report['analysis_date']}", header_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Horizontal line
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 0.2*inch))
        
        # Credit Score Section
        elements.append(Paragraph("CREDIT SCORE & RISK LEVEL", section_style))
        
        credit_data = report['credit_assessment']
        score_color = colors.green if credit_data['risk_color'] == 'green' else \
                      colors.orange if credit_data['risk_color'] == 'yellow' else colors.red
        
        score_table_data = [
            ['Credit Score', str(credit_data['credit_score'])],
            ['Risk Level', credit_data['risk_level']],
            ['Credit Limit', f"${credit_data['credit_limit_millions']:.2f}M"],
            ['Credit Period', credit_data['recommended_credit_period']],
        ]
        
        score_table = Table(score_table_data, colWidths=[2.5*inch, 3*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0FE')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Company Information
        elements.append(Paragraph("COMPANY INFORMATION", section_style))
        
        company_info = report['company_info']
        info_data = [
            ['Year Established', str(company_info['year_established'])],
            ['Years in Business', str(company_info['years_in_business'])],
            ['Annual Revenue', f"${company_info['annual_revenue_millions']:.2f}M"],
            ['Employee Count', f"{company_info['employee_count']:,}"],
            ['Industry', company_info['industry']],
            ['Business Type', company_info['business_type']],
        ]
        
        info_table = Table(info_data, colWidths=[2.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0FE')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Financial Health
        elements.append(Paragraph("FINANCIAL HEALTH", section_style))
        
        financial = report['financial_health']
        financial_data = [
            ['Existing Debt', f"${financial['existing_debt_millions']:.2f}M"],
            ['Debt to Revenue Ratio', financial['debt_to_revenue_ratio']],
            ['Financial Stability', financial['financial_stability']],
            ['Payment History', financial['payment_history']],
            ['Cash Flow', financial['cash_flow']],
            ['Profitability', financial['profitability']],
        ]
        
        financial_table = Table(financial_data, colWidths=[2.5*inch, 3*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F0FE')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(financial_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Risk Factors
        elements.append(Paragraph("RISK FACTORS", section_style))
        
        for i, factor in enumerate(report['risk_factors'], 1):
            elements.append(Paragraph(f"{i}. {factor}", styles['Normal']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Recommendation
        elements.append(Paragraph("RECOMMENDATION", section_style))
        
        rec_box = Table([[report['recommendation']]], colWidths=[5.5*inch])
        rec_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF3CD')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#856404')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FFEAA7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(rec_box)
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        elements.append(Spacer(1, 0.1*inch))
        footer_text = f"""
        <i>This report was generated by Unified MVP - Credit Scout</i><br/>
        Confidence Score: {report['confidence_score']}% | 
        Report ID: {datetime.now().strftime('%Y%m%d')}-{hash(company_name) % 10000:04d}
        """
        elements.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        return filename