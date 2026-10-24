# Publication checklist — prepared only

ATLAS V7.1 RC1 is frozen. The owner reports the complete 134-test + V6/V7 +
Streamlit browser preflight passed. No remote repository, push, CI dispatch or
hosting has been performed. All steps below are instructions for a later explicit
publication decision, not actions already taken.

## Ready locally

- [x] Financial models, UI, tests, dependencies and static snapshot frozen by SHA-256.
- [x] Complete preflight passed in the owner's normal Mac Terminal.
- [x] Public demo is exact seeded synthetic data; only index.html and .nojekyll.
- [x] MIT project license selected by owner; third-party notices retained.
- [x] README screenshots, methodology, limitations and interview materials updated.
- [x] Clean source candidate excludes work/, caches, private/provider downloads,
  old reports with local paths and redundant generated example exports.
- [ ] Explicit authorization to create/push a PUBLIC repository and publish Pages.
- [ ] After publication: inspect the actual hosted URL and retain the commit/result.

## Create the GitHub repository — after authorization

Use the audited clean candidate folder delivered with this release, not the outer
Codex workspace or your separate personal portfolio website. If copying elsewhere,
copy only that candidate. Replace placeholders before running commands.

1. Sign in to GitHub on the existing free account. Choose **New repository**.
   Name it **atlas-portfolio-risk**, choose **Public**, and leave README, license
   and .gitignore initialization unchecked (all three are supplied locally).
   Click **Create repository**. This makes the repository public.
2. In Terminal, change to the clean candidate root and verify its freeze:

   ```bash
   cd /path/to/atlas-portfolio-risk
   shasum -a 256 -c RELEASE_FREEZE_SHA256.txt
   shasum -a 256 -c MANIFEST_SHA256.txt
   ```

3. Initialize/review locally. These instructions assume the clean candidate has no
   .git directory; do not reinitialize or force-push an unrelated repository.

   ```bash
   git init -b main
   git add .
   git diff --cached --stat
   git status --short
   git commit -m "Prepare ATLAS V7.1 release candidate"
   ```

   Review the staged list before committing: there must be no work/, credentials,
   provider records, private CSVs, caches or personal website files.
4. Use the exact HTTPS URL shown by GitHub (replace YOUR_GITHUB_USERNAME):

   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/atlas-portfolio-risk.git
   git remote -v
   git push -u origin main
   ```

   Authenticate using GitHub's supported browser/credential flow. Do not put tokens
   in commands/files. This push publishes the source and triggers the read-only,
   public-only validation workflow. Do not buy minutes, a plan or a domain.

## Publish the free static Pages demo — after authorization

1. Repository → **Settings → Pages**.
2. Under Build and deployment, Source → **Deploy from a branch**.
3. Choose **main** and **/docs**, then **Save**. This is the hosting action.
4. Wait for the Pages build/deployment to complete. Open the URL shown in Settings;
   normally `https://YOUR_GITHUB_USERNAME.github.io/atlas-portfolio-risk/`.
5. Confirm the synthetic label/date range, all five panels, chart rendering,
   scenario presets/custom controls, invalid-input behavior, CSV/JSON downloads,
   keyboard navigation and 390px layout on the ACTUAL hosted URL. Check the console.
6. Add the verified Pages URL to GitHub About and the README, then commit/push that
   documentation update only after its content is reviewed. Add the same verified
   URL to LinkedIn Featured if desired. Do not claim an untested URL is live.

GitHub Free supports Pages for public repositories; use the default github.io URL.
No paid service or custom domain is needed. Pages serves the frozen standalone
synthetic demo only; it cannot run app.py or provide Streamlit analyst approval.
The HTML contains its chart runtime and uses relative/no remote data dependencies.
The public audit rejects extra docs files. Keep notices in the source repository
and preserve the embedded Phosphor/Plotly notices in the HTML.

## Optional later Streamlit deployment — separate decision

Streamlit hosting is not needed for the free static demo or this RC. If separately
authorized, inspect current Community Cloud free availability, select this approved
repository and app.py with Python 3.12, and install requirements.txt only. Keep
Synthetic demo as the public default. Stop if payment/trial/upgrade is requested.
Do not add provider credentials, private uploads or licensed data to the public
repository. Approval is session-local, with no enterprise identity store. A hosted
app needs its own E2E/privacy review; no hosted Streamlit pass is claimed here.

## Reference instructions (checked 24 October 2026)

- [GitHub: import local code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
- [GitHub: configure Pages source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub: Pages availability](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
