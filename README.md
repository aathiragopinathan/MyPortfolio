# Portfolio

This project contains a portfolio site that is rendered by `website.py` and can be deployed to GitHub Pages.

## Edit content

The easiest setup now is:

- `site.json` chooses which profile is active.
- `profiles/*.json` stores each portfolio version.
- `profiles/template.json` is the copyable starting point for a new profile.

Common workflow:

1. Copy or clone a profile.
2. Paste or edit the content inside that profile JSON file.
3. Switch the active profile.
4. Rebuild the site.

Useful commands:

```bash
python3 website.py list-profiles
python3 website.py new-profile ml-engineer --from-profile template
python3 website.py use-profile ml-engineer
python3 website.py build
```

You can also preview a specific profile without switching the active one:

```bash
python3 website.py serve --profile automation-engineer
python3 website.py build --profile automation-engineer
```

Inside any profile file:

- Update your profile, projects, skills, experience, education, certifications, volunteering, and contact details.
- Use `**bold text**` inside any sentence if you want a keyword label to stand out.
- Keep the JSON structure the same and only replace the values.

## Local preview

```bash
python3 website.py
```

Open `http://127.0.0.1:8000`.

## Build static files locally

```bash
python3 website.py build
```

This writes:

- `index.html`
- `styles.css`
- `.nojekyll`

## Publish on GitHub Pages

This repo now includes `.github/workflows/deploy-pages.yml`, so GitHub can build and publish the site automatically.

Use this setup:

1. Push this folder to the `main` branch of your GitHub repository.
2. In the repository on GitHub, open `Settings` -> `Pages`.
3. Set the source to `GitHub Actions`.
4. Wait for the `Deploy Portfolio` workflow to finish.

For this repository, the site URL will be:

```text
https://aathiragopinathan.github.io/MyPortfolio/
```

After that, the website stays online without running the Python server locally.

## Editing content

Change your content in `profiles/<profile-name>.json`, commit, and push.

If you want to preview or export the site before pushing, you can still run:

```bash
python3 website.py build
```

GitHub Actions will rebuild and republish the site on each push to `main`.
