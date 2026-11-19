from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Any
import pandas as pd
import io
import time

from pipeline import categorize, generate_journal_entry

app = FastAPI(
    title="AI Transaction Categoriser API",
    description="Hybrid rule-based + ML pipeline for Namibian SME transactions.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORIES = ["Assets", "Liabilities", "Equity", "Income", "Expenses", "Drawings"]

class TransactionInput(BaseModel):
    description: str
    amount: Optional[float] = None
    date: Optional[str] = None

class BatchInput(BaseModel):
    transactions: List[TransactionInput]

@app.get("/")
def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "AI Transaction Categoriser",
        "version": "1.0.0",
        "categories": CATEGORIES,
    }

@app.get("/categories")
def get_categories() -> dict[str, List[str]]:
    return {"categories": CATEGORIES}

@app.post("/classify")
def classify_transaction(tx: TransactionInput) -> dict[str, Any]:
    if not tx.description or not tx.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty.")

    start = time.time()
    result = categorize(tx.description)
    
    journal = None
    if result["category"]:
        journal = generate_journal_entry(tx.description, tx.amount or 0.0, result["category"])

    elapsed_ms = (time.time() - start) * 1000

    return {
        "input": tx.description,
        "category": result["category"],
        "source": result["source"],
        "confidence": round(result["confidence"], 4),
        "suggestion": result["suggestion"],
        "message": result["message"],
        "processing_time_ms": round(elapsed_ms, 2),
        "journal_entry": journal
    }

@app.post("/classify-batch")
def classify_batch(payload: BatchInput) -> dict[str, Any]:
    if not payload.transactions:
        raise HTTPException(status_code=400, detail="Transaction list is empty.")

    start = time.time()
    results = []
    for tx in payload.transactions:
        result = categorize(tx.description)
        journal = None
        if result["category"]:
            journal = generate_journal_entry(tx.description, tx.amount or 0.0, result["category"])
            
        results.append({
            "input": tx.description,
            "category": result["category"],
            "source": result["source"],
            "confidence": round(result["confidence"], 4),
            "suggestion": result["suggestion"],
            "message": result["message"],
            "journal_entry": journal
        })
    elapsed_ms = (time.time() - start) * 1000

    return {
        "results": results,
        "summary": {
            "total": len(results),
            "by_source": {
                "rule": sum(1 for r in results if r["source"] == "rule"),
                "ml": sum(1 for r in results if r["source"] == "ml"),
                "needs_review": sum(1 for r in results if r["source"] == "needs_review"),
            },
        },
        "processing_time_ms": round(elapsed_ms, 2),
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = (file.filename or "").lower()
    
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")

    contents = await file.read()
    results = []
    start = time.time()

    try:
        if filename.endswith(".csv"):
            text = contents.decode("utf-8")
            df = pd.read_csv(io.StringIO(text))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        desc_col = next((col for col in df.columns if str(col).lower().strip() == "description"), None)
        if not desc_col:
            raise HTTPException(status_code=400, detail="File must have a 'description' column.")

        for _, row in df.iterrows():
            desc = str(row[desc_col])
            
            amount_val = 0.0
            if "amount" in df.columns:
                try:
                    amount_val = float(row["amount"])
                except:
                    pass

            # Extract the date if it exists in the file
            date_val = ""
            if "date" in df.columns:
                raw_date = row["date"]
                if pd.isna(raw_date):
                    date_val = ""
                elif isinstance(raw_date, pd.Timestamp):
                    # Excel dates arrive as Timestamps; keep the date only, drop the time
                    date_val = raw_date.strftime("%Y-%m-%d")
                else:
                    # CSV dates are already plain text
                    date_val = str(raw_date).strip()

            result = categorize(desc)
            results.append({
                "input": desc,
                "amount": amount_val,
                "date": date_val, 
                "category": result["category"],
                "source": result["source"],
                "confidence": round(result["confidence"], 4),
                "suggestion": result["suggestion"],
                "message": result["message"],
            })
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    elapsed_ms = (time.time() - start) * 1000

    return {
        "filename": file.filename,
        "results": results,
        "summary": {
            "total": len(results),
            "by_source": {
                "rule": sum(1 for r in results if r["source"] == "rule"),
                "ml": sum(1 for r in results if r["source"] == "ml"),
                "needs_review": sum(1 for r in results if r["source"] == "needs_review"),
            },
        },
        "processing_time_ms": round(elapsed_ms, 2),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)