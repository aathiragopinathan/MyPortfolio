from __future__ import annotations

import argparse
import html
import json
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from textwrap import dedent
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
INDEX_FILE = ROOT / "index.html"
STYLES_FILE = ROOT / "styles.css"
NOJEKYLL_FILE = ROOT / ".nojekyll"


@dataclass(frozen=True)
class Project:
    title: str
    category: str
    description: str
    impact: str
    stack: list[str]


@dataclass(frozen=True)
class Experience:
    role: str
    company: str
    period: str
    summary: str
    highlights: list[str]


PORTFOLIO = {
    "name": "Aathira Gopinathan",
    "headline": "Building calm, useful AI experiences with a human point of view.",
    "intro": (
        "I like turning messy ideas into simple digital products. "
        "My work sits between product thinking, AI workflows, and clean user experience."
    ),
    "location": "Based in Germany",
    "status": "Open to AI, product, and software roles",
    "email": "hello@example.com",
    "about": (
        "This is a starter portfolio with placeholder content. The tone is intentionally "
        "simple, warm, and slightly futuristic so it feels personal without becoming overly formal."
    ),
    "focus_points": [
        "AI-assisted product design",
        "Workflow automation",
        "Human-centered interfaces",
    ],
    "projects": [
        Project(
            title="SignalDesk",
            category="AI Productivity Tool",
            description=(
                "A lightweight workspace that turns scattered notes, voice snippets, "
                "and links into structured daily briefs."
            ),
            impact="Reduced research prep time by 60% in early mock tests.",
            stack=["Python", "Prompt Design", "Automation", "UX Writing"],
        ),
        Project(
            title="CareLoop",
            category="Conversational Assistant",
            description=(
                "A simple assistant concept for helping users track routines, reminders, "
                "and emotional check-ins in a softer, less robotic way."
            ),
            impact="Designed to make habit tracking feel supportive instead of clinical.",
            stack=["LLM UX", "Conversation Design", "Prototyping"],
        ),
        Project(
            title="InsightCanvas",
            category="Data Storytelling",
            description=(
                "A dashboard-style concept that translates dense analytics into short, "
                "actionable narratives for non-technical teams."
            ),
            impact="Framed analytics around decisions rather than raw metrics.",
            stack=["Data Visualization", "Product Thinking", "Frontend Concepts"],
        ),
    ],
    "experience": [
        Experience(
            role="AI Product Intern",
            company="Nova Systems",
            period="2025 - Present",
            summary=(
                "Worked on internal AI workflows, lightweight prototypes, and early product "
                "ideas focused on reducing manual work."
            ),
            highlights=[
                "Mapped repetitive team processes and identified automation opportunities.",
                "Created prototype flows for AI-assisted summaries and task organization.",
                "Helped shape product copy so technical features felt easier to understand.",
            ],
        ),
        Experience(
            role="Software Engineering Intern",
            company="Pixel Foundry",
            period="2024 - 2025",
            summary=(
                "Supported frontend and backend work across small client-facing tools, "
                "with a focus on clarity, usability, and iteration speed."
            ),
            highlights=[
                "Built and refined UI components for internal web tools.",
                "Collaborated on bug fixes, QA feedback, and feature polish.",
                "Improved readability of technical flows for both users and teammates.",
            ],
        ),
    ],
}


