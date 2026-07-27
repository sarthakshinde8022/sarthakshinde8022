# Setting this up on your GitHub profile

## 1. Create the magic repo
GitHub renders the README of a repo whose name matches your username at
the top of your profile page.

```
gh repo create sarthakshinde8022 --public --clone
cd sarthakshinde8022
# copy every file from this folder into the new repo folder
```

(If you don't use the `gh` CLI: create an empty public repo named
exactly `<your-username>` on github.com, then `git clone` it and copy
these files in.)

## 2. Install the toolchain
```
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
```
`rembg`'s first run downloads a background-removal model (~176 MB), so
that step takes a minute the first time only.

## 3. Generate the ASCII portrait (one-time, redo only if you change photos)
```
python scripts/prep_photo.py your-photo.jpg
python scripts/make_ascii_svg.py
```
Open `ascii-portrait.svg` in a browser to check it. If the portrait
looks too dark/blobby, the photo probably has flat, even lighting —
try one with more directional light and contrast on the face.

## 4. Edit and generate the info card
Open `scripts/make_info_card.py` and edit the `ROWS` list at the top —
that's the only thing you should need to touch. Then:
```
python scripts/make_info_card.py
```

## 5. Generate the live heatmap (also what the daily workflow runs)
```
python scripts/fetch_contributions.py sarthakshinde8022
python scripts/render_heatmap_svg.py
```

## 6. Push
```
git add .
git commit -m "profile: animated terminal README"
git push
```

## 7. Turn on the daily refresh
The workflow at `.github/workflows/update-profile-art.yml` re-scrapes
and re-renders `contrib-heatmap.svg` every day at ~06:17 UTC and
commits it back automatically — the portrait and info card stay static
since they only need to change when your photo or details do.

One easy-to-miss gotcha: GitHub repos default their Actions token to
**read-only**. If the workflow's auto-commit step fails with a
permissions error, go to **Settings → Actions → General → Workflow
permissions** and switch it to **Read and write permissions**.

Trigger it once by hand to confirm: **Actions tab → Update profile art
→ Run workflow**.

## What's committed vs. what's gitignored
`source-photo.*` and `source-prepped.png` are gitignored — they're
personal working files, not needed once `ascii-portrait.svg` exists.
Everything else (the three SVGs, `data/contributions.json`, scripts,
workflow, README) is meant to be committed.
