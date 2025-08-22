import os
from supabase import create_client
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MONGO_URL = os.getenv("MONGO_URL")
mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["recruiter-platform"]
candidates_col = mongo_db["candidates"]
jobs_col = mongo_db["jds"]


def get_all_results():

    response = []

    jobs = list(jobs_col.find({}))

    for job in jobs:
        job_id = str(job["_id"])
        job_title = job.get("title", "Untitled Job")

        candidates = list(candidates_col.find({"jdId": job["_id"]}))
        candidate_data = []

        for cand in candidates:
            cand_name = cand.get("name", "Unknown")
            cand_email = cand.get("email", "Unknown")
            cand_id = str(cand["_id"])

            qsets = supabase.table("question_sets").select("*").eq("jd_id", job_id).execute()
            qset_ids = [q["id"] for q in qsets.data] if qsets.data else []

            test_result = None
            if qset_ids:
                res = supabase.table("test_results")\
                    .select("*")\
                    .in_("question_set_id", qset_ids)\
                    .eq("candidate_id", cand_id)\
                    .order("created_at", desc=True)\
                    .limit(1)\
                    .execute()

                if res.data:
                    test_result = res.data[0]

            candidate_data.append({
                "name": cand_name,
                "ID": cand_id,
                "email": cand_email,
                "score": test_result["score"] if test_result else None,
                "max_score": test_result["max_score"] if test_result else None,
                "status": test_result["status"] if test_result else "Not Attempted",
                "evaluated_at": test_result["evaluated_at"] if test_result else None,
            })

        response.append({
            "jobId": job_id,
            "jobTitle": job_title,
            "totalCandidates": len(candidates),
            "candidates": candidate_data
        })

    return response



if __name__ == "__main__":
    import json
    data = get_all_results()
    print(json.dumps(data, indent=2, default=str))
