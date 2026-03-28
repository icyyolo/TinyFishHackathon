import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.errors import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models import (
    ExtractedSkill,
    GeneratedQuestion,
    OnboardingAnswer,
    OnboardingSession,
    User,
)


class OnboardingRepository:
    def parse_id(self, value: str, field_name: str = "id") -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, TypeError) as error:
            raise ValidationError(f"Invalid {field_name}.") from error

    def find_user(self, user_id: str):
        user = db.session.get(User, self.parse_id(user_id, "user_id"))
        if not user:
            raise NotFoundError("User not found.")
        return user.to_dict()

    def upsert_user(self, payload: dict):
        email = payload.get("email")
        user_id = payload.get("user_id")

        if not user_id and not email:
            raise ValidationError("User payload must include either user_id or email.")

        user = None
        parsed_user_id = None
        if user_id:
            parsed_user_id = self.parse_id(user_id, "user_id")
            user = db.session.get(User, parsed_user_id)
            if not user:
                user = User(id=parsed_user_id)
                db.session.add(user)

        if email:
            normalized_email = email.lower()
            email_match = db.session.scalar(select(User).where(User.email == normalized_email))
            if email_match and user and email_match.id != user.id:
                raise ConflictError("A user with the same email already exists.")
            if not user:
                user = email_match or User(email=normalized_email)
                if not email_match:
                    db.session.add(user)
            user.email = normalized_email

        if payload.get("full_name") is not None:
            user.full_name = payload.get("full_name")
        if payload.get("phone") is not None:
            user.phone = payload.get("phone")

        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ConflictError("A user with the same email already exists.") from error

        return user.to_dict()

    def create_session(self, user_id: str, payload: dict):
        session = OnboardingSession(
            user_id=user_id,
            status="draft",
            profile={
                "basic_info": payload.get("basic_profile", {}),
                "education_background": payload.get("education_background", []),
                "skills": {
                    "user_selected": payload.get("skills", []),
                    "extracted": [],
                    "merged": payload.get("skills", []),
                },
                "target_roles": payload.get("target_roles", []),
                "work_preferences": payload.get("work_preferences", {}),
                "ai_question_responses": [],
            },
            resume={
                "filename": None,
                "uploaded_at": None,
                "parsed_text_excerpt": None,
                "education": [],
                "skills": [],
                "role_keywords": [],
            },
            completion={
                "score": 0,
                "missing_fields": [],
                "updated_at": None,
            },
            finalized_profile=None,
        )
        db.session.add(session)
        db.session.commit()
        return session.to_dict()

    def get_session(self, session_id: str):
        session = db.session.get(OnboardingSession, self.parse_id(session_id, "session_id"))
        if not session:
            raise NotFoundError("Onboarding session not found.")
        return session.to_dict()

    def update_session(self, session_id: str, update_fields: dict):
        session = db.session.get(OnboardingSession, self.parse_id(session_id, "session_id"))
        if not session:
            raise NotFoundError("Onboarding session not found.")

        for key, value in update_fields.items():
            setattr(session, key, value)

        db.session.commit()
        return session.to_dict()

    def replace_generated_questions(self, session_id: str, questions: list[dict]):
        parsed_session_id = self.parse_id(session_id, "session_id")
        GeneratedQuestion.query.filter_by(session_id=parsed_session_id).delete()

        saved = []
        for item in questions:
            question = GeneratedQuestion(
                session_id=parsed_session_id,
                question=item["question"],
                category=item["category"],
                reason=item["reason"],
            )
            db.session.add(question)
            saved.append(question)

        db.session.commit()
        return [item.to_dict() for item in saved]

    def get_generated_questions(self, session_id: str):
        parsed_session_id = self.parse_id(session_id, "session_id")
        questions = db.session.scalars(
            select(GeneratedQuestion).where(GeneratedQuestion.session_id == parsed_session_id)
        ).all()
        return [item.to_dict() for item in questions]

    def save_answers(self, session_id: str, answers: list[dict]):
        parsed_session_id = self.parse_id(session_id, "session_id")
        saved = []

        for item in answers:
            question_id = self.parse_id(item["question_id"], "question_id")
            question = db.session.scalar(
                select(GeneratedQuestion).where(
                    GeneratedQuestion.id == question_id,
                    GeneratedQuestion.session_id == parsed_session_id,
                )
            )
            if not question:
                raise NotFoundError(
                    f"Generated question {item['question_id']} was not found for this session."
                )

            answer = db.session.scalar(
                select(OnboardingAnswer).where(
                    OnboardingAnswer.session_id == parsed_session_id,
                    OnboardingAnswer.question_id == question_id,
                )
            )
            if not answer:
                answer = OnboardingAnswer(
                    session_id=parsed_session_id,
                    question_id=question_id,
                    answer=item["answer"].strip(),
                    category=question.category,
                )
                db.session.add(answer)
            else:
                answer.answer = item["answer"].strip()
                answer.category = question.category

            question.status = "answered"
            saved.append(answer)

        db.session.commit()
        return [item.to_dict() for item in saved]

    def get_answers(self, session_id: str):
        parsed_session_id = self.parse_id(session_id, "session_id")
        answers = db.session.scalars(
            select(OnboardingAnswer).where(OnboardingAnswer.session_id == parsed_session_id)
        ).all()
        return [item.to_dict() for item in answers]

    def save_extracted_skills(self, session_id: str, skills: list[dict]):
        parsed_session_id = self.parse_id(session_id, "session_id")
        saved = []
        for item in skills:
            skill = db.session.scalar(
                select(ExtractedSkill).where(
                    ExtractedSkill.session_id == parsed_session_id,
                    ExtractedSkill.skill == item["skill"],
                )
            )
            if not skill:
                skill = ExtractedSkill(
                    session_id=parsed_session_id,
                    skill=item["skill"],
                    confidence=item["confidence"],
                    source=item.get("source", "resume"),
                )
                db.session.add(skill)
            else:
                skill.confidence = item["confidence"]
                skill.source = item.get("source", "resume")
            saved.append(skill)

        db.session.commit()
        return [item.to_dict() for item in saved]

    def get_extracted_skills(self, session_id: str):
        parsed_session_id = self.parse_id(session_id, "session_id")
        skills = db.session.scalars(
            select(ExtractedSkill).where(ExtractedSkill.session_id == parsed_session_id)
        ).all()
        return [item.to_dict() for item in skills]

    def update_user_onboarding_profile(self, user_id: str, profile: dict):
        user = db.session.get(User, self.parse_id(user_id, "user_id"))
        if not user:
            raise NotFoundError("User not found.")
        user.onboarding_profile = profile
        db.session.commit()
        return user.to_dict()