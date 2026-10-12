import sys
import os
import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    print("\n[+] Opening web interface at http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

def main():
    print("===================================================================")
    print(" ⚡ AI Resume & Cover Letter Generator (Dual ATS + HR Scoring) ⚡ ")
    print("===================================================================")
    print("[*] Strict Candidate Fit Gate: 50+ Fit Bar & 0 Hard Knockouts")
    print("[*] Dual Advisory Heuristics: ATS Keyword + HR Recruiter Review")
    print("[*] Auto-Refinement Engine: Targets 75%+ Must-Have Evidence Match")
    print("[*] Artifacts: Production DOCX Files & Excel Tracker (applications.xlsx)")
    print("[*] Server starting at: http://localhost:8000")
    print("===================================================================\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run FastAPI server
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
