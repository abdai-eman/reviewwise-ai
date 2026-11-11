MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://127.0.0.1:11434"
MAX_REVIEWS = 1000
MAX_REVIEW_LENGTH = 2000
REQUEST_TIMEOUT = 60.0

CATEGORIES = {
    "slow_service": "Slow service",
    "cold_coffee": "Cold coffee",
    "high_prices": "High prices",
    "dirty_tables": "Dirty tables",
    "incorrect_order": "Incorrect order",
    "unfriendly_staff": "Unfriendly staff",
    "other": "Other complaints (inspect individually)",
}

ACTIONS = {
    "slow_service": "Review the ordering and serving process to reduce waiting times.",
    "cold_coffee": "Check coffee temperature just before serving.",
    "high_prices": "Review pricing and communicate clearly what customers receive.",
    "dirty_tables": "Add a table-cleaning check between customers.",
    "incorrect_order": "Confirm each order before handing it to the customer.",
    "unfriendly_staff": "Discuss friendly, respectful service with the team.",
}
