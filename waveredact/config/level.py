import json
from enum import Enum
from pathlib import Path

import questionary

from waveredact.utils.console import console


class Levels(Enum):
    """
    Enum representing different privacy levels for censoring.
    """
    BASE = "base"
    MEDIUM = "medium"
    TOTAL = "total"

    @property
    def labels(self) -> list[str]:
        base_labels = [
            "password", "api_key", "secret", "access_token", "recovery_code", 
            "iban", "bank_account", "account_number", "routing_number", 
            "payment_card", "card_number", "card_expiry", "card_cvv"
        ]
        
        medium_additions = [
            "person", "full_name", "first_name", "middle_name", "last_name", 
            "username", "email", "phone_number", "ip_address", "account_id",
            "sensitive_account_id", "government_id", "national_id_number", 
            "passport_number", "drivers_license_number", "tax_id", "tax_number", 
            "date_of_birth"
        ]
        
        total_additions = [
            "address", "street_address", "city", "state_or_region", "postal_code", 
            "country", "sensitive_date", "document_date", "expiration_date", 
            "transaction_date", "license_number"
        ]

        if self == Levels.BASE:
            return base_labels
        elif self == Levels.MEDIUM:
            return base_labels + medium_additions
        elif self == Levels.TOTAL:
            return base_labels + medium_additions + total_additions
        else:
            return []

class LevelSetter:
    """
    Handle the selection and configuration of the privacy level.

    Attributes:
        level           - Selected Levels enum
        target_labels   - List of labels associated with the selected level
    """
    def __init__(self, interactive: bool, level_name: str = "", custom_label_file: str | None = None):
        if custom_label_file:
            self.level = Levels.TOTAL
            self.target_labels = self.parse_labels(custom_label_file, self.level.labels)
            return
        
        if not interactive:
            if level_name.lower() == "base":
                self.level = Levels.BASE
            elif level_name.lower() == "medium":
                self.level = Levels.MEDIUM
            else:
                self.level = Levels.TOTAL
        else:
            self.level = self._ask_level()
            console.print("")
            
        self.target_labels = self.level.labels

    @staticmethod
    def _ask_level() -> Levels:
        """
        Interactively ask the user to select a privacy level.

        Return:
            Selected Levels enum
        """
        choices = [
            questionary.Choice("1) Base level: Redact passwords, banking info, etc.", value=Levels.BASE),
            questionary.Choice("2) Medium level: Base + names, emails, phones, IDs", value=Levels.MEDIUM),
            questionary.Choice("3) Total level: Medium + addresses, dates (full decontextualization)", value=Levels.TOTAL),
        ]
        
        answer = questionary.select(
            "Select the level of censor you like:",
            choices=choices
        ).ask()
        
        return answer

    @staticmethod
    def parse_labels(json_path: str, all_labels: list[str]) -> list[str]:

        path_obj = Path(json_path).resolve()

        if not path_obj.exists():
            raise FileNotFoundError(f"Custom label file not found at: {path_obj}")

        try:
            with open(path_obj, 'r') as file:
                labels = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"The file {json_path} is not a valid JSON. Error: {e}")

        if not isinstance(labels, list):
            raise TypeError("The custom JSON file must contain a list of strings (e.g., [\"email\", \"password\"]).")

        if not all(isinstance(item, str) for item in labels):
            raise ValueError("Invalid format: All elements inside the JSON list must be strings.")

        custom_labels = set(labels)
        full_labels = set(all_labels)

        unsupported_labels = custom_labels.difference(full_labels)

        if len(unsupported_labels) > 0:
            raise ValueError(f"These labels are not supported by the model: {list(unsupported_labels)}")
        
        return labels


