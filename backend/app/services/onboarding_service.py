from datetime import datetime, timezone

from werkzeug.datastructures import FileStorage

from app.errors import ValidationError
from app.repositories import OnboardingRepository
from app.services.question_generator import AIQuestionService
from app.services.resume_parser import ResumeParserService
from app.utils.responses import serialize_document


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OnboardingService:
    def __init__(self) -> None:
        self.repository = OnboardingRepository()
        self.resume_parser = ResumeParserService()
        self.question_service = AIQuestionService()

    def create_session(self, payload):
        user = self.repository.upsert_user(payload.user.model_dump(exclude_none=True))
        session = self.repository.create_session(
            user["id"],
            payload.model_dump(mode="python", exclude_none=True),
        )
        completion = self._build_completion(session)
        session = self.repository.update_session(
            session["id"],
            {
                "status": "in_progress",
                "completion": completion,
            },
        )
        return serialize_document(session)

    def get_session(self, session_id: str):
        return serialize_document(self.repository.get_session(session_id))

    def update_session(self, session_id: str, payload):
        existing = self.repository.get_session(session_id)
        payload_dict = payload.model_dump(mode="python", exclude_none=True)

        if payload_dict.get("user"):
            self.repository.upsert_user(payload_dict["user"])

        profile = existing.get("profile", {})
        skills = profile.get("skills", {})

        updated_profile = {
            "basic_info": payload_dict.get("basic_profile", profile.get("basic_info", {})),
            "education_background": payload_dict.get(
                "education_background", profile.get("education_background", [])
            ),
            "skills": {
                "user_selected": payload_dict.get("skills", skills.get("user_selected", [])),
                "extracted": skills.get("extracted", []),
                "merged": self._merge_lists(
                    payload_dict.get("skills", skills.get("user_selected", [])),
                    skills.get("extracted", []),
                ),
            },
            "target_roles": self._merge_lists(payload_dict.get("target_roles", []))
            if "target_roles" in payload_dict
            else profile.get("target_roles", []),
            "work_preferences": payload_dict.get(
                "work_preferences", profile.get("work_preferences", {})
            ),
            "ai_question_responses": profile.get("ai_question_responses", []),
        }

        updated_session = self.repository.update_session(
            session_id,
            {
                "profile": updated_profile,
                "status": payload_dict.get("status", existing.get("status", "in_progress")),
            },
        )
        completion = self._build_completion(updated_session)
        updated_session = self.repository.update_session(
            session_id,
            {"completion": completion},
        )
        return serialize_document(updated_session)

    def upload_resume(self, session_id: str, resume_file: FileStorage):
        session = self.repository.get_session(session_id)
        if not resume_file.filename:
            raise ValidationError("Resume filename is required.")

        file_bytes = resume_file.read()
        parsed_resume = self.resume_parser.parse_resume(resume_file.filename, file_bytes)

        extracted_skills = [
            {"skill": skill, "confidence": 0.8} for skill in parsed_resume["skills"]
        ]
        self.repository.save_extracted_skills(session_id, extracted_skills)

        profile = session.get("profile", {})
        user_selected_skills = profile.get("skills", {}).get("user_selected", [])
        merged_skills = self._merge_lists(user_selected_skills, parsed_resume["skills"])

        resume_block = {
            "filename": parsed_resume["filename"],
            "uploaded_at": utcnow_iso(),
            "parsed_text_excerpt": parsed_resume["parsed_text_excerpt"],
            "education": parsed_resume["education"],
            "skills": parsed_resume["skills"],
            "role_keywords": parsed_resume["role_keywords"],
        }

        updated_profile = {
            **profile,
            "skills": {
                "user_selected": user_selected_skills,
                "extracted": parsed_resume["skills"],
                "merged": merged_skills,
            },
        }

        updated_session = self.repository.update_session(
            session_id,
            {
                "profile": updated_profile,
                "resume": resume_block,
            },
        )
        completion = self._build_completion(updated_session)
        updated_session = self.repository.update_session(session_id, {"completion": completion})
        return serialize_document(updated_session)

    def generate_questions(self, session_id: str, max_questions: int):
        session = self.repository.get_session(session_id)
        questions = self.question_service.generate(session, max_questions=max_questions)
        saved = self.repository.replace_generated_questions(session_id, questions)
        return {
            "session_id": session_id,
            "questions": serialize_document(saved),
        }

    def save_answers(self, session_id: str, payload):
        self.repository.get_session(session_id)
        self.repository.save_answers(
            session_id, payload.model_dump(mode="python")["answers"]
        )

        existing_session = self.repository.get_session(session_id)
        all_answers = self.repository.get_answers(session_id)
        profile = existing_session.get("profile", {})
        response_snapshot = [
            {
                "question_id": answer["question_id"],
                "answer": answer["answer"],
                "category": answer.get("category"),
            }
            for answer in all_answers
        ]
        profile["ai_question_responses"] = response_snapshot

        updated_session = self.repository.update_session(
            session_id,
            {
                "profile": profile,
                "completion": self._build_completion({**existing_session, "profile": profile}),
                "status": "in_progress",
            },
        )
        return serialize_document(updated_session)

    def finalize_session(self, session_id: str):
        session = self.repository.get_session(session_id)
        profile = session.get("profile", {})
        answers = serialize_document(self.repository.get_answers(session_id))
        finalized_completion = self._build_completion(session)

        final_profile = {
            "user_id": session["user_id"],
            "session_id": session["id"],
            "basic_profile": profile.get("basic_info", {}),
            "education_background": self._merge_lists_of_records(
                profile.get("education_background", []),
                [{"summary": item} for item in session.get("resume", {}).get("education", [])],
            ),
            "skills": profile.get("skills", {}),
            "target_roles": profile.get("target_roles") or session.get("resume", {}).get("role_keywords", []),
            "work_preferences": profile.get("work_preferences", {}),
            "ai_question_responses": answers,
            "resume_insights": {
                "skills": session.get("resume", {}).get("skills", []),
                "education": session.get("resume", {}).get("education", []),
                "role_keywords": session.get("resume", {}).get("role_keywords", []),
            },
            "completion": finalized_completion,
            "finalized_at": utcnow_iso(),
        }

        updated_session = self.repository.update_session(
            session_id,
            {
                "status": "finalized",
                "finalized_profile": final_profile,
                "completion": finalized_completion,
            },
        )
        self.repository.update_user_onboarding_profile(session["user_id"], final_profile)
        return serialize_document(updated_session)

    def _build_completion(self, session: dict) -> dict:
        profile = session.get("profile", {})
        basic_info = profile.get("basic_info", {})
        missing = []

        if not basic_info.get("headline"):
            missing.append("basic_profile.headline")
        if not basic_info.get("location"):
            missing.append("basic_profile.location")
        if not profile.get("education_background") and not session.get("resume", {}).get("education"):
            missing.append("education_background")
        if len(profile.get("skills", {}).get("merged", [])) < 3:
            missing.append("skills")
        if not profile.get("target_roles"):
            missing.append("target_roles")
        work_preferences = profile.get("work_preferences", {})
        if not work_preferences.get("employment_type"):
            missing.append("work_preferences.employment_type")
        if not work_preferences.get("remote_preference"):
            missing.append("work_preferences.remote_preference")

        total_checks = 7
        score = int(((total_checks - len(missing)) / total_checks) * 100)
        return {
            "score": max(score, 0),
            "missing_fields": missing,
            "updated_at": utcnow_iso(),
        }

    def _merge_lists(self, *lists):
        merged = []
        seen = set()
        for values in lists:
            for value in values:
                if not value:
                    continue
                normalized = value.strip()
                key = normalized.lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append(normalized)
        return merged

    def _merge_lists_of_records(self, manual_records: list[dict], extracted_records: list[dict]):
        seen = set()
        merged = []
        for record in manual_records + extracted_records:
            key = str(record).lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(record)
        return merged