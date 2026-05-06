from __future__ import annotations

import argparse
import html
import json
import mimetypes
import re
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from textwrap import dedent
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
SITE_FILE = ROOT / "site.json"
PROFILES_DIR = ROOT / "profiles"
DEFAULT_PROFILE = "automation-engineer"


STYLES = dedent(
    """\
    :root {
        color-scheme: light;
        --bg: #eee7da;
        --surface: rgba(255, 249, 240, 0.78);
        --surface-strong: rgba(255, 249, 240, 0.92);
        --surface-muted: rgba(245, 236, 223, 0.84);
        --text: #18202b;
        --muted: #5b6674;
        --accent: #0f766e;
        --accent-strong: #0b5c56;
        --warm: #b66339;
        --warm-strong: #934d2c;
        --border: rgba(24, 32, 43, 0.12);
        --grid-line: rgba(24, 32, 43, 0.06);
        --shadow-soft: 0 28px 64px rgba(84, 59, 28, 0.12);
        --shadow-card: 0 16px 34px rgba(76, 56, 30, 0.08);
        --radius-xl: 34px;
        --radius-lg: 24px;
        --radius-md: 16px;
        --sans: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
        --display: "Fraunces", "Georgia", serif;
        --mono: "IBM Plex Mono", "SFMono-Regular", "Menlo", monospace;
    }

    :root[data-theme="dark"] {
        color-scheme: dark;
        --bg: #10161d;
        --surface: rgba(20, 27, 34, 0.8);
        --surface-strong: rgba(20, 27, 34, 0.94);
        --surface-muted: rgba(16, 22, 29, 0.9);
        --text: #edf2f7;
        --muted: #a0acb8;
        --accent: #82d8cb;
        --accent-strong: #b8f2e8;
        --warm: #efb48c;
        --warm-strong: #ffd0b3;
        --border: rgba(237, 242, 247, 0.12);
        --grid-line: rgba(237, 242, 247, 0.05);
        --shadow-soft: 0 28px 72px rgba(0, 0, 0, 0.36);
        --shadow-card: 0 18px 40px rgba(0, 0, 0, 0.28);
    }

    * {
        box-sizing: border-box;
    }

    html {
        scroll-behavior: smooth;
    }

    body {
        margin: 0;
        min-height: 100vh;
        background:
            radial-gradient(circle at 14% 10%, rgba(15, 118, 110, 0.12), transparent 28%),
            radial-gradient(circle at 84% 14%, rgba(182, 99, 57, 0.14), transparent 24%),
            var(--bg);
        color: var(--text);
        font-family: var(--sans);
        line-height: 1.68;
        transition: background-color 260ms ease, color 220ms ease;
        position: relative;
        overflow-x: hidden;
    }

    body::before {
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(var(--grid-line) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
        background-size: 72px 72px;
        mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.76), transparent 86%);
        pointer-events: none;
        z-index: -2;
    }

    body::after {
        content: "";
        position: fixed;
        width: 38vw;
        height: 38vw;
        min-width: 320px;
        min-height: 320px;
        right: -12vw;
        bottom: -16vw;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(15, 118, 110, 0.12), transparent 66%);
        filter: blur(12px);
        pointer-events: none;
        z-index: -1;
    }

    a {
        color: inherit;
        text-decoration: none;
    }

    button,
    input,
    textarea,
    select {
        font: inherit;
    }

    .shell {
        width: min(1180px, calc(100% - 40px));
        margin: 0 auto;
    }

    .topbar {
        position: sticky;
        top: 18px;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        margin-top: 20px;
        padding: 16px 18px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 999px;
        backdrop-filter: blur(18px);
        box-shadow: var(--shadow-card);
    }

    .topbar-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 0;
    }

    .brand-mark {
        width: 52px;
        height: 52px;
        border-radius: 18px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.18), rgba(182, 99, 57, 0.14));
        border: 1px solid var(--border);
        color: var(--text);
        font-family: var(--mono);
        font-size: 0.92rem;
        font-weight: 700;
        letter-spacing: 0.08em;
    }

    .brand-text {
        min-width: 0;
    }

    .brand-text strong,
    .theme-toggle__copy strong {
        display: block;
    }

    .brand-text strong {
        font-size: 0.98rem;
    }

    .brand-text span {
        display: block;
        color: var(--muted);
        font-size: 0.9rem;
    }

    .nav-links {
        display: flex;
        align-items: center;
        gap: 18px;
        flex-wrap: wrap;
    }

    .nav-links a {
        color: var(--muted);
        font-size: 0.92rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: color 180ms ease;
    }

    .nav-links a:hover,
    .nav-links a:focus-visible {
        color: var(--text);
    }

    .theme-toggle {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        min-width: 202px;
        padding: 8px 10px;
        border: 1px solid var(--border);
        border-radius: 999px;
        background: var(--surface-strong);
        color: var(--text);
        cursor: pointer;
        transition:
            transform 180ms ease,
            border-color 180ms ease,
            box-shadow 180ms ease;
    }

    .theme-toggle:hover,
    .theme-toggle:focus-visible {
        transform: translateY(-1px);
        border-color: rgba(15, 118, 110, 0.34);
        box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.08);
    }

    .theme-toggle__track {
        position: relative;
        flex: 0 0 58px;
        height: 34px;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--warm), var(--accent));
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
        overflow: hidden;
    }

    .theme-toggle__thumb {
        position: absolute;
        top: 4px;
        left: 4px;
        width: 26px;
        height: 26px;
        border-radius: 999px;
        background: var(--surface-strong);
        box-shadow: var(--shadow-card);
        transition: transform 220ms ease;
    }

    :root[data-theme="dark"] .theme-toggle__thumb {
        transform: translateX(24px);
    }

    .theme-toggle__copy {
        min-width: 0;
        text-align: left;
    }

    .theme-toggle__copy strong {
        font-size: 0.84rem;
        letter-spacing: 0.02em;
    }

    .theme-toggle__copy span {
        display: block;
        color: var(--muted);
        font-size: 0.74rem;
        line-height: 1.35;
    }

    main {
        padding: 54px 0 84px;
    }

    section + section {
        margin-top: 88px;
    }

    h1,
    h2,
    h3,
    p {
        margin: 0;
    }

    h1,
    h2,
    h3 {
        letter-spacing: -0.03em;
    }

    h1,
    h2 {
        font-family: var(--display);
        font-weight: 700;
        line-height: 0.98;
    }

    h1 {
        font-size: clamp(3.35rem, 8vw, 6.1rem);
        max-width: 11ch;
    }

    h2 {
        font-size: clamp(2rem, 4vw, 3.3rem);
        max-width: 12ch;
    }

    h3 {
        font-size: 1.22rem;
        line-height: 1.2;
    }

    .eyebrow {
        margin: 0 0 14px;
        color: var(--accent);
        font-family: var(--mono);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.8fr);
        gap: 28px;
        align-items: stretch;
    }

    .hero-copy,
    .hero-panel,
    .card {
        border: 1px solid var(--border);
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(18px);
    }

    .hero-copy {
        padding: 40px 42px 44px;
        border-radius: var(--radius-xl);
        background: linear-gradient(180deg, var(--surface-strong), rgba(255, 255, 255, 0.06));
        position: relative;
        overflow: hidden;
    }

    .hero-copy::before {
        content: "";
        position: absolute;
        inset: auto auto -80px -60px;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(15, 118, 110, 0.14), transparent 68%);
        pointer-events: none;
    }

    .hero-context {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }

    .context-pill,
    .tag-row li,
    .contact-links a {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.3);
        font-size: 0.82rem;
        font-weight: 600;
    }

    :root[data-theme="dark"] .context-pill,
    :root[data-theme="dark"] .tag-row li,
    :root[data-theme="dark"] .contact-links a {
        background: rgba(255, 255, 255, 0.03);
    }

    .context-pill {
        color: var(--muted);
        font-family: var(--mono);
    }

    .role {
        margin-top: 16px;
        color: var(--warm);
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .lead,
    .summary,
    .section-copy,
    .body-text,
    .card p,
    .card li,
    .detail-list p,
    .meta-row,
    .language-item,
    footer p {
        color: var(--muted);
    }

    .lead,
    .summary {
        max-width: 62ch;
        font-size: 1.02rem;
        line-height: 1.85;
    }

    .lead {
        margin-top: 22px;
    }

    .summary {
        margin-top: 14px;
    }

    .hero-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 14px;
        margin-top: 34px;
    }

    .button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 13px 20px;
        border-radius: 999px;
        border: 1px solid var(--border);
        font-weight: 700;
        letter-spacing: 0.01em;
        transition:
            transform 180ms ease,
            border-color 180ms ease,
            background-color 180ms ease,
            color 180ms ease,
            box-shadow 180ms ease;
    }

    .button:hover,
    .button:focus-visible {
        transform: translateY(-1px);
    }

    .button.primary {
        background: var(--text);
        border-color: var(--text);
        color: var(--bg);
    }

    .button.primary:hover,
    .button.primary:focus-visible {
        box-shadow: 0 12px 28px rgba(24, 32, 43, 0.14);
    }

    .button.secondary {
        background: transparent;
        color: var(--text);
    }

    .button.secondary:hover,
    .button.secondary:focus-visible {
        border-color: var(--warm);
        color: var(--warm);
    }

    .hero-panel {
        padding: 28px;
        border-radius: var(--radius-xl);
        background:
            linear-gradient(180deg, rgba(15, 118, 110, 0.14), transparent 52%),
            var(--surface-muted);
        display: grid;
        gap: 22px;
    }

    .panel-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
    }

    .panel-title {
        font-family: var(--display);
        font-size: 1.5rem;
        line-height: 1.12;
    }

    .panel-kicker {
        color: var(--muted);
        font-size: 0.92rem;
        max-width: 26ch;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.38);
        border: 1px solid var(--border);
        font-family: var(--mono);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        white-space: nowrap;
    }

    :root[data-theme="dark"] .status-pill {
        background: rgba(255, 255, 255, 0.04);
    }

    .status-pill::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--accent);
        box-shadow: 0 0 0 6px rgba(15, 118, 110, 0.12);
    }

    .signal-list,
    .clean-list,
    .skill-list,
    .tag-row {
        margin: 0;
        padding: 0;
        list-style: none;
    }

    .signal-list {
        display: grid;
        gap: 12px;
    }

    .signal-list li {
        padding: 14px 16px;
        border-radius: var(--radius-md);
        background: rgba(255, 255, 255, 0.34);
        border: 1px solid var(--border);
        color: var(--text);
        font-weight: 600;
        line-height: 1.5;
    }

    :root[data-theme="dark"] .signal-list li {
        background: rgba(255, 255, 255, 0.04);
    }

    .panel-foot {
        display: grid;
        gap: 12px;
        padding-top: 2px;
    }

    .panel-foot .body-text {
        line-height: 1.8;
    }

    .section-head {
        display: grid;
        gap: 12px;
        max-width: 660px;
        margin-bottom: 28px;
    }

    .section-copy {
        max-width: 62ch;
        line-height: 1.8;
    }

    .projects-grid,
    .card-grid,
    .split-grid {
        display: grid;
        gap: 24px;
    }

    .projects-grid {
        grid-template-columns: repeat(12, minmax(0, 1fr));
    }

    .project-card {
        grid-column: span 6;
    }

    .project-card--featured {
        grid-column: 1 / -1;
    }

    .project-card--featured .card-body {
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.95fr);
        gap: 28px;
        align-items: start;
    }

    .card {
        background: var(--surface);
        border-radius: var(--radius-lg);
        overflow: hidden;
        position: relative;
    }

    .card::before {
        content: "";
        position: absolute;
        inset: 0 auto auto 0;
        width: 100%;
        height: 6px;
        background: linear-gradient(90deg, var(--accent), rgba(182, 99, 57, 0.7));
        opacity: 0.7;
    }

    .card[data-tone="warm"]::before {
        background: linear-gradient(90deg, var(--warm), rgba(15, 118, 110, 0.7));
    }

    .card[data-tone="neutral"]::before {
        background: linear-gradient(90deg, rgba(91, 102, 116, 0.76), rgba(15, 118, 110, 0.76));
    }

    .card-body {
        padding: 30px;
    }

    .card-body.compact {
        padding: 24px;
    }

    .card-header {
        display: grid;
        gap: 10px;
        margin-bottom: 18px;
    }

    .card-header--project {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
    }

    .card-header.company-head {
        display: flex;
        align-items: flex-start;
        gap: 16px;
    }

    .company-copy {
        display: grid;
        gap: 10px;
        flex: 1;
        min-width: 0;
    }

    .company-logo-wrap {
        width: 72px;
        height: 72px;
        flex: 0 0 72px;
        display: grid;
        place-items: center;
        padding: 12px;
        border-radius: 20px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.32);
        box-shadow: var(--shadow-card);
        overflow: hidden;
    }

    .company-logo-link {
        display: block;
        border-radius: 20px;
        transition: transform 160ms ease, box-shadow 160ms ease;
    }

    .company-logo-link:hover,
    .company-logo-link:focus-visible {
        transform: translateY(-1px);
        box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.08);
    }

    :root[data-theme="dark"] .company-logo-wrap {
        background: rgba(255, 255, 255, 0.04);
    }

    .company-logo {
        display: block;
        width: 100%;
        height: auto;
        max-height: 40px;
        object-fit: contain;
    }

    .eyebrow-link {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--accent);
    }

    .eyebrow-link::after {
        content: "↗";
        font-size: 0.88em;
        line-height: 1;
    }

    .eyebrow-link:hover,
    .eyebrow-link:focus-visible {
        color: var(--accent-strong);
    }

    .meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px 12px;
        font-family: var(--mono);
        font-size: 0.78rem;
    }

    .meta-row span {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 11px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.22);
    }

    :root[data-theme="dark"] .meta-row span {
        background: rgba(255, 255, 255, 0.03);
    }

    .project-overview,
    .experience-overview {
        color: var(--text);
        font-size: 1rem;
        line-height: 1.8;
        margin-bottom: 18px;
    }

    .clean-list {
        display: grid;
        gap: 12px;
    }

    .clean-list li {
        position: relative;
        padding-left: 18px;
        line-height: 1.8;
    }

    .clean-list li::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0.82em;
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: var(--accent);
        transform: translateY(-50%);
    }

    .detail-list {
        display: grid;
        gap: 10px;
    }

    .detail-list p {
        line-height: 1.8;
    }

    .key {
        color: var(--text);
        font-weight: 700;
    }

    .tag-row,
    .contact-links {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .tag-row {
        margin-top: 22px;
    }

    .tag-row li {
        color: var(--text);
    }

    .project-links {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: flex-end;
    }

    .project-links a,
    .contact-links a {
        color: var(--text);
        transition:
            transform 160ms ease,
            border-color 160ms ease,
            color 160ms ease;
    }

    .project-links a {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 10px 14px;
        border-radius: 999px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.22);
        font-weight: 700;
    }

    :root[data-theme="dark"] .project-links a {
        background: rgba(255, 255, 255, 0.03);
    }

    .project-links a:hover,
    .project-links a:focus-visible,
    .contact-links a:hover,
    .contact-links a:focus-visible {
        transform: translateY(-1px);
        border-color: rgba(15, 118, 110, 0.4);
        color: var(--accent-strong);
    }

    .card-grid.three {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .skill-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .skill-list li {
        padding: 10px 13px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.28);
        border: 1px solid var(--border);
        line-height: 1.45;
    }

    :root[data-theme="dark"] .skill-list li {
        background: rgba(255, 255, 255, 0.03);
    }

    .skill-list .language-item {
        width: 100%;
    }

    .split-grid {
        grid-template-columns: minmax(0, 1.08fr) minmax(300px, 0.92fr);
        align-items: start;
    }

    .column {
        display: grid;
        gap: 24px;
        align-content: start;
    }

    .subhead {
        margin: 0;
        color: var(--text);
        font-size: 0.84rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .contact-card {
        max-width: 880px;
        background:
            linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(182, 99, 57, 0.1)),
            var(--surface);
    }

    footer {
        padding-bottom: 42px;
    }

    footer p {
        font-size: 0.9rem;
    }

    .js .reveal {
        opacity: 0;
        transform: translateY(22px);
        transition: opacity 360ms ease, transform 360ms ease;
    }

    .js .reveal.is-visible {
        opacity: 1;
        transform: translateY(0);
    }

    @media (max-width: 1080px) {
        .hero-grid,
        .project-card--featured .card-body,
        .split-grid {
            grid-template-columns: 1fr;
        }

        .project-card,
        .project-card--featured {
            grid-column: 1 / -1;
        }

        .card-grid.three {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 820px) {
        .topbar {
            align-items: flex-start;
            border-radius: 28px;
        }

        .topbar,
        .topbar-right {
            flex-direction: column;
        }

        .topbar-right {
            width: 100%;
            align-items: stretch;
        }

        .theme-toggle {
            width: 100%;
            min-width: 0;
        }
    }

    @media (max-width: 720px) {
        .shell {
            width: min(100% - 24px, 1180px);
        }

        main {
            padding-top: 38px;
        }

        section + section {
            margin-top: 72px;
        }

        .hero-copy,
        .hero-panel,
        .card-body {
            padding: 24px;
        }

        .hero-copy {
            border-radius: 26px;
        }

        h1 {
            font-size: clamp(2.8rem, 14vw, 4.2rem);
        }

        h2 {
            max-width: none;
        }

        .card-header--project {
            flex-direction: column;
        }

        .card-header.company-head {
            align-items: center;
        }

        .project-links {
            justify-content: flex-start;
        }

        .card-grid.three {
            grid-template-columns: 1fr;
        }

        .company-logo-wrap {
            width: 64px;
            height: 64px;
            flex-basis: 64px;
        }
    }
    """
)

INITIAL_THEME_SCRIPT = dedent(
    """\
    (() => {
        const root = document.documentElement;
        const storageKey = "portfolio-theme";

        root.classList.add("js");

        let storedTheme = null;
        try {
            storedTheme = localStorage.getItem(storageKey);
        } catch (error) {
            storedTheme = null;
        }

        const prefersDark =
            window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches;

        root.dataset.theme =
            storedTheme === "light" || storedTheme === "dark"
                ? storedTheme
                : prefersDark
                  ? "dark"
                  : "light";
    })();
    """
).strip()

PAGE_SCRIPT = dedent(
    """\
    (() => {
        const root = document.documentElement;
        const button = document.querySelector("[data-theme-toggle]");
        const themeMode = document.querySelector("[data-theme-mode]");
        const themeHint = document.querySelector("[data-theme-hint]");
        const storageKey = "portfolio-theme";
        const mediaQuery =
            window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)");

        const readStoredTheme = () => {
            try {
                return localStorage.getItem(storageKey);
            } catch (error) {
                return null;
            }
        };

        const applyTheme = (theme, persist = false) => {
            const resolvedTheme = theme === "dark" ? "dark" : "light";
            root.dataset.theme = resolvedTheme;
            button?.setAttribute("aria-pressed", String(resolvedTheme === "dark"));

            if (themeMode) {
                themeMode.textContent =
                    resolvedTheme === "dark" ? "Night shift" : "Studio light";
            }

            if (themeHint) {
                themeHint.textContent =
                    resolvedTheme === "dark"
                        ? "Switch to the daylight palette"
                        : "Switch to the after-hours palette";
            }

            if (persist) {
                try {
                    localStorage.setItem(storageKey, resolvedTheme);
                } catch (error) {
                    // Keep the control usable even if storage is blocked.
                }
            }
        };

        applyTheme(root.dataset.theme || "light");

        button?.addEventListener("click", () => {
            const nextTheme = root.dataset.theme === "dark" ? "light" : "dark";
            applyTheme(nextTheme, true);
        });

        if (mediaQuery) {
            const syncWithSystem = (event) => {
                if (!readStoredTheme()) {
                    applyTheme(event.matches ? "dark" : "light");
                }
            };

            if (typeof mediaQuery.addEventListener === "function") {
                mediaQuery.addEventListener("change", syncWithSystem);
            } else if (typeof mediaQuery.addListener === "function") {
                mediaQuery.addListener(syncWithSystem);
            }
        }

        if ("IntersectionObserver" in window) {
            const observer = new IntersectionObserver(
                (entries) => {
                    for (const entry of entries) {
                        if (entry.isIntersecting) {
                            entry.target.classList.add("is-visible");
                            observer.unobserve(entry.target);
                        }
                    }
                },
                { threshold: 0.14 }
            );

            for (const element of document.querySelectorAll(".reveal")) {
                observer.observe(element);
            }
        } else {
            for (const element of document.querySelectorAll(".reveal")) {
                element.classList.add("is-visible");
            }
        }
    })();
    """
).strip()


BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def load_site_config() -> dict[str, str]:
    if not SITE_FILE.exists():
        return {"active_profile": DEFAULT_PROFILE}
    with SITE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_site_config(config: dict[str, str]) -> None:
    SITE_FILE.write_text(f"{json.dumps(config, indent=2)}\n", encoding="utf-8")


def get_profile_path(profile_name: str) -> Path:
    return PROFILES_DIR / f"{profile_name}.json"


def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(path.stem for path in PROFILES_DIR.glob("*.json"))


def expect_dict(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{field_name} must be an object.")
    return value


def expect_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list.")
    return value


def expect_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    return value


def validate_string_list(value: object, field_name: str) -> list[str]:
    items = expect_list(value, field_name)
    validated: list[str] = []

    for index, item in enumerate(items):
        validated.append(expect_string(item, f"{field_name}[{index}]"))

    return validated


def validate_object_list(value: object, field_name: str) -> list[dict[str, object]]:
    items = expect_list(value, field_name)
    validated: list[dict[str, object]] = []

    for index, item in enumerate(items):
        validated.append(expect_dict(item, f"{field_name}[{index}]"))

    return validated


def validate_content(content: object) -> dict[str, object]:
    data = expect_dict(content, "content")

    profile = expect_dict(data.get("profile"), "profile")
    for field in ("name", "role", "location", "status", "intro", "summary"):
        expect_string(profile.get(field), f"profile.{field}")
    validate_string_list(profile.get("hero_highlights"), "profile.hero_highlights")

    contact = expect_dict(data.get("contact"), "contact")
    expect_string(contact.get("note"), "contact.note")
    for index, link in enumerate(validate_object_list(contact.get("links"), "contact.links")):
        expect_string(link.get("label"), f"contact.links[{index}].label")
        expect_string(link.get("url"), f"contact.links[{index}].url")

    for index, group in enumerate(validate_object_list(data.get("skill_groups"), "skill_groups")):
        expect_string(group.get("title"), f"skill_groups[{index}].title")
        validate_string_list(group.get("items"), f"skill_groups[{index}].items")

    for index, language in enumerate(validate_object_list(data.get("languages"), "languages")):
        for field in ("name", "level", "details"):
            expect_string(language.get(field), f"languages[{index}].{field}")

    for index, project in enumerate(validate_object_list(data.get("projects"), "projects")):
        for field in ("title", "overview"):
            expect_string(project.get(field), f"projects[{index}].{field}")
        for field in ("github_url", "demo_url"):
            expect_string(project.get(field, ""), f"projects[{index}].{field}")
        validate_string_list(project.get("highlights"), f"projects[{index}].highlights")
        validate_string_list(project.get("stack"), f"projects[{index}].stack")

    for index, item in enumerate(validate_object_list(data.get("experience"), "experience")):
        for field in ("role", "company", "period", "location", "client", "overview"):
            expect_string(item.get(field, ""), f"experience[{index}].{field}")
        for field in ("logo_path", "logo_alt", "organization_url"):
            expect_string(item.get(field, ""), f"experience[{index}].{field}")
        validate_string_list(item.get("highlights"), f"experience[{index}].highlights")

    for index, item in enumerate(validate_object_list(data.get("education"), "education")):
        for field in ("degree", "institution", "period", "location"):
            expect_string(item.get(field), f"education[{index}].{field}")
        for field in ("logo_path", "logo_alt", "organization_url"):
            expect_string(item.get(field, ""), f"education[{index}].{field}")
        validate_string_list(item.get("details"), f"education[{index}].details")

    for index, item in enumerate(validate_object_list(data.get("certifications"), "certifications")):
        for field in ("title", "issuer", "period"):
            expect_string(item.get(field), f"certifications[{index}].{field}")
        details = item.get("details")
        if isinstance(details, str):
            expect_string(details, f"certifications[{index}].details")
        else:
            validate_string_list(details, f"certifications[{index}].details")

    for index, item in enumerate(validate_object_list(data.get("volunteering"), "volunteering")):
        for field in ("role", "organization", "period"):
            expect_string(item.get(field), f"volunteering[{index}].{field}")
        validate_string_list(item.get("details"), f"volunteering[{index}].details")

    return data


def load_content(profile_name: str | None = None) -> tuple[str, dict[str, object]]:
    active_profile = profile_name or load_site_config().get("active_profile", DEFAULT_PROFILE)
    profile_path = get_profile_path(active_profile)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    with profile_path.open("r", encoding="utf-8") as file:
        return active_profile, validate_content(json.load(file))


def set_active_profile(profile_name: str) -> None:
    profile_path = get_profile_path(profile_name)
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")
    save_site_config({"active_profile": profile_name})


def clone_profile(new_profile: str, source_profile: str = DEFAULT_PROFILE) -> Path:
    source_path = get_profile_path(source_profile)
    destination_path = get_profile_path(new_profile)
    if not source_path.exists():
        raise FileNotFoundError(f"Source profile not found: {source_path}")
    if destination_path.exists():
        raise FileExistsError(f"Profile already exists: {destination_path}")
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    return destination_path


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def format_text(text: str) -> str:
    parts: list[str] = []
    last_index = 0

    for match in BOLD_PATTERN.finditer(text):
        start, end = match.span()
        parts.append(escape(text[last_index:start]))
        parts.append(f'<strong class="key">{escape(match.group(1))}</strong>')
        last_index = end

    parts.append(escape(text[last_index:]))
    return "".join(parts)


def initials(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "AG"


def render_clean_list(items: list[str]) -> str:
    rendered = "".join(f"<li>{format_text(item)}</li>" for item in items)
    return f'<ul class="clean-list">{rendered}</ul>'


def render_skill_list(items: list[str]) -> str:
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="skill-list">{rendered}</ul>'


def render_tag_row(items: list[str]) -> str:
    if not items:
        return ""
    rendered = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f'<ul class="tag-row">{rendered}</ul>'


def render_eyebrow(value: str, link_url: str = "") -> str:
    if link_url:
        return (
            f'<a class="eyebrow eyebrow-link" href="{escape(link_url)}" '
            f'target="_blank" rel="noreferrer">{escape(value)}</a>'
        )
    return f'<p class="eyebrow">{escape(value)}</p>'


def render_meta_row(parts: list[str]) -> str:
    filtered = [escape(part) for part in parts if part]
    if not filtered:
        return ""
    joined = "".join(f"<span>{part}</span>" for part in filtered)
    return f'<div class="meta-row">{joined}</div>'


def render_projects(projects: list[dict[str, object]]) -> str:
    cards = []
    tones = ("accent", "warm", "neutral")

    for index, project in enumerate(projects):
        card_classes = "card project-card reveal"
        if index == 0:
            card_classes += " project-card--featured"

        links = []
        if project.get("github_url"):
            links.append(
                f'<a href="{escape(project["github_url"])}" target="_blank" rel="noreferrer">GitHub</a>'
            )
        if project.get("demo_url"):
            links.append(
                f'<a href="{escape(project["demo_url"])}" target="_blank" rel="noreferrer">Live Demo</a>'
            )
        link_block = f'<div class="project-links">{"".join(links)}</div>' if links else ""

        cards.append(
            f"""
            <article class="{card_classes}" data-tone="{tones[index % len(tones)]}">
                <div class="card-body">
                    <div class="project-summary">
                        <div class="card-header card-header--project">
                            <div>
                                <p class="eyebrow">Project {index + 1:02d}</p>
                                <h3>{escape(project["title"])}</h3>
                            </div>
                            {link_block}
                        </div>
                        <p class="project-overview">{format_text(project["overview"])}</p>
                        {render_tag_row(project["stack"])}
                    </div>
                    <div class="project-details">
                        {render_clean_list(project["highlights"])}
                    </div>
                </div>
            </article>
            """
        )
    return "".join(cards)


def render_experience(items: list[dict[str, object]]) -> str:
    cards = []
    tones = ("neutral", "accent", "warm")

    for index, item in enumerate(items):
        client = item.get("client", "")
        client_part = f"Client: {client}" if client else ""
        organization_url = item.get("organization_url", "")
        logo_block = ""
        logo_path = item.get("logo_path", "")
        if logo_path:
            logo_alt = item.get("logo_alt") or f'{item["company"]} logo'
            logo_image = (
                f'<div class="company-logo-wrap">'
                f'<img class="company-logo" src="{escape(logo_path)}" '
                f'alt="{escape(logo_alt)}" loading="lazy" />'
                f"</div>"
            )
            if organization_url:
                logo_block = (
                    f'<a class="company-logo-link" href="{escape(organization_url)}" '
                    f'target="_blank" rel="noreferrer" '
                    f'aria-label="Open {escape(item["company"])} website">'
                    f"{logo_image}</a>"
                )
            else:
                logo_block = logo_image
        cards.append(
            f"""
            <article class="card reveal" data-tone="{tones[index % len(tones)]}">
                <div class="card-body">
                    <div class="card-header company-head">
                        {logo_block}
                        <div class="company-copy">
                            {render_eyebrow(item["company"], organization_url)}
                            <h3>{escape(item["role"])}</h3>
                            {render_meta_row([item["period"], item["location"], client_part])}
                        </div>
                    </div>
                    <p class="experience-overview">{format_text(item["overview"])}</p>
                    {render_clean_list(item["highlights"])}
                </div>
            </article>
            """
        )
    return "".join(cards)


def render_education(items: list[dict[str, object]]) -> str:
    cards = []
    tones = ("accent", "neutral")

    for index, item in enumerate(items):
        organization_url = item.get("organization_url", "")
        logo_block = ""
        logo_path = item.get("logo_path", "")
        if logo_path:
            logo_alt = item.get("logo_alt") or f'{item["institution"]} logo'
            logo_image = (
                f'<div class="company-logo-wrap">'
                f'<img class="company-logo" src="{escape(logo_path)}" '
                f'alt="{escape(logo_alt)}" loading="lazy" />'
                f"</div>"
            )
            if organization_url:
                logo_block = (
                    f'<a class="company-logo-link" href="{escape(organization_url)}" '
                    f'target="_blank" rel="noreferrer" '
                    f'aria-label="Open {escape(item["institution"])} website">'
                    f"{logo_image}</a>"
                )
            else:
                logo_block = logo_image
        details = "".join(f"<p>{format_text(detail)}</p>" for detail in item["details"])
        cards.append(
            f"""
            <article class="card reveal" data-tone="{tones[index % len(tones)]}">
                <div class="card-body compact">
                    <div class="card-header company-head">
                        {logo_block}
                        <div class="company-copy">
                            {render_eyebrow(item["institution"], organization_url)}
                            <h3>{escape(item["degree"])}</h3>
                            {render_meta_row([item["period"], item["location"]])}
                        </div>
                    </div>
                    <div class="detail-list">{details}</div>
                </div>
            </article>
            """
        )
    return "".join(cards)


def render_certifications(items: list[dict[str, object]]) -> str:
    cards = []
    tones = ("warm", "neutral", "accent")

    for index, item in enumerate(items):
        details = item.get("details", [])
        detail_block = render_clean_list(details) if isinstance(details, list) else f"<p>{format_text(details)}</p>"
        cards.append(
            f"""
            <article class="card reveal" data-tone="{tones[index % len(tones)]}">
                <div class="card-body compact">
                    <div class="card-header">
                        <p class="eyebrow">{escape(item["issuer"])}</p>
                        <h3>{escape(item["title"])}</h3>
                        {render_meta_row([item["period"]])}
                    </div>
                    {detail_block}
                </div>
            </article>
            """
        )
    return "".join(cards)


def render_volunteering(items: list[dict[str, object]]) -> str:
    cards = []
    tones = ("accent", "warm")

    for index, item in enumerate(items):
        cards.append(
            f"""
            <article class="card reveal" data-tone="{tones[index % len(tones)]}">
                <div class="card-body compact">
                    <div class="card-header">
                        <p class="eyebrow">{escape(item["organization"])}</p>
                        <h3>{escape(item["role"])}</h3>
                        {render_meta_row([item["period"]])}
                    </div>
                    {render_clean_list(item["details"])}
                </div>
            </article>
            """
        )
    return "".join(cards)


def render_skills(groups: list[dict[str, object]], languages: list[dict[str, object]]) -> str:
    cards = []
    tones = ("accent", "neutral", "warm")

    for index, group in enumerate(groups):
        cards.append(
            f"""
            <article class="card reveal" data-tone="{tones[index % len(tones)]}">
                <div class="card-body compact">
                    <div class="card-header">
                        <p class="eyebrow">Skills</p>
                        <h3>{escape(group["title"])}</h3>
                    </div>
                    {render_skill_list(group["items"])}
                </div>
            </article>
            """
        )

    language_items = "".join(
        f'<li class="language-item"><strong class="key">{escape(item["name"])} ({escape(item["level"])})</strong>: {format_text(item["details"])}</li>'
        for item in languages
    )
    cards.append(
        f"""
        <article class="card reveal" data-tone="warm">
            <div class="card-body compact">
                <div class="card-header">
                    <p class="eyebrow">Languages</p>
                    <h3>Language Skills</h3>
                </div>
                <ul class="skill-list">{language_items}</ul>
            </div>
        </article>
        """
    )

    return "".join(cards)


def render_contact_links(links: list[dict[str, str]]) -> str:
    if not links:
        return ""
    rendered = "".join(
        f'<a href="{escape(link["url"])}" target="_blank" rel="noreferrer">{escape(link["label"])}</a>'
        for link in links
    )
    return f'<div class="contact-links">{rendered}</div>'


def build_page(profile_name: str | None = None) -> str:
    _, content = load_content(profile_name)
    profile = content["profile"]
    contact_links = render_contact_links(content["contact"]["links"])
    projects = render_projects(content["projects"])
    skills = render_skills(content["skill_groups"], content["languages"])
    experience = render_experience(content["experience"])
    education = render_education(content["education"])
    certifications = render_certifications(content["certifications"])
    volunteering = render_volunteering(content["volunteering"])
    hero_items = "".join(f"<li>{escape(item)}</li>" for item in profile["hero_highlights"])

    return dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>{escape(profile["name"])} | Portfolio</title>
            <meta
                name="description"
                content="Systems and automation engineering portfolio."
            />
            <script>
                {INITIAL_THEME_SCRIPT}
            </script>
            <link rel="preconnect" href="https://fonts.googleapis.com" />
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
            <link
                href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@500;700&family=Manrope:wght@400;500;600;700;800&display=swap"
                rel="stylesheet"
            />
            <link rel="stylesheet" href="styles.css" />
        </head>
        <body>
            <div class="shell">
                <header class="topbar">
                    <a class="brand" href="#top">
                        <div class="brand-mark">{initials(profile["name"])}</div>
                        <div class="brand-text">
                            <strong>{escape(profile["name"])}</strong>
                            <span>{escape(profile["role"])}</span>
                        </div>
                    </a>
                    <div class="topbar-right">
                        <nav class="nav-links">
                            <a href="#projects">Projects</a>
                            <a href="#skills">Skills</a>
                            <a href="#experience">Experience</a>
                            <a href="#contact">Contact</a>
                        </nav>
                        <button
                            type="button"
                            class="theme-toggle"
                            aria-label="Toggle color theme"
                            aria-pressed="false"
                            data-theme-toggle
                        >
                            <span class="theme-toggle__track" aria-hidden="true">
                                <span class="theme-toggle__thumb"></span>
                            </span>
                            <span class="theme-toggle__copy">
                                <strong data-theme-mode>Studio light</strong>
                                <span data-theme-hint>Switch to the after-hours palette</span>
                            </span>
                        </button>
                    </div>
                </header>

                <main>
                    <section class="hero-grid" id="top">
                        <div class="hero-copy reveal">
                            <div class="hero-context">
                                <span class="context-pill">{escape(profile["location"])}</span>
                                <span class="context-pill">{escape(profile["status"])}</span>
                            </div>
                            <p class="eyebrow">Systems Portfolio</p>
                            <h1>{escape(profile["name"])}</h1>
                            <p class="role">{escape(profile["role"])}</p>
                            <p class="lead">{format_text(profile["intro"])}</p>
                            <p class="summary">{format_text(profile["summary"])}</p>
                            <div class="hero-actions">
                                <a class="button primary" href="#projects">See selected work</a>
                                <a class="button secondary" href="#contact">Start a conversation</a>
                            </div>
                        </div>

                        <aside class="hero-panel reveal" aria-label="Profile highlights">
                            <div class="panel-head">
                                <div>
                                    <p class="eyebrow">Current Signal</p>
                                    <p class="panel-title">Engineering work shaped by field constraints, not just clean demos.</p>
                                </div>
                                <span class="status-pill">Systems + Robotics</span>
                            </div>
                            <ul class="signal-list">{hero_items}</ul>
                            <div class="panel-foot">
                                <p class="body-text">{escape(profile["location"])} | {escape(profile["status"])}</p>
                                <p class="body-text">The through-line is practical automation: diagnostics, industrial connectivity, embedded control, and robotics with measurable outcomes.</p>
                            </div>
                        </aside>
                    </section>

                    <section id="projects">
                        <div class="section-head reveal">
                            <p class="eyebrow">Selected Work</p>
                            <h2>Projects that connect hardware, data, and operations.</h2>
                            <p class="section-copy">A compact set of builds across robotics, machine learning, embedded systems, and energy-aware control.</p>
                        </div>
                        <div class="projects-grid">
                            {projects}
                        </div>
                    </section>

                    <section id="skills">
                        <div class="section-head reveal">
                            <p class="eyebrow">Skills</p>
                            <h2>Tools, working habits, and language range.</h2>
                            <p class="section-copy">The technical stack is broad, but the pattern stays consistent: learn the system quickly, isolate the constraint, and ship the fix.</p>
                        </div>
                        <div class="card-grid three">
                            {skills}
                        </div>
                    </section>

                    <section id="experience">
                        <div class="section-head reveal">
                            <p class="eyebrow">Experience</p>
                            <h2>Recent roles, study, and the systems behind them.</h2>
                            <p class="section-copy">{escape(profile["location"])} | {escape(profile["status"])}</p>
                        </div>
                        <div class="split-grid">
                            <div class="column">
                                <p class="subhead">Work Experience</p>
                                {experience}
                            </div>
                            <div class="column">
                                <p class="subhead">Education</p>
                                {education}
                                <p class="subhead">Achievements & Certifications</p>
                                {certifications}
                                <p class="subhead">Volunteering</p>
                                {volunteering}
                            </div>
                        </div>
                    </section>

                    <section id="contact">
                        <div class="card contact-card reveal">
                            <div class="card-body">
                                <div class="card-header">
                                    <p class="eyebrow">Contact</p>
                                    <h2>Start a conversation.</h2>
                                </div>
                                <p class="body-text">{format_text(content["contact"]["note"])}</p>
                                {contact_links}
                            </div>
                        </div>
                    </section>
                </main>

                <footer>
                    <p>{escape(profile["name"])} | {escape(profile["role"])} | {escape(profile["location"])}</p>
                </footer>
            </div>
            <script>
                {PAGE_SCRIPT}
            </script>
        </body>
        </html>
        """
    )


def content_payload(profile_name: str | None = None) -> dict[str, object]:
    active_profile, content = load_content(profile_name)
    return {
        "active_profile": active_profile,
        "available_profiles": list_profiles(),
        "content": content,
    }


def export_static_site(
    output_dir: Path = ROOT, profile_name: str | None = None
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    index_file = output_dir / "index.html"
    styles_file = output_dir / "styles.css"
    nojekyll_file = output_dir / ".nojekyll"
    source_assets_dir = ROOT / "assets"
    target_assets_dir = output_dir / "assets"

    index_file.write_text(build_page(profile_name), encoding="utf-8")
    styles_file.write_text(STYLES, encoding="utf-8")
    nojekyll_file.write_text("", encoding="utf-8")

    if source_assets_dir.exists() and source_assets_dir.resolve() != target_assets_dir.resolve():
        shutil.copytree(source_assets_dir, target_assets_dir, dirs_exist_ok=True)

    return index_file, styles_file, nojekyll_file


class PortfolioHandler(BaseHTTPRequestHandler):
    profile_name: str | None = None

    def _handle_request(self, include_body: bool) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/content":
            payload = json.dumps(content_payload(self.profile_name)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if include_body:
                self.wfile.write(payload)
            return

        if parsed.path in {"/", "/index.html"}:
            page = build_page(self.profile_name).encode("utf-8")
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

        if parsed.path.startswith("/assets/"):
            asset_path = (ROOT / parsed.path.lstrip("/")).resolve()
            if asset_path.is_file() and asset_path.is_relative_to(ROOT):
                payload = asset_path.read_bytes()
                content_type, _ = mimetypes.guess_type(asset_path.name)
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    f"{content_type or 'application/octet-stream'}; charset=utf-8"
                    if content_type == "image/svg+xml"
                    else content_type or "application/octet-stream",
                )
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if include_body:
                    self.wfile.write(payload)
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


def run(host: str = "127.0.0.1", port: int = 8000, profile_name: str | None = None) -> None:
    export_static_site(profile_name=profile_name)
    PortfolioHandler.profile_name = profile_name
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
    serve_parser.add_argument("--profile", default=None)

    build_parser = subparsers.add_parser("build", help="Generate static files for GitHub Pages.")
    build_parser.add_argument("--output-dir", type=Path, default=ROOT)
    build_parser.add_argument("--profile", default=None)

    subparsers.add_parser("list-profiles", help="List available portfolio profiles.")

    use_parser = subparsers.add_parser("use-profile", help="Set the active profile in site.json.")
    use_parser.add_argument("profile")

    new_parser = subparsers.add_parser("new-profile", help="Clone a new profile from an existing one.")
    new_parser.add_argument("profile")
    new_parser.add_argument("--from-profile", default=DEFAULT_PROFILE)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.command == "build":
        index_file, styles_file, nojekyll_file = export_static_site(
            args.output_dir, args.profile
        )
        print(f"Wrote {index_file}")
        print(f"Wrote {styles_file}")
        print(f"Wrote {nojekyll_file}")
    elif args.command == "list-profiles":
        for profile in list_profiles():
            print(profile)
    elif args.command == "use-profile":
        set_active_profile(args.profile)
        print(f"Active profile set to {args.profile}")
    elif args.command == "new-profile":
        destination = clone_profile(args.profile, args.from_profile)
        print(f"Created {destination}")
    else:
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8000)
        profile_name = getattr(args, "profile", None)
        run(host=host, port=port, profile_name=profile_name)
