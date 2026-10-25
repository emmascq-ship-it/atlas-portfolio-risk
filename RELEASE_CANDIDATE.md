# ATLAS V7.1 RC2 — release scope

The owner approved the light static design and authorized publication to the existing public repository and GitHub Pages URL. RC2 replaces the earlier RC1 static presentation; financial models, Streamlit application/styles, financial payload, original report Markdown, export handlers and dependency pins remain unchanged.

The exact final corrected artifact passed the saved normal-Mac-Terminal release preflight: 134 Python tests, V6/V7 Chromium, all five static modules at 1440/1024/768/390px without horizontal overflow, full Streamlit E2E (including approval/revocation and exports), and offline synthetic generation. Two clean pinned builds also reproduced the HTML; the public artifact audit passed.

Approved docs/index.html SHA-256:
`8ea773df1ef3a98bc3d00dff13cb5b5399bd9f9c0a4ba4cf96d480497947edca`

The release contains the 103 allowlisted candidate files, including MIT and third-party notices. Only README, release/verification documentation and checksum metadata were refreshed after the successful gate, as authorized; tested code and HTML are byte-identical. No caches, local environment, raw Terminal logs, private datasets or provider-licensed prices are included. Public docs contains only index.html and .nojekyll.

Source destination: public emmascq-ship-it/atlas-portfolio-risk, main. Pages source: /docs. Static synthetic-only demo; no Streamlit hosting or paid services. Static Review Desk is read-only with unapproved exports; drafting, acknowledgment, approval and revocation require the full local Streamlit application. Evidence references do not verify claim truth.

RELEASE_FREEZE_SHA256.txt binds frozen source files. MANIFEST_SHA256.txt covers every packaged file except itself. Remote CI and deployed-byte/browser checks are verified after the publication commit; consult GitHub Actions and the publication verification report for their actual outcomes, rather than treating the local pass as hosted verification.
