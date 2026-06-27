"""
config.py – Centralised runtime configuration constants.
Non-secret values that are fixed across environments live here.
"""

# Directories (relative to the blog_automation root)
DB_PATH = "storage/database.db"
LOGS_DIR = "logs"
GENERATED_DIR = "generated"

# Scheduler
DEFAULT_SCHEDULE_TIME = "09:00"

# AI defaults
DEFAULT_MODEL = "gpt-4o"
MIN_WORD_COUNT = 2000
MAX_WORD_COUNT = 3000
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60

# HTTP request headers for Pinterest scraping
PINTEREST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# HTML post template path (relative to blog_automation root)
HTML_TEMPLATE = "templates/post_template.html"

# Site configuration for internal linking
SITE_URL = "https://yarnoodle.com"
SITE_NAME = "Yarnoodle Amigurumi"
SITE_TAGLINE = "Bringing yarn to life, one stitch at a time."

# Social handles
PINTEREST_HANDLE = "YarnoodleAmigurumi"
