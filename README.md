# Portfolio

This project contains a simple portfolio site that is authored in `website.py` and exported as static files for GitHub Pages.

## Local preview

```bash
python3 website.py
```

Open `http://127.0.0.1:8000`.

## Build static files

```bash
python3 website.py build
```

This writes:

- `index.html`
- `styles.css`
- `.nojekyll`

## Publish on GitHub Pages

1. Create a new GitHub repository.
2. Push this folder to the `main` branch.
3. In the repository on GitHub, open `Settings` -> `Pages`.
4. Set the publishing source to `Deploy from a branch`.
5. Select branch `main` and folder `/ (root)`.

After that, GitHub Pages will publish the static files from the repository root.

## Editing content

Change the placeholder text in `website.py`, then run:

```bash
python3 website.py build
```

Commit and push the updated files to republish the site.
