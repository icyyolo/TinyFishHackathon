from flask import Blueprint

from app.utils.responses import success_response


questionnaire_bp = Blueprint("questionnaire", __name__)


@questionnaire_bp.get("")
def fetch_questionnaire():
    steps = [
        {
            "id": "domain",
            "type": "select",
            "question": "What domain are you targeting?",
            "sub": "Choose the field that excites you most.",
            "iconSet": "domain",
            "options": [
                {"id": "pm", "label": "Product Management", "iconName": "ClipboardList"},
                {"id": "ds", "label": "Data Science", "iconName": "BarChart3"},
                {"id": "swe", "label": "Software Engineering", "iconName": "Code2"},
                {"id": "ux", "label": "UX Design", "iconName": "Palette"},
                {"id": "mkt", "label": "Digital Marketing", "iconName": "TrendingUp"},
                {"id": "consulting", "label": "Consulting", "iconName": "Brain"},
            ],
        },
        {
            "id": "environment",
            "type": "select",
            "question": "Where do you want to work?",
            "sub": "Pick your ideal work environment.",
            "iconSet": "environment",
            "options": [
                {"id": "remote", "label": "Remote", "iconName": "Home"},
                {"id": "hybrid", "label": "Hybrid", "iconName": "RefreshCw"},
                {"id": "onsite", "label": "On-site", "iconName": "Building2"},
            ],
        },
        {
            "id": "job_types",
            "type": "multi_select",
            "multiple": True,
            "question": "What job types are you open to?",
            "sub": "Select one or more preferences.",
            "options": [
                {"id": "full_time", "label": "Full-time"},
                {"id": "contract", "label": "Contract"},
                {"id": "internship", "label": "Internship"},
            ],
        },
        {
            "id": "skills",
            "type": "tags",
            "question": "What are your key skills?",
            "sub": "Add the skills you bring to the table.",
            "defaults": ["Python", "SQL", "Data Visualization"],
        },
        {
            "id": "motivation",
            "type": "text",
            "question": "What type of projects do you enjoy the most?",
            "sub": "This helps personalize recommendation explanations.",
        },
    ]

    return success_response({"steps": steps})
