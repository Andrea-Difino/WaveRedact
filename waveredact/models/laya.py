from laya import Router


class Laya:

    def __init__(self, router: Router) -> None:
        self.router = router

    def validate_entity(self, entity: str, entity_label: str, full_text: str) -> bool:

        state = {
            "audio_context": full_text,
            "extracted_entity": entity,
            "pii_category": entity_label
        }

        questions = {
            "pii_validation": {
                "type": "choice",
                "instructions" : f"L'elemento '{entity}' rappresenta un dato sensibile di tipo {entity_label} nel constesto fornito?",
                "criteria": {
                "true_positive": f"Yes, '{entity}' is a real sensitive data to censor.",
                "false_positive": f"No, '{entity}' It is harmless, a figure of speech, or a system error."
                },
            }
        }

        result = self.router.predict(state, questions)

        response = result["answers"]["pii_validation"]["choice"]

        return response == "true_positive"