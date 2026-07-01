from enum import Enum

class Levels(Enum):
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

    def __init__(self, interactive: bool, level_name: str = ""):
        if not interactive:
            if level_name.lower() == "base":
                self.level = Levels.BASE
            elif level_name.lower() == "medium":
                self.level = Levels.MEDIUM
            else:
                self.level = Levels.TOTAL
        else:
            self.level: Levels = LevelSetter._ask_level()
        self.target_labels: list[str] = self.level.labels

    @staticmethod
    def _ask_level() -> Levels:
        while True:
            user_q = input(
                "\nSelect the level of censor you like:\n"
                "1) Base level:  Immediately redact sensitive information that could compromise the security of your accounts or savings. Remove passwords, digital access keys, tokens, and banking or credit card details.\n"
                "2) Medium level: It extends Base level to ensure maximum compliance with privacy regulations. It removes any data that could directly identify you or other individuals, such as names, email addresses, phone numbers, and identification documents.\n"
                "3) Beyond protecting accounts and identities, it eliminates every trace of geographic and temporal context—removing addresses, cities, states, and any dates mentioned in the audio—thereby rendering the conversation completely decontextualized.\n"
                "Insert the number: "
                )
            
            if user_q == "1":
                return Levels.BASE
            elif user_q == "2":
                return Levels.MEDIUM
            elif user_q == "3":
                return Levels.TOTAL
            else:
                print("Invalid input. Please enter 1,2 or 3")

