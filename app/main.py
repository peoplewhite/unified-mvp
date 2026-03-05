"""
Unified MVP - FastAPI Application
Combines Vendor Scout and Credit Scout into one web app
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn

from app.vendor.scanner import VendorScanner
from app.vendor.exporter import VendorExporter
from app.credit.analyzer import CreditAnalyzer
from app.credit.reporter import CreditReporter

app = FastAPI(
    title="Unified MVP",
    description="AI Vendor Scout + SME Credit Scout",
    version="1.0.0"
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize modules
vendor_scanner = VendorScanner()
vendor_exporter = VendorExporter()
credit_analyzer = CreditAnalyzer()
credit_reporter = CreditReporter()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with entry cards for both tools"""
    return templates.TemplateResponse("index.html", {"request": request})


# ==================== Vendor Scout Routes ====================

@app.get("/vendor", response_class=HTMLResponse)
async def vendor_page(request: Request):
    """Vendor Scout page"""
    return templates.TemplateResponse("vendor.html", {"request": request})


@app.post("/api/vendor/search")
async def vendor_search(keyword: str = Form(...), country: str = Form(...)):
    """Search for vendors by keyword and country"""
    try:
        results = await vendor_scanner.search(keyword, country)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vendor/download/excel")
async def vendor_download_excel(keyword: str, country: str):
    """Download vendor results as Excel"""
    try:
        results = await vendor_scanner.search(keyword, country)
        file_path = vendor_exporter.to_excel(results, keyword, country)
        return FileResponse(
            file_path,
            filename=f"vendors_{keyword}_{country}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vendor/download/pdf")
async def vendor_download_pdf(keyword: str, country: str):
    """Download vendor results as PDF"""
    try:
        results = await vendor_scanner.search(keyword, country)
        file_path = vendor_exporter.to_pdf(results, keyword, country)
        return FileResponse(
            file_path,
            filename=f"vendors_{keyword}_{country}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Credit Scout Routes ====================

@app.get("/credit", response_class=HTMLResponse)
async def credit_page(request: Request):
    """Credit Scout page"""
    return templates.TemplateResponse("credit.html", {"request": request})


@app.post("/api/credit/analyze")
async def credit_analyze(company_name: str = Form(...)):
    """Analyze company credit risk"""
    try:
        result = await credit_analyzer.analyze(company_name)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/credit/download/pdf")
async def credit_download_pdf(company_name: str):
    """Download credit report as PDF"""
    try:
        result = await credit_analyzer.analyze(company_name)
        file_path = credit_reporter.to_pdf(result, company_name)
        return FileResponse(
            file_path,
            filename=f"credit_report_{company_name}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)