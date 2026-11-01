import openai
from openai import OpenAI
from dotenv import load_dotenv
import os

class SafetyGuard:
    def __init__(self, threshold: float = 0.5):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.threshold = threshold

    def is_safe(self, text: str) -> bool:
        try:
            response = self.client.moderations.create(input=text)
            scores_obj = response.results[0].category_scores
            flagged = response.results[0].flagged

            # ✅ Convert scores object to dictionary explicitly
            scores = dict(scores_obj)

            # Optional: Debug info
            print("MODERATION SCORES >>>", scores)

            too_high = any(score is not None and score > self.threshold for score in scores.values())
            return not (flagged or too_high)
        except Exception as e:
            print(f"[SafetyGuard] Error during moderation API call: {e}")
            return True

    def get_scores(self, text: str) -> dict:
        try:
            response = self.client.moderations.create(input=text)
            return dict(response.results[0].category_scores)
        except Exception as e:
            print(f"[SafetyGuard] Error during moderation API call: {e}")
            return {}
