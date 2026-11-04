# M3 submission preparation

The semester brief requires a running product from a README with at most five
steps on another person's laptop, real AI on real input, a current exported
architecture diagram, a three-minute unlisted video, three known limitations,
two lines on actual contributions since M2, a repository link and a one-page
summary. Deadline: **16 November 2026, 23:59**.

- [ ] Complete a real Ollama extraction/report run on new permitted input.
- [ ] Follow the README on another person's laptop; record evidence in `m3_validation.md`.
- [ ] Give the professor the dedicated Windows ZIP link, not terminal commands. Confirm START_REVIEWWISE.bat appears directly in its extracted folder.
- [ ] Test `START_REVIEWWISE.bat` from a fresh Windows account with missing prerequisites, then repeat with internet disconnected after successful setup.
- [ ] Record versions, model digest, latency and actual failure cases.
- [ ] Confirm every member can explain and change the pipeline and launcher.
- [ ] Confirm actual contributions since M2; update README and project log.
- [ ] Record/upload the three-minute video and verify instructor access.
- [ ] Update the summary using measured results only; export the final one-page PDF.
- [ ] Review the draft branch and member attribution, then tag the agreed M3 submission commit.
- [ ] Submit the tagged repository link, video link and one-page PDF on Moodle.

The implementation draft is kept on the separate `m3-mvp` branch. Preserve
`main`, existing M1/M2 history and all M2 evidence. No submission tag, video upload
or Moodle submission is claimed. The summary PDF is a draft.

## Three-minute video outline

| Time | What to show |
|---|---|
| 0:00–0:20 | Problem, intended user and running local app. |
| 0:20–0:45 | New multilingual reviews and input preview. |
| 0:45–1:30 | Start real analysis and show progress. Label any time cut and state actual duration. |
| 1:30–2:10 | Counts, original evidence, positives and supported actions. |
| 2:10–2:30 | Download report; explain AI extraction versus Python counting. |
| 2:30–3:00 | Architecture, setup/restart, three limitations and actual test status. |

Use Windows Xbox Game Bar or a recorder already available. Do not present saved
or mocked responses as live inference. Remove personal details before recording
and use an accessible unlisted link; do not invent one in the summary.
