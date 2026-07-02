from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.export_service.exporters import export_csv, export_excel, export_pdf
from app.schemas import ExportRequest
from app.services.jd_service import get_job_description
from app.services.ranking_service import get_rankings_for_jd

CONTENT_TYPES = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def handle_export(db: Session, payload: ExportRequest) -> tuple[bytes, str, str]:
    jd = get_job_description(db, payload.job_description_id)
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    results = get_rankings_for_jd(db, payload.job_description_id)
    if payload.candidate_ids:
        results = [r for r in results if r["candidate_id"] in payload.candidate_ids]
    if not results:
        raise HTTPException(status_code=400, detail="No ranking results available to export")

    if payload.format == "csv":
        data = export_csv(results)
    elif payload.format == "xlsx":
        data = export_excel(results, jd.title)
    else:
        data = export_pdf(results, jd.title)

    filename = f"shortlist_{jd.title.replace(' ', '_')[:30]}.{payload.format}"
    return data, CONTENT_TYPES[payload.format], filename