STYLES = dedent(
    """\
    :root {
        --bg: #08111f;
        --bg-soft: #0f1c30;
        --line: rgba(165, 196, 255, 0.18);
        --text: #f5f7fb;
        --muted: #adc0e4;
        --accent: #82f3d5;
        --accent-warm: #f2b880;
        --glow: rgba(130, 243, 213, 0.26);
        --shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
        --sans: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
        --mono: "SFMono-Regular", "Menlo", "Monaco", monospace;
    }

    * {
        box-sizing: border-box;
    }

    html {
        scroll-behavior: smooth;
    }

    body {
        margin: 0;
        color: var(--text);
        background:
            radial-gradient(circle at top left, rgba(242, 184, 128, 0.18), transparent 30%),
            radial-gradient(circle at 80% 20%, rgba(130, 243, 213, 0.12), transparent 25%),
            linear-gradient(180deg, #07101b 0%, #091423 45%, #06111d 100%);
        font-family: var(--sans);
        min-height: 100vh;
        overflow-x: hidden;
    }

    body::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(173, 192, 228, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(173, 192, 228, 0.05) 1px, transparent 1px);
        background-size: 42px 42px;
        mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.4), transparent 85%);
        pointer-events: none;
    }

    .orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(16px);
        opacity: 0.35;
        pointer-events: none;
    }

    .orb.one {
        width: 260px;
        height: 260px;
        background: rgba(130, 243, 213, 0.18);
        top: 8%;
        right: -60px;
        animation: float 12s ease-in-out infinite;
    }

    .orb.two {
        width: 180px;
        height: 180px;
        background: rgba(242, 184, 128, 0.16);
        left: -40px;
        bottom: 12%;
        animation: float 15s ease-in-out infinite reverse;
    }

    @keyframes float {
        0%, 100% { transform: translate3d(0, 0, 0); }
        50% { transform: translate3d(0, -22px, 0); }
    }

    @keyframes fade-up {
        from {
            opacity: 0;
            transform: translateY(18px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    a {
        color: inherit;
        text-decoration: none;
    }

    .shell {
        width: min(1120px, calc(100% - 32px));
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        padding: 24px 0 8px;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.92rem;
        color: var(--muted);
    }

    .brand-mark {
        width: 38px;
        height: 38px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, rgba(130, 243, 213, 0.18), rgba(242, 184, 128, 0.22));
        border: 1px solid var(--line);
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.04) inset;
        font-family: var(--mono);
        color: var(--accent);
    }

    .nav-links {
        display: flex;
        gap: 18px;
        flex-wrap: wrap;
        color: var(--muted);
        font-size: 0.92rem;
    }

    .hero {
        display: grid;
        grid-template-columns: 1.35fr 0.9fr;
        gap: 26px;
        padding: 48px 0 28px;
        align-items: center;
    }

    .hero-copy,
    .hero-panel,
    section {
        animation: fade-up 0.7s ease both;
    }

    .kicker {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.04);
        color: var(--muted);
        font-size: 0.85rem;
        margin-bottom: 22px;
    }

    .kicker::before {
        content: "";
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 18px var(--glow);
    }

    h1,
    h2,
    h3,
    p {
        margin: 0;
    }

    h1 {
        font-size: clamp(2.9rem, 7vw, 5.8rem);
        line-height: 0.98;
        letter-spacing: -0.05em;
        max-width: 10ch;
    }

    .lead {
        margin-top: 20px;
        color: var(--muted);
        font-size: 1.06rem;
        line-height: 1.75;
        max-width: 62ch;
    }

    .hero-actions {
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        margin-top: 28px;
    }

    .button {
        border: 1px solid transparent;
        padding: 12px 18px;
        border-radius: 999px;
        font-weight: 600;
        transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
    }

    .button:hover {
        transform: translateY(-1px);
    }

    .button.primary {
        background: linear-gradient(135deg, rgba(130, 243, 213, 0.9), rgba(242, 184, 128, 0.88));
        color: #06111d;
        box-shadow: 0 18px 45px rgba(130, 243, 213, 0.2);
    }

    .button.secondary {
        background: rgba(255, 255, 255, 0.03);
        border-color: var(--line);
        color: var(--text);
    }

    .hero-panel,
    .card {
        background: linear-gradient(180deg, rgba(14, 26, 43, 0.92), rgba(9, 18, 31, 0.82));
        border: 1px solid var(--line);
        border-radius: 24px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(16px);
    }

    .hero-panel {
        padding: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-panel::after {
        content: "";
        position: absolute;
        inset: auto -40px -70px auto;
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(130, 243, 213, 0.18), transparent 68%);
    }

    .panel-label,
    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.74rem;
        color: #90a7cf;
    }

    .signal-line {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        padding: 14px 0;
        border-bottom: 1px solid rgba(165, 196, 255, 0.12);
        color: var(--muted);
        font-size: 0.95rem;
    }

    .signal-line strong {
        color: var(--text);
        font-weight: 600;
    }

    .signal-line:last-of-type {
        border-bottom: 0;
    }

    .tag-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 16px;
    }

    .tag {
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid rgba(165, 196, 255, 0.16);
        background: rgba(255, 255, 255, 0.03);
        color: #d5e1f8;
        font-size: 0.84rem;
    }

    main {
        padding-bottom: 56px;
    }

    section {
        padding: 28px 0;
    }

    .section-head {
        display: flex;
        justify-content: space-between;
        align-items: end;
        gap: 18px;
        margin-bottom: 18px;
    }

    .section-head h2 {
        font-size: clamp(1.7rem, 2.5vw, 2.3rem);
        letter-spacing: -0.04em;
    }

    .section-head p,
    .body-copy,
    .card p,
    .clean-list {
        color: var(--muted);
        line-height: 1.75;
    }

    .about-card {
        padding: 24px;
    }

    .project-grid,
    .experience-grid {
        display: grid;
        gap: 18px;
    }

    .project-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .experience-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .project-card,
    .timeline-card {
        padding: 24px;
    }

    .project-card h3,
    .timeline-card h3 {
        margin-top: 10px;
        margin-bottom: 12px;
        font-size: 1.3rem;
        letter-spacing: -0.03em;
    }

    .impact {
        margin-top: 18px;
        padding-top: 16px;
        border-top: 1px solid rgba(165, 196, 255, 0.12);
        color: var(--text);
        font-weight: 600;
    }

    .timeline-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: start;
        margin-bottom: 12px;
    }

    .period {
        color: var(--accent-warm);
        font-family: var(--mono);
        font-size: 0.85rem;
        white-space: nowrap;
    }

    .clean-list {
        margin: 16px 0 0;
        padding-left: 18px;
    }

    footer {
        padding: 18px 0 42px;
        color: #90a7cf;
        font-size: 0.92rem;
    }

    .footer-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        padding: 18px 20px;
        border-radius: 20px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.03);
    }

    .code-note {
        font-family: var(--mono);
        color: var(--accent);
    }

    @media (max-width: 980px) {
        .hero,
        .project-grid,
        .experience-grid {
            grid-template-columns: 1fr;
        }

        .hero {
            padding-top: 28px;
        }
    }

    @media (max-width: 720px) {
        .topbar,
        .section-head,
        .timeline-top,
        .footer-card {
            flex-direction: column;
            align-items: flex-start;
        }

        h1 {
            max-width: 100%;
        }

        .shell {
            width: min(100% - 24px, 1120px);
        }
    }
    """
)


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def initials(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "AG"


def render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="tag">{escape(tag)}</span>' for tag in tags)


def render_projects(projects: list[Project]) -> str:
    cards = []
    for project in projects:
        cards.append(
            f"""
            <article class="card project-card">
                <p class="eyebrow">{escape(project.category)}</p>
                <h3>{escape(project.title)}</h3>
                <p>{escape(project.description)}</p>
                <div class="impact">{escape(project.impact)}</div>
                <div class="tag-row">{render_tags(project.stack)}</div>
            </article>
            """
        )
    return "".join(cards)


def render_experience(items: list[Experience]) -> str:
    cards = []
    for item in items:
        highlights = "".join(f"<li>{escape(point)}</li>" for point in item.highlights)
        cards.append(
            f"""
            <article class="card timeline-card">
                <div class="timeline-top">
                    <div>
                        <p class="eyebrow">{escape(item.company)}</p>
                        <h3>{escape(item.role)}</h3>
                    </div>
                    <span class="period">{escape(item.period)}</span>
                </div>
                <p>{escape(item.summary)}</p>
                <ul class="clean-list">{highlights}</ul>
            </article>
            """
        )
    return "".join(cards)


def content_payload() -> dict[str, object]:
    return {
        "name": PORTFOLIO["name"],
        "headline": PORTFOLIO["headline"],
        "projects": [asdict(project) for project in PORTFOLIO["projects"]],
        "experience": [asdict(item) for item in PORTFOLIO["experience"]],
    }


def build_page() -> str:
    focus_tags = render_tags(PORTFOLIO["focus_points"])
    projects = render_projects(PORTFOLIO["projects"])
    experience = render_experience(PORTFOLIO["experience"])
    email = escape(PORTFOLIO["email"])
    brand = initials(PORTFOLIO["name"])

    return dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{escape(PORTFOLIO["name"])} | Portfolio</title>
            <meta
                name="description"
                content="A simple AI-inspired portfolio website built for GitHub Pages."
            />
            <link rel="stylesheet" href="styles.css" />
        </head>
        <body>
            <div class="orb one"></div>
            <div class="orb two"></div>
            <div class="shell">
                <header class="topbar">
                    <div class="brand">
                        <div class="brand-mark">{brand}</div>
                        <div>
                            <strong>{escape(PORTFOLIO["name"])}</strong><br />
                            <span>{escape(PORTFOLIO["status"])}</span>
                        </div>
                    </div>
                    <nav class="nav-links">
                        <a href="#about">About</a>
                        <a href="#projects">Projects</a>
                        <a href="#experience">Experience</a>
                        <a href="mailto:{email}">Contact</a>
                    </nav>
                </header>

                <main>
                    <section class="hero">
                        <div class="hero-copy">
                            <div class="kicker">AI-inspired portfolio / simple by design</div>
                            <h1>{escape(PORTFOLIO["headline"])}</h1>
                            <p class="lead">{escape(PORTFOLIO["intro"])}</p>
                            <div class="hero-actions">
                                <a class="button primary" href="mailto:{email}">Let's connect</a>
                                <a class="button secondary" href="#projects">View projects</a>
                            </div>
                        </div>

                        <aside class="hero-panel">
                            <p class="panel-label">Current Signal</p>
                            <div class="signal-line">
                                <span>Location</span>
                                <strong>{escape(PORTFOLIO["location"])}</strong>
                            </div>
                            <div class="signal-line">
                                <span>Focus</span>
                                <strong>AI x Product x UX</strong>
                            </div>
                            <div class="signal-line">
                                <span>Approach</span>
                                <strong>Calm, practical, human</strong>
                            </div>
                            <div class="signal-line">
                                <span>Status</span>
                                <strong>{escape(PORTFOLIO["status"])}</strong>
                            </div>
                            <div class="tag-row">{focus_tags}</div>
                        </aside>
                    </section>

                    <section id="about">
                        <div class="section-head">
                            <div>
                                <p class="eyebrow">About</p>
                                <h2>Simple, thoughtful, and built to feel real.</h2>
                            </div>
                        </div>
                        <div class="card about-card">
                            <p class="body-copy">{escape(PORTFOLIO["about"])}</p>
                        </div>
                    </section>

                    <section id="projects">
                        <div class="section-head">
                            <div>
                                <p class="eyebrow">Selected Projects</p>
                                <h2>Placeholder work with an AI-first visual style.</h2>
                            </div>
                            <p>Swap these with your actual projects later.</p>
                        </div>
                        <div class="project-grid">
                            {projects}
                        </div>
                    </section>

                    <section id="experience">
                        <div class="section-head">
                            <div>
                                <p class="eyebrow">Experience</p>
                                <h2>1-2 sample roles to complete the story.</h2>
                            </div>
                            <p>These are editable placeholders inside the Python file.</p>
                        </div>
                        <div class="experience-grid">
                            {experience}
                        </div>
                    </section>
                </main>

                <footer>
                    <div class="footer-card">
                        <div>
                            <div class="code-note">portfolio.ready = true;</div>
                            <p>Replace the dummy text whenever you are ready with your exact content.</p>
                        </div>
                        <a class="button secondary" href="mailto:{email}">Email me</a>
                    </div>
                </footer>
            </div>
            <script>
                console.log("Portfolio loaded.");
            </script>
        </body>
        </html>
        """
    )


def export_static_site(output_dir: Path = ROOT) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_file = output_dir / "index.html"
    styles_file = output_dir / "styles.css"
    nojekyll_file = output_dir / ".nojekyll"

    index_file.write_text(build_page(), encoding="utf-8")
    styles_file.write_text(STYLES, encoding="utf-8")
    nojekyll_file.write_text("", encoding="utf-8")
    return index_file, styles_file, nojekyll_file


class PortfolioHandler(BaseHTTPRequestHandler):
    def _handle_request(self, include_body: bool) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/content":
            payload = json.dumps(content_payload()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if include_body:
                self.wfile.write(payload)
            return

        if parsed.path in {"/", "/index.html"}:
            page = build_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            if include_body:
                self.wfile.write(page)
            return

        if parsed.path == "/styles.css":
            styles = STYLES.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(styles)))
            self.end_headers()
            if include_body:
                self.wfile.write(styles)
            return

        if parsed.path == "/.nojekyll":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self.send_error(404, "Page not found")

    def do_GET(self) -> None:
        self._handle_request(include_body=True)

    def do_HEAD(self) -> None:
        self._handle_request(include_body=False)

    def log_message(self, format: str, *args: object) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    export_static_site()
    server = ThreadingHTTPServer((host, port), PortfolioHandler)
    print(f"Serving portfolio at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nShutting down server.")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or build a GitHub Pages-friendly portfolio site."
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Preview the portfolio locally.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    build_parser = subparsers.add_parser("build", help="Generate static files for GitHub Pages.")
    build_parser.add_argument("--output-dir", type=Path, default=ROOT)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.command == "build":
        index_file, styles_file, nojekyll_file = export_static_site(args.output_dir)
        print(f"Wrote {index_file}")
        print(f"Wrote {styles_file}")
        print(f"Wrote {nojekyll_file}")
    else:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8000)
        run(host=host, port=port)
