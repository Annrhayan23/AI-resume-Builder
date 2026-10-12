import asyncio
import httpx
from backend.app import app

async def test_full_application():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test Static Frontend Serving
        r_home = await client.get("/")
        print(f"GET / (Frontend index.html) -> Status {r_home.status_code}")
        assert r_home.status_code == 200
        assert "<title>" in r_home.text
        assert "root" in r_home.text
        print("[+] Frontend static bundle correctly served by FastAPI")

        # 2. Test Master Resume Endpoint
        r_resume = await client.get("/api/master-resume")
        print(f"GET /api/master-resume -> Status {r_resume.status_code}")
        assert r_resume.status_code == 200
        data = r_resume.json()
        assert data["contact"]["name"] == "Alex Mercer"
        print(f"[+] Master Resume retrieved: {data['contact']['name']}")

        # 3. Test Fit Gate Endpoint (Passing)
        r_fit_pass = await client.post("/api/fit-gate", json={
            "job_description": "We need a Senior Full-Stack Engineer with Python, React, AWS, Docker.",
            "job_title": "Senior Full-Stack Engineer"
        })
        assert r_fit_pass.status_code == 200
        res_pass = r_fit_pass.json()
        assert res_pass["passed"] is True
        print(f"[+] Fit Gate (Pass) verified: Score {res_pass['fit_score']}/100, Passed: {res_pass['passed']}")

        # 4. Test Fit Gate Endpoint (Knockout)
        r_fit_ko = await client.post("/api/fit-gate", json={
            "job_description": "Vice President of Engineering. Requires 15+ years experience. Active Top Secret clearance required.",
            "job_title": "VP of Engineering"
        })
        assert r_fit_ko.status_code == 200
        res_ko = r_fit_ko.json()
        assert res_ko["passed"] is False
        assert len(res_ko["knockouts"]) > 0
        print(f"[+] Fit Gate (Knockout) verified: Score {res_ko['fit_score']}/100, Knockouts: {res_ko['knockouts']}")

        # 5. Test Tailoring Endpoint with Passing JD
        r_tailor = await client.post("/api/tailor", json={
            "job_description": "We need a Senior Software Engineer with Python, FastAPI, React, PostgreSQL, AWS.",
            "job_title": "Senior Software Engineer",
            "company_name": "TestCorp",
            "fit_bar": 50,
            "evidence_target": 75,
            "max_iterations": 3
        })
        assert r_tailor.status_code == 200
        tailor_res = r_tailor.json()
        assert tailor_res["success"] is True
        assert tailor_res["final_ats"]["score"] > 60
        assert tailor_res["final_hr"]["score"] > 60
        assert tailor_res["resume_docx_filename"].endswith(".docx")
        assert tailor_res["cover_letter_docx_filename"].endswith(".docx")
        print(f"[+] Tailoring Pipeline verified: Success={tailor_res['success']}, ATS={tailor_res['final_ats']['score']}, HR={tailor_res['final_hr']['score']}, Evidence={tailor_res['final_ats']['evidence_match_pct']}%")

        # 6. Test Tracker Endpoint
        r_apps = await client.get("/api/tracker/applications")
        assert r_apps.status_code == 200
        apps = r_apps.json()
        assert len(apps) >= 1
        print(f"[+] Tracker applications verified: {len(apps)} applications logged in Excel")

        # 7. Test Download Endpoint
        r_dl = await client.get(f"/api/download/{tailor_res['resume_docx_filename']}")
        assert r_dl.status_code == 200
        assert len(r_dl.content) > 1000
        print(f"[+] Resume DOCX download verified: {len(r_dl.content)} bytes")

        # 8. Test Settings Endpoint
        r_settings = await client.get("/api/settings")
        assert r_settings.status_code == 200
        settings = r_settings.json()
        print(f"[+] Settings verified: Model={settings['gemini_model']}, FitBar={settings['fit_bar_threshold']}")

    print("\n>>> ALL SYSTEM INTEGRATION TESTS PASSED 100%! <<<")

if __name__ == "__main__":
    asyncio.run(test_full_application())
