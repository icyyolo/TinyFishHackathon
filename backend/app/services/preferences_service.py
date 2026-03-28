from app.repositories import PreferenceRepository
from app.services.preference_normalizer import PreferenceNormalizer


class PreferenceService:
    def __init__(self) -> None:
        self.repository = PreferenceRepository()
        self.normalizer = PreferenceNormalizer()

    def fetch_preferences(self, user_id: str):
        self.repository.require_user(user_id)
        current = self.repository.get_current_preferences(user_id)
        history = self.repository.get_preference_history(user_id)

        if not current:
            defaults = self.normalizer.normalize({})
            return {
                "user_id": user_id,
                "exists": False,
                "preferences": defaults["normalized_preferences"],
                "defaults_applied": defaults["defaults_applied"],
                "matching_strategy": defaults["matching_strategy"],
                "history": history,
            }

        return {
            "user_id": user_id,
            "exists": True,
            "preference_id": current["id"],
            "version": current["version"],
            "raw_preferences": current["raw_preferences"],
            "preferences": current["normalized_preferences"],
            "defaults_applied": current["defaults_applied"],
            "matching_strategy": current["ranking_profile"],
            "history": history,
        }

    def upsert_preferences(self, user_id: str, payload):
        raw_payload = payload.model_dump(mode="python", exclude_none=True)
        normalized = self.normalizer.normalize(raw_payload)
        current, history_entry = self.repository.upsert_preferences(
            user_id=user_id,
            raw_preferences=raw_payload,
            normalized_preferences=normalized["normalized_preferences"],
            ranking_profile=normalized["matching_strategy"],
            defaults_applied=normalized["defaults_applied"],
        )

        return {
            "user_id": user_id,
            "preference_id": current["id"],
            "version": current["version"],
            "raw_preferences": current["raw_preferences"],
            "preferences": current["normalized_preferences"],
            "defaults_applied": current["defaults_applied"],
            "matching_strategy": current["ranking_profile"],
            "history_entry": history_entry,
        }

    def normalize_preferences(self, payload):
        raw_payload = payload.model_dump(mode="python", exclude_none=True)
        normalized = self.normalizer.normalize(raw_payload)
        return {
            "raw_preferences": raw_payload,
            "preferences": normalized["normalized_preferences"],
            "defaults_applied": normalized["defaults_applied"],
            "matching_strategy": normalized["matching_strategy"],
        }
