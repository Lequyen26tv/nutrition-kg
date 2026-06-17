@echo off
title He thong Dinh duong Graph-RAG (NGR-Engine)
cls
echo ==========================================================
echo   DANG KICH HOAT HE THONG HYBRID GRAPH-RAG TU DONG...
echo ==========================================================
echo.

:: 1. KÍCH HOẠT BACKEND FASTAPI TRÊN PORT 8000
echo -> Dang khoi dong Backend FastAPI (Uvicorn)...
start "NGR - Backend Server" cmd /k "cd /d D:\KHOALUAN9\nutrition_graph_rag\backend && ..\venv\Scripts\python.exe -m uvicorn app.main:app --reload"

:: Chờ 3 giây để Backend khởi động xong port và kết nối Neo4j
timeout /t 3 /nobreak > null

:: 2. KÍCH HOẠT FRONTEND STREAMLIT TRÊN PORT 8501
echo -> Dang khoi dong Frontend Streamlit Interface...
start "NGR - Frontend Web" cmd /k "cd /d D:\KHOALUAN9\nutrition_graph_rag\frontend && ..\venv\Scripts\python.exe -m streamlit run app.py"

echo.
echo ==========================================================
echo   KICH HOAT THANH CONG! VUI LONG KIEM TRA CA 2 CUA SO.
echo ==========================================================
timeout /t 5