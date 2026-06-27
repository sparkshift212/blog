# Yarnoodle AI Blog Automation 🧶

> **Automatically generate and publish SEO-optimised crochet blog posts every day — powered by OpenAI GPT-4o and your Pinterest account.**

---

## ✨ What It Does

| Step | Action |
|------|--------|
| 1 | Reads your newest Pinterest pin |
| 2 | Analyses title, description, image, and keywords |
| 3 | Generates a 2000–3000-word SEO blog article with GPT-4o |
| 4 | Produces full SEO metadata (title, slug, meta, keywords) |
| 5 | Generates 7 image prompts with alt text |
| 6 | Converts Markdown → clean semantic HTML |
| 7 | Publishes to your website (Static / WordPress / Custom API) |
| 8 | Updates `sitemap.xml` |
| 9 | Logs every article in SQLite to prevent duplicates |
| 10 | Runs automatically every day at 09:00 |

---

## 📁 Project Structure

```
blog_automation/
├── app.py                 # CLI entry point (Typer)
├── pipeline.py            # Main orchestration logic
├── config.py              # Non-secret constants
├── settings.py            # Pydantic env-var loading
├── logger.py              # Structured logging (Rich)
├── scheduler.py           # Daily job scheduler
├── database.py            # SQLite repository layer
├── models.py              # Pydantic data models
├── utils.py               # Shared helpers
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
│
├── services/
│   ├── pinterest.py       # Scrapes Pinterest profile
│   ├── ai_writer.py       # GPT-4o article generation
│   ├── seo.py             # SEO metadata validation
│   ├── images.py          # Image prompt generation
│   ├── markdown_converter.py  # Markdown → HTML
│   ├── publisher.py       # Static / WordPress / API publisher
│   ├── sitemap.py         # sitemap.xml manager
│   └── duplicate_checker.py   # Duplicate detection
│
├── storage/
│   └── database.db        # Auto-created SQLite database
├── logs/                  # Daily rotating log files
└── generated/             # Generated HTML, Markdown, JSON
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- An OpenAI API key (GPT-4o access)

### 2. Install

```bash
cd blog_automation
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
OPENAI_API_KEY=sk-...
PUBLISHER_MODE=static
```

### 4. Run

```bash
# Full pipeline (scrape → generate → publish)
python app.py run

# Generate only (no publishing)
python app.py generate

# Start the daily scheduler
python app.py schedule

# Check status of published articles
python app.py status

# View logs
python app.py logs
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI secret key |
| `OPENAI_MODEL` | | `gpt-4o` | Model to use |
| `PUBLISHER_MODE` | | `static` | `static` / `wordpress` / `api` |
| `WEBSITE_OUTPUT_DIR` | | `../generated_posts` | Output dir for static HTML |
| `WEBSITE_API` | | — | Custom REST API base URL |
| `WEBSITE_TOKEN` | | — | Bearer token for custom API |
| `WORDPRESS_URL` | | — | WordPress site URL |
| `WORDPRESS_USERNAME` | | — | WordPress username |
| `WORDPRESS_PASSWORD` | | — | WordPress application password |
| `PINTEREST_PROFILE_URL` | | YarnoodleAmigurumi | Pinterest profile to scrape |
| `SCHEDULE_TIME` | | `09:00` | Daily run time (24h format) |
| `POSTS_PER_DAY` | | `1` | Max articles per day |

---

## 📦 Publisher Modes

### Static HTML (Default)
Saves a standalone `.html` file to `WEBSITE_OUTPUT_DIR`. Copy to your server manually or via FTP/rsync.

```env
PUBLISHER_MODE=static
WEBSITE_OUTPUT_DIR=../generated_posts
```

### WordPress REST API
Posts directly to your WordPress site using the WP REST API with Application Passwords.

```env
PUBLISHER_MODE=wordpress
WORDPRESS_URL=https://your-site.com
WORDPRESS_USERNAME=admin
WORDPRESS_PASSWORD=xxxx xxxx xxxx xxxx
```

To create an Application Password in WordPress: **Users → Profile → Application Passwords**.

### Custom REST API
Posts to any custom endpoint expecting a JSON POST body.

```env
PUBLISHER_MODE=api
WEBSITE_API=https://your-site.com/api
WEBSITE_TOKEN=your-bearer-token
```

Expected request format:
```json
{
  "title": "...",
  "slug": "...",
  "html": "...",
  "markdown": "...",
  "meta_title": "...",
  "meta_description": "...",
  "focus_keyword": "...",
  "category": "...",
  "tags": ["..."],
  "status": "published"
}
```

---

## 🕙 Scheduling

### Built-in Scheduler (Recommended)
```bash
python app.py schedule
```
Runs continuously in the foreground. Keep it alive with a process manager.

### Windows Task Scheduler
1. Create a new Basic Task.
2. Set trigger: Daily at 09:00.
3. Action: Start a program → `python.exe`
4. Arguments: `C:\path\to\blog_automation\app.py run`

### Linux cron
```bash
0 9 * * * cd /path/to/blog_automation && python app.py run >> logs/cron.log 2>&1
```

---

## 🛡️ Duplicate Prevention

Before generating any article, the system checks **3 independent signals**:

1. **Content hash** – SHA-256 of `title + slug + topic`
2. **Slug** – exact URL slug match
3. **Topic** – case-insensitive topic string match

If any match is found, the pipeline skips generation and logs a warning.

---

## 📊 Logging

Log files are stored in `logs/YYYY-MM-DD.log` (one per day).

View logs in the terminal:
```bash
python app.py logs          # last 50 lines
python app.py logs -n 100   # last 100 lines
```

Log levels:
- `DEBUG` → file only
- `INFO`, `WARNING`, `ERROR` → file + console

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `OPENAI_API_KEY not set` | Add key to `.env` and restart |
| Pinterest returns empty data | Pinterest uses JS rendering; fallback topic is used |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Duplicate skipped every run | Change the pin on Pinterest or clear `database.db` |
| WordPress 401 error | Use an Application Password, not your login password |
| Static HTML missing styles | Copy `generated/` folder next to your `css/` folder |

---

## 🧪 Testing the Pipeline

```bash
# Test with a single run (no scheduler)
python app.py run

# Check what was saved
python app.py status

# Review today's logs
python app.py logs
```

---

## 📄 License

MIT License – use freely for your Yarnoodle Amigurumi business.

---

*Built with 🧶 for Yarnoodle Amigurumi – Bringing yarn to life, one stitch at a time.*
