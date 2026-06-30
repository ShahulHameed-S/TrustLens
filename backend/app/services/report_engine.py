import os
import json
import logging
import uuid
import html
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportContent, ReportGenerationResult

logger = logging.getLogger(__name__)

class ReportEngine:
    def __init__(self):
        self.repository = ReportRepository()

    def create_report_content(
        self,
        asset_info: Dict[str, Any],
        hash_result: Optional[Any],
        metadata_result: Optional[Any],
        forensics_result: Optional[Any],
        trust_score_result: Any,
        ai_explanation_result: Any,
        blockchain_proof: Optional[Any] = None
    ) -> ReportContent:
        """Create a structured ReportContent object from provided results."""
        
        return ReportContent(
            verification_summary=ai_explanation_result.summary if ai_explanation_result else "Verification complete.",
            asset_details=asset_info,
            hash_details=hash_result.model_dump() if hash_result else None,
            metadata_details=metadata_result.model_dump() if metadata_result else None,
            forensic_findings=forensics_result.model_dump() if forensics_result else None,
            trust_score=trust_score_result.trust_score,
            risk_level=trust_score_result.risk_level.value if hasattr(trust_score_result.risk_level, 'value') else str(trust_score_result.risk_level),
            document_status=trust_score_result.document_status.value if hasattr(trust_score_result.document_status, 'value') else str(trust_score_result.document_status),
            ai_explanation=ai_explanation_result.model_dump() if ai_explanation_result else None,
            blockchain_proof=blockchain_proof.model_dump() if blockchain_proof else None,
            generated_at=datetime.utcnow()
        )

    def save_json_report(self, report_content: ReportContent, output_dir: str) -> str:
        """Save report as JSON file securely."""
        filename = f"report_{uuid.uuid4().hex}.json"
        
        # Prevent path traversal implicitly by strictly joining with a clean filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename generated")
            
        file_path = os.path.join(output_dir, filename)
        
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_content.model_dump(), f, indent=4, default=str)
            
        logger.info(f"JSON report saved successfully")
        return file_path

    def save_html_report(self, report_content: ReportContent, output_dir: str) -> str:
        """Save report as a standalone HTML file securely."""
        filename = f"report_{uuid.uuid4().hex}.html"
        
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename generated")
            
        file_path = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)
        
        # Safely escape text content
        def safe_text(val):
            if val is None:
                return "N/A"
            return html.escape(str(val))
            
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrustLens Verification Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .status-badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
        .authentic {{ background: #d4edda; color: #155724; }}
        .suspicious {{ background: #fff3cd; color: #856404; }}
        .unverified {{ background: #f8d7da; color: #721c24; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; width: 30%; }}
        pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TrustLens Verification Report</h1>
        <p><strong>Generated At:</strong> {safe_text(report_content.generated_at)}</p>
        <p><strong>Status:</strong> <span class="status-badge {safe_text(report_content.document_status).lower()}">{safe_text(report_content.document_status)}</span></p>
        <p><strong>Risk Level:</strong> {safe_text(report_content.risk_level)}</p>
        <p><strong>Trust Score:</strong> {safe_text(report_content.trust_score)} / 100</p>
    </div>

    <div class="section">
        <h2>Verification Summary</h2>
        <p>{safe_text(report_content.verification_summary)}</p>
    </div>

    <div class="section">
        <h2>Asset Details</h2>
        <table>
            <tbody>
"""
        for k, v in report_content.asset_details.items():
            html_content += f"<tr><th>{safe_text(k)}</th><td>{safe_text(v)}</td></tr>\n"
            
        html_content += """
            </tbody>
        </table>
    </div>
"""

        if report_content.blockchain_proof:
            html_content += f"""
    <div class="section">
        <h2>Blockchain Proof</h2>
        <pre>{safe_text(json.dumps(report_content.blockchain_proof, indent=2, default=str))}</pre>
    </div>
"""
        else:
            html_content += """
    <div class="section">
        <h2>Blockchain Proof</h2>
        <p>Blockchain proof was not available or not generated for this asset.</p>
    </div>
"""

        html_content += f"""
    <div class="section">
        <h2>Raw Evidence</h2>
        <h3>AI Explanation</h3>
        <pre>{safe_text(json.dumps(report_content.ai_explanation, indent=2, default=str)) if report_content.ai_explanation else "N/A"}</pre>
        <h3>Hash Details</h3>
        <pre>{safe_text(json.dumps(report_content.hash_details, indent=2, default=str)) if report_content.hash_details else "N/A"}</pre>
        <h3>Metadata Details</h3>
        <pre>{safe_text(json.dumps(report_content.metadata_details, indent=2, default=str)) if report_content.metadata_details else "N/A"}</pre>
        <h3>Forensic Findings</h3>
        <pre>{safe_text(json.dumps(report_content.forensic_findings, indent=2, default=str)) if report_content.forensic_findings else "N/A"}</pre>
    </div>
</body>
</html>
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        logger.info(f"HTML report saved successfully")
        return file_path

    def save_pdf_report(self, report_content: ReportContent, output_dir: str) -> str:
        """Save report as a standalone PDF file securely."""
        filename = f"report_{uuid.uuid4().hex}.pdf"
        
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename generated")
            
        file_path = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)
        
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add Header
        title_style = styles['Heading1']
        elements.append(Paragraph("TrustLens Verification Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Summary Section
        elements.append(Paragraph(f"<b>Generated At:</b> {str(report_content.generated_at)}", styles['Normal']))
        elements.append(Paragraph(f"<b>Status:</b> {str(report_content.document_status)}", styles['Normal']))
        elements.append(Paragraph(f"<b>Risk Level:</b> {str(report_content.risk_level)}", styles['Normal']))
        elements.append(Paragraph(f"<b>Trust Score:</b> {str(report_content.trust_score)} / 100", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("<b>Verification Summary:</b>", styles['Heading2']))
        elements.append(Paragraph(str(report_content.verification_summary), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Asset Details
        elements.append(Paragraph("<b>Asset Details:</b>", styles['Heading2']))
        data = [[str(k), str(v)] for k, v in report_content.asset_details.items()]
        t = Table(data, colWidths=[150, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        # Blockchain Proof
        elements.append(Paragraph("<b>Blockchain Proof:</b>", styles['Heading2']))
        if report_content.blockchain_proof:
            bc_str = json.dumps(report_content.blockchain_proof, indent=2, default=str)
        else:
            bc_str = "Blockchain proof was not available or not generated for this asset."
        
        code_style = ParagraphStyle(name='Code', parent=styles['Normal'], fontName='Courier', fontSize=8)
        elements.append(Paragraph(bc_str.replace('\n', '<br/>'), code_style))
        
        doc.build(elements)
        logger.info(f"PDF report saved successfully")
        return file_path

    def generate_report(
        self,
        db: Session,
        verification_id: UUID,
        asset_info: Dict[str, Any],
        hash_result: Optional[Any],
        metadata_result: Optional[Any],
        forensics_result: Optional[Any],
        trust_score_result: Any,
        ai_explanation_result: Any,
        blockchain_proof: Optional[Any] = None,
        report_format: str = "JSON",
        output_dir: str = "/tmp/trustlens_reports"
    ) -> ReportGenerationResult:
        """
        Main entrypoint for generating, saving, and registering a verification report.
        """
        logger.info(f"Report generation started for verification {verification_id} in {report_format} format")
        
        try:
            report_format = report_format.upper()
            if report_format not in ["JSON", "HTML", "PDF"]:
                raise ValueError(f"Unsupported report format: {report_format}")

            report_content = self.create_report_content(
                asset_info=asset_info,
                hash_result=hash_result,
                metadata_result=metadata_result,
                forensics_result=forensics_result,
                trust_score_result=trust_score_result,
                ai_explanation_result=ai_explanation_result,
                blockchain_proof=blockchain_proof
            )
            logger.info("Report content created")
            
            # Normalize and secure output directory to prevent traversal
            safe_output_dir = os.path.abspath(output_dir)
            
            if report_format == "JSON":
                file_path = self.save_json_report(report_content, safe_output_dir)
            elif report_format == "HTML":
                file_path = self.save_html_report(report_content, safe_output_dir)
            elif report_format == "PDF":
                file_path = self.save_pdf_report(report_content, safe_output_dir)
                
            # Optional DB record creation if db is provided
            db_report_id = None
            if db:
                # Store the relative/public URL instead of internal path if there is a storage service,
                # but for v1.0 we'll store the local path or a safe reference.
                db_report = self.repository.create_report(
                    db=db, 
                    verification_id=verification_id, 
                    report_url=file_path
                )
                db_report_id = db_report.id

            return ReportGenerationResult(
                report_id=db_report_id,
                verification_id=verification_id,
                report_format=report_format,
                report_path=file_path,
                generated_at=report_content.generated_at,
                status="COMPLETED",
                summary="Report generated and saved successfully."
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return ReportGenerationResult(
                report_id=None,
                verification_id=verification_id,
                report_format=report_format,
                report_path="",
                generated_at=datetime.utcnow(),
                status="FAILED",
                summary=f"Report generation failed: {str(e)}"
            )

    def generate_report_from_existing(
        self,
        db: Session,
        verification_id: UUID,
        report_format: str = "JSON",
        output_dir: str = "/tmp/trustlens_reports"
    ) -> ReportGenerationResult:
        """
        Generate a report in the specified format using an existing JSON report.
        """
        report_format = report_format.upper()
        if report_format not in ["JSON", "HTML"]:
            raise ValueError(f"Unsupported report format: {report_format}")

        existing_report = self.repository.get_report_by_verification_id(db, verification_id)
        if not existing_report:
            raise ValueError("VERIFICATION_NOT_FOUND or REPORT_NOT_FOUND")

        # Check if existing report is JSON
        if not existing_report.report_url.endswith(".json"):
            # If it's already HTML and they want HTML, just return it
            if existing_report.report_url.endswith(".html") and report_format == "HTML":
                return ReportGenerationResult(
                    report_id=existing_report.id,
                    verification_id=verification_id,
                    report_format="HTML",
                    report_path=existing_report.report_url,
                    generated_at=existing_report.generated_at,
                    status="READY",
                    summary="Existing HTML report returned."
                )
            raise ValueError("Existing report is not JSON, cannot convert.")

        if report_format == "JSON":
            return ReportGenerationResult(
                report_id=existing_report.id,
                verification_id=verification_id,
                report_format="JSON",
                report_path=existing_report.report_url,
                generated_at=existing_report.generated_at,
                status="READY",
                summary="Existing JSON report returned."
            )

        # We need to convert JSON to HTML
        try:
            with open(existing_report.report_url, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            report_content = ReportContent(**data)
            safe_output_dir = os.path.abspath(output_dir)
            file_path = self.save_html_report(report_content, safe_output_dir)
            
            # Update DB with new URL
            existing_report.report_url = file_path
            db.commit()
            
            return ReportGenerationResult(
                report_id=existing_report.id,
                verification_id=verification_id,
                report_format="HTML",
                report_path=file_path,
                generated_at=existing_report.generated_at,
                status="READY",
                summary="Report converted to HTML successfully."
            )
        except Exception as e:
            logger.error(f"Failed to regenerate report: {str(e)}")
            raise ValueError(f"REPORT_GENERATION_FAILED: {str(e)}")
