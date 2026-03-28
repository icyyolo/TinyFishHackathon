import uuid

from sqlalchemy import desc, select

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import User, UserPreference, UserPreferenceHistory


class PreferenceRepository:
    def parse_id(self, value: str, field_name: str = "id") -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, TypeError) as error:
            raise ValidationError(f"Invalid {field_name}.") from error

    def require_user(self, user_id: str) -> User:
        parsed_user_id = self.parse_id(user_id, "user_id")
        user = db.session.get(User, parsed_user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    def get_current_preferences(self, user_id: str):
        parsed_user_id = self.parse_id(user_id, "user_id")
        record = db.session.scalar(
            select(UserPreference).where(UserPreference.user_id == parsed_user_id)
        )
        return record.to_dict() if record else None

    def get_preference_history(self, user_id: str, limit: int = 10):
        parsed_user_id = self.parse_id(user_id, "user_id")
        rows = db.session.scalars(
            select(UserPreferenceHistory)
            .where(UserPreferenceHistory.user_id == parsed_user_id)
            .order_by(desc(UserPreferenceHistory.created_at))
            .limit(limit)
        ).all()
        return [row.to_dict() for row in rows]

    def upsert_preferences(
        self,
        user_id: str,
        raw_preferences: dict,
        normalized_preferences: dict,
        ranking_profile: dict,
        defaults_applied: dict,
    ):
        user = self.require_user(user_id)
        record = db.session.scalar(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        event_type = "create"
        changed_fields = []

        if not record:
            record = UserPreference(
                user_id=user.id,
                raw_preferences=raw_preferences,
                normalized_preferences=normalized_preferences,
                ranking_profile=ranking_profile,
                defaults_applied=defaults_applied,
                version=1,
            )
            db.session.add(record)
            changed_fields = sorted(list(normalized_preferences.keys()))
        else:
            event_type = "update"
            changed_fields = self._changed_fields(
                record.normalized_preferences or {}, normalized_preferences
            )
            record.raw_preferences = raw_preferences
            record.normalized_preferences = normalized_preferences
            record.ranking_profile = ranking_profile
            record.defaults_applied = defaults_applied
            record.version += 1

        db.session.flush()

        history = UserPreferenceHistory(
            user_id=user.id,
            preference_id=record.id,
            event_type=event_type,
            changed_fields=changed_fields,
            snapshot={
                "raw_preferences": raw_preferences,
                "normalized_preferences": normalized_preferences,
                "ranking_profile": ranking_profile,
                "defaults_applied": defaults_applied,
                "version": record.version,
            },
        )
        db.session.add(history)
        db.session.commit()

        return record.to_dict(), history.to_dict()

    def _changed_fields(self, previous: dict, current: dict) -> list[str]:
        keys = set(previous.keys()) | set(current.keys())
        return sorted([key for key in keys if previous.get(key) != current.get(key)])
