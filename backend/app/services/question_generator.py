class AIQuestionService:
    def generate(self, session: dict, max_questions: int = 5) -> list[dict]:
        profile = session.get("profile", {})
        basic_info = profile.get("basic_info", {})
        skills = profile.get("skills", {})
        work_preferences = profile.get("work_preferences", {})
        resume = session.get("resume", {})

        questions = []
        self._add_if_needed(
            questions,
            not profile.get("education_background") and not resume.get("education"),
            "education",
            "What is your highest completed education level, and what did you study?",
            "Education history is missing, which weakens role-fit scoring.",
        )
        self._add_if_needed(
            questions,
            len(skills.get("merged", [])) < 3,
            "skills",
            "Which 3 to 5 skills best represent your strengths today?",
            "Too few confirmed skills were captured from the form or resume.",
        )
        self._add_if_needed(
            questions,
            not profile.get("target_roles"),
            "target_roles",
            "Which job titles are you most interested in for your next role?",
            "Target roles are missing, so recommendations cannot be ranked well.",
        )
        self._add_if_needed(
            questions,
            not basic_info.get("years_of_experience") and basic_info.get("years_of_experience") != 0,
            "experience",
            "How many years of relevant experience do you have, including internships or freelance work?",
            "Experience level is missing and is useful for job matching.",
        )
        self._add_if_needed(
            questions,
            not work_preferences.get("employment_type") or not work_preferences.get("remote_preference"),
            "work_preferences",
            "What type of work arrangement do you prefer, such as full-time, contract, remote, hybrid, or onsite?",
            "Work preferences are incomplete.",
        )

        resume_roles = set(role.lower() for role in resume.get("role_keywords", []))
        target_roles = set(role.lower() for role in profile.get("target_roles", []))
        self._add_if_needed(
            questions,
            bool(resume_roles) and bool(target_roles) and resume_roles.isdisjoint(target_roles),
            "role_alignment",
            "Your resume suggests roles that differ from your selected target roles. Which direction should we prioritize?",
            "Resume role signals and selected role targets do not align.",
        )
        self._add_if_needed(
            questions,
            not basic_info.get("summary"),
            "motivation",
            "What kind of problems or projects do you enjoy working on most?",
            "A short motivation summary helps recommendation explanations feel more relevant.",
        )

        return questions[:max_questions]

    def _add_if_needed(self, questions: list[dict], condition: bool, category: str, question: str, reason: str) -> None:
        if not condition:
            return
        questions.append(
            {
                "category": category,
                "question": question,
                "reason": reason,
            }
        )