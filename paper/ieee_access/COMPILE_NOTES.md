# IEEE Access Compile Notes

This folder mirrors the modular structure of the approved IEEE Access
reference draft from the separate solar project, but contains only the
Fed-DDQN manuscript content.

Template status:
- Official IEEE Access LaTeX class files were not present locally.
- `ieeeaccess.cls` is a local compatibility wrapper for drafting.
- Replace/compare with the official IEEE Access template before final
  submission.

Build results should be appended after compilation.

## Verified Local Build

Compiled successfully on 2026-05-30 with bundled Tectonic:

```powershell
tectonic -X compile --outdir . --outfmt pdf --keep-logs --keep-intermediates --untrusted main.tex
```

Output:

- `main.pdf`
- `main.log`
- `main.bbl`
- `main.blg`

Post-build notes:

- BibTeX now completes without error messages after normalizing author
  separators in `references.bib`.
- Wide inherited tables were converted to `table*` floats for the two-column
  draft.
- Remaining warnings are non-fatal underfull box warnings and the local
  Fontconfig warning from Tectonic.

## 20-Page IEEE Working Draft Build

Compiled successfully on 2026-05-30 after the IEEE-first manuscript expansion.

Command used from `Paper_LATEX/ieee_access`:

```powershell
C:\Users\mayan\.codex\plugins\cache\openai-bundled\latex\0.2.0\bin\tectonic.exe -X compile --outdir . --outfmt pdf --keep-logs --keep-intermediates --untrusted main.tex
```

Current output:

- `main.pdf`: 20 pages.
- `main.log`: no fatal LaTeX errors found in the final scan.
- `main.bbl`: generated successfully.
- `main.blg`: BibTeX completed.

Verification notes:

- PDF text contains the canonical result values: Fed-DDQN latency 136.009 ms,
  SLA 97.73%, rejection 3.68%, edge usage 67.43%, DDQN latency 144.926 ms,
  FL-DDPG latency 138.373 ms, and Oracle latency 123.310 ms.
- Figure-file scan found no missing included image files.
- Final log scan found no undefined citations, undefined references, missing
  figures, fatal errors, emergency stops, or overfull-box matches.
- Remaining warnings are non-fatal underfull box messages and the local
  Fontconfig warning emitted by bundled Tectonic.

Template note:

- This remains a drafting build using the local `ieeeaccess.cls`
  compatibility wrapper. Before final submission, migrate or compare against
  the official IEEE Access LaTeX template and rerun the page-count and layout
  checks.

## Publication-Tone Cleanup

Updated on 2026-05-30 after the user requested that the manuscript read like a
submission paper rather than an internal caveat memo.

Edited sections:

- `sections/abstract_keywords.tex`
- `sections/dataset.tex`
- `sections/related_work.tex`
- `sections/experimental_setup.tex`
- `sections/results_discussion.tex`
- `sections/limitations.tex`

Style rule now applied:

- Use confident, normal academic wording for claims and results.
- Keep Dataset3 described as realistic synthetic, but avoid self-undermining
  phrases such as "strongest defensible claim," "universally superior,"
  "bounded claim," or "all results are synthetic."
- Put scope notes in standard manuscript language, not in reviewer-warning
  language.

Verification:

- Recompiled successfully with bundled Tectonic.
- Page count remains 20.
- PDF text scan confirmed the removed defensive phrases no longer appear.
- Final log scan again found no fatal errors, undefined references, undefined
  citations, missing figures, or overfull-box matches.

## Issue-Fix Pass From Attachment Review

Updated on 2026-05-30 after reviewing the attached issue list.

Implemented fixes:

- Localized canonical metric macros under `macros/canonical_metrics.tex` so the
  IEEE branch is self-contained and no longer depends on `../shared` during
  standalone compilation.
- Corrected the optimization objective in `sections/system_model.tex` from a
  multiplicative product to an additive weighted cost over selected latency,
  SLA misses, realized rejection, and edge penalty.
- Separated realized rejection `R_i` from the pre-decision QoS/admission-risk
  estimate `\hat{\rho}_i` used by the Stage-2 allocator.
- Clarified that the Stage-1 DDQN environment is an offline replay setting:
  each action is evaluated against a sampled Dataset3 row, while the next
  state is the next exogenous precomputed row rather than a mutated simulator
  state.
- Added the exact 30-feature Stage-1 feature list in `tables/features.tex` and
  clarified that label-generation outcomes are excluded from policy features.
- Corrected the dueling-network citation to Wang et al. (ICML/PMLR 2016) and
  added the corresponding BibTeX entry as `ref41`.
- Adjusted results wording so the main Fed-DDQN claim is tied to the main
  trainable baselines, while ablation variants remain diagnostic variants.
- Removed stale notation references and converted Markdown-style backticks in
  LaTeX source to `\texttt{}`.
- Added a note to the multi-seed ablation table clarifying which entries report
  standard deviations and which are seed means.

Verification:

- Recompiled `main.tex` with bundled Tectonic successfully.
- `main.pdf` exists and has 20 pages.
- Final source scan found no stale `../shared/canonical` include, stale
  `app:notation` label, stale `tables/notation` include, or old main-claim
  phrase.
- Final log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing figures, or overfull-box matches.

Remaining author-side items:

- Author affiliations, emails, funding details, ORCID IDs, and repository links
  are still placeholders because they were not supplied and should not be
  invented.
- The branch still uses the local `ieeeaccess.cls` compatibility wrapper for
  drafting; compare with the official IEEE Access template before submission.

## 22-Page Focused Reference Revision

Updated on 2026-05-31 after the second attachment review.

Implemented fixes:

- Reduced `references.bib` to 20 focused references aligned with the title:
  edge-cloud IoT offloading, DRL/DDQN, federated learning/FedProx,
  federated DRL offloading, and resource allocation.
- Removed broad `\nocite` usage from `main.tex`; every reference in the PDF is
  now cited from manuscript text or tables.
- Reframed Dataset3 as `the benchmark dataset` in manuscript macros and prose,
  avoiding version-history wording in the paper body.
- Reworked notation so the reported QoS rejection metric is explicitly
  `R_i = I[M_i=1 or F_i=1]`, with `M_i` as SLA miss, `F_i` as selected-path
  feasibility/admission failure, and `\hat{\rho}_i` as pre-decision risk.
- Updated the validation-score equation to include edge-overuse and heavy-task
  penalties matching the implementation.
- Added deeper method formulas for effective bandwidth, queue carryover,
  channel-aware decision margin, and capacity normalization.
- Split the Stage-2 allocator comparison into two readable tables:
  error/feasibility and QoS/efficiency.
- Added the task-type edge-share figure and moved selected diagnostics so the
  paper reaches 22 pages without padding.
- Added `\FloatBarrier`/`\clearpage` before references to stop appendix floats
  from mixing into the bibliography.

Verification:

- Recompiled `main.tex` with bundled Tectonic successfully.
- `main.pdf` now has 22 pages.
- `main.bbl` contains exactly 20 `\bibitem` entries.
- Source scan found no `v6.x`, `Dataset3`, stale `dataset3`, fake DOI, or
  `example.com` references in active IEEE manuscript sources.
- Final log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing figures, emergency stops, or overfull-box matches.

Remaining author-side items:

- Real affiliations, verified emails, ORCID IDs, funding text, repository/data
  links, and official IEEE Access production metadata still need author input.
- The draft still uses the local compatibility `ieeeaccess.cls`; migrate to the
  official IEEE Access class before submission.

## Appendix Page 19--20 Layout Refresh

Updated on 2026-05-31 after the user flagged sparse formatting on pages 19 and
20 of the compiled IEEE Access PDF.

Implemented fixes:

- Added a `\FloatBarrier` before the appendix input so result-section floats
  clear before Appendix A starts.
- Reworked `sections/appendix.tex` so Appendix A begins with the heading,
  explanatory text, and grouped figure interpretation rather than loose figure
  captions.
- Converted appendix figures to in-place `[H]` placement to keep the page 19
  and page 20 diagnostics near their explanatory text.
- Converted `tables/sla_thresholds.tex` from a two-column `table*` float to a
  compact single-column in-place table.
- Added explanatory text around Table 14 and Fig. 25 so the allocator/SLA
  diagnostics on page 20 read as part of the paper instead of isolated display
  items.
- Removed the full-size compact visual-summary appendix figure from the first
  appendix flow so it would not create a sparse page.

Verification:

- Recompiled `main.tex` with bundled Tectonic successfully.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count remains 22 pages.
- Page-text check confirms page 19 now starts with Appendix A and page 20
  contains Table 14 plus explanatory SLA/allocator text.
- Log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.

## Conclusion Page 18 Fill Revision

Updated on 2026-05-31 after the user asked to make page 18 less empty and fill
roughly 70 percent of the page with relevant paper content.

Implemented fixes:

- Expanded `sections/conclusion.tex` with deployment-facing interpretation
  rather than filler text.
- Added discussion of channel-aware and resource-aware offloading control under
  burst windows.
- Added deployment interpretation for federated zone-level learning,
  heterogeneous edge zones, FedProx-style stabilization, and prioritized replay.
- Added a clearer connection between Stage-1 offloading and Stage-2
  resource-admission/allocation.
- Added an operational layered-scheduler paragraph explaining how routing
  metrics and resource-admission metrics can be monitored separately while
  remaining tied to the same QoS objective.

Verification:

- Recompiled `main.tex` with bundled Tectonic successfully.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count remains 22 pages.
- Page 18 extracted text increased from about 489 characters before this
  revision to about 2954 characters after the revision.
- Log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.

## Conclusion Page 18 Visual Fill Refinement

Updated on 2026-05-31 after the user clarified that page 18 was still not
visually filled enough and requested roughly 70 percent page coverage.

Implemented fixes:

- Added a compact unnumbered deployment-reading table to
  `sections/conclusion.tex`.
- The table summarizes how the proposed two-stage scheduler responds to queue
  bursts, channel degradation, tight deadlines, high priority, and heavy
  video/AI/firmware loads.
- Added a short explanatory paragraph after the table to clarify the
  deployment distinction between Stage-1 tier selection and Stage-2 bounded
  resource assignment.

Verification:

- Recompiled `main.tex` with bundled Tectonic successfully.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count remains 22 pages.
- Page 18 extracted text increased again to about 4275 characters and now
  includes a visible compact table, making the page substantially fuller.
- Log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.

## Appendix Page 19--20 Density Refinement

Updated on 2026-05-31 after the user asked to reduce the remaining page 19
figure spacing and use the empty space on page 20.

Implemented fixes:

- Tightened local appendix float spacing with smaller `\textfloatsep`,
  `\floatsep`, `\intextsep`, and caption skips.
- Created cropped derived copies of the claim-evidence map and compact
  policy-metric visual to remove large internal blank margins:
  `170_fig_a23_research_claim_evidence_map_cropped.png` and
  `171_fig_a24_compact_policy_metric_table_cropped.png`.
- Replaced the full claim-evidence image with the cropped version.
- Added more interpretation after the queue-pressure and claim-evidence
  figures so page 19 reads as a diagnostic discussion, not only a figure stack.
- Reintroduced the compact policy-metric visual as a cropped reading-aid figure
  on page 20, with text explaining why Stage-2 allocator improvements must be
  read together with Stage-1 latency, SLA, rejection, and edge-use behavior.

Verification:

- Recompiled `main.tex` with bundled Tectonic successfully.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count remains 22 pages.
- Page-text check increased page 19 from about 2003 to 2843 extracted
  characters and page 20 from about 1179 to 1762 extracted characters.
- Log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.

## Humanization, Flow, and Hyphenation Pass

Updated on 2026-05-31 after the user asked to humanize the IEEE Access draft,
remove AI-like phrasing, reduce plagiarism-style risk, stop distracting
sentence breaks around floats, and prevent dash-based word splitting.

Implemented fixes:

- Reworked the active IEEE manuscript prose across the abstract, introduction,
  related work, dataset, system model, proposed Fed-DDQN section, Stage-2
  allocator, experimental setup, results, limitations, conclusion, and
  appendix.
- Removed internal project-log language from the active manuscript, including
  notebook-output wording, version-style framing, cache discussion, and
  development-run phrasing.
- Fixed the problem-objective equation in `sections/system_model.tex` by adding
  the missing heavy-task penalty plus sign and splitting the equation across
  aligned lines.
- Added stronger LaTeX line-breaking controls in `main.tex`:
  `microtype`, high hyphen penalties, high tolerance, emergency stretch, and
  large hyphen minima.
- Removed the visible placeholder author-biography block from the compiled
  draft until final author details are available.
- Removed one duplicated appendix reading-aid figure so the references and
  appendix fit cleanly into the 22-page target.

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 22 pages.
- Extracted-PDF hyphenated line-break count: 0.
- `main.bbl` contains exactly 20 bibliography items.
- Final log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.
- Active-source scan found no stale `Dataset3`, `v6.x`, internal notebook,
  cache, verified-run, or common AI-intro phrases in compiled manuscript paths.

## Formatting Repair After Exact-Page Compaction

Updated on 2026-05-31 after the user clarified that 22 pages is the minimum,
not an exact cap, and reported that the PDF formatting had become unstable.

Implemented fixes:

- Replaced the previous extreme line-breaking settings with a moderate
  `microtype`-based setup: higher hyphen penalties, controlled emergency
  stretch, and normal paragraph spacing without `\sloppy`.
- Restored normal IEEE-style bibliography sizing instead of forcing the
  reference list into `\scriptsize`.
- Added a clean page break before the appendix and another before references so
  the appendix, conclusion, and bibliography no longer run into each other.
- Restored a compact policy-metric diagnostic in the appendix and added
  explanatory text so the extra page is useful rather than mostly empty.
- Replaced the remaining "current benchmark" phrasing in the active compiled
  sources with neutral "benchmark dataset" wording.

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic 0.16.9 through the
  LaTeX plugin.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 23 pages, satisfying the requested minimum of 22 pages.
- `main.bbl` contains exactly 20 bibliography items.
- Final log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.
- Visual preview was regenerated under
  `Paper_LATEX/ieee_access/_layout_preview/`; pages 19--21 now separate the
  conclusion and appendix cleanly and page 21 is filled with relevant appendix
  diagnostics.
- Active-source scan found no stale `Dataset3`, `v6.x`, internal notebook/cache
  wording, AI-disclosure wording, or earlier internal caveat phrases in the
  compiled manuscript paths.

## Manuscript-Only Review Fix Pass

Updated on 2026-05-31 after the approved manuscript-only review plan. This pass
did not modify `v6.6.ipynb` and did not add notebook hooks, gamma-zero runs, or
baseline multi-seed reruns.

Implemented fixes:

- Reframed Stage 1 as an offline exogenous-transition Fed-DDQN benchmark where
  actions affect current-task reward but do not mutate future CSV states.
- Added terminal-mask notation to the DDQN target and defined
  `d_i^{term}` for split, gap, sequence, and final-sample boundaries.
- Added `tables/method_parameters.tex` for missing symbols including
  `u_min`, `P_i^e`, `H_i`, `h_i`, `B(j,t)`, `C^r_{j,t}`, `epsilon`, `eta`,
  `w`, `z_i`, and `f_phi`.
- Clarified generator-native CPU, memory, bandwidth, and availability units.
- Updated the effective-bandwidth equation with packet-loss, outage,
  jitter/congestion domains and a positive floor.
- Added `tables/reward_reproducibility.tex` with reward shaping, clipping, and
  validation-score details.
- Expanded the baseline table into a provenance/adaptation table with source
  families, objectives, local adaptation, validation protocol, and fidelity.
- Added `tables/reproducibility_manifest.tex` for the generator, six CSV files,
  split protocol, label-generation logic, analysis workflow, figure exporter,
  and checksum plan.
- Added Stage-2 target-generation equations for urgency, queue/network stress,
  demand-scaled resource targets, pre-decision risk, and capacity projection.
- Clarified that Stage-2 risk excludes realized labels, Oracle actions, and
  generated final allocation targets.
- Added scenario-table notes explaining descriptive dashes and the
  impossible-deadline rejection/SLA mismatch.
- Toned down the main causal wording to "consistent with the combined effect of
  the proposed training, reward, and validation design."

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic 0.16.9 through the
  LaTeX plugin.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 26 pages, satisfying the requested minimum of 22 pages.
- `main.bbl` contains exactly 20 bibliography items.
- Final severe-warning scan found no fatal LaTeX errors, undefined citations,
  undefined references, missing included figures, emergency stops,
  float-too-large warnings, or overfull-box matches.
- Active-source scan found no stale `Dataset3`, `dataset3`, `v6.x`, notebook,
  internal cache, CUDA wording, or federation-only causal overclaim in compiled
  manuscript paths.
- The only `optimal` wording in active sources explicitly states that generated
  allocator targets are not measured or globally optimal labels.
- Rendered audit previews were generated under
  `Paper_LATEX/ieee_access/_review_fix2_audit/` using PyMuPDF.

## Appendix Figure 20 Replacement

Updated on 2026-05-31 after the user noted that Figure 20 used an internal
claim-evidence/nomenclature-style map that would not be useful to readers.

Implemented fixes:

- Removed the claim-evidence map from the compiled appendix.
- Created a new high-resolution metric figure:
  `figures/diagnostics/173_fig_a26_policy_metric_snapshot.png`.
- Replaced Figure 20 with the new core test-metric snapshot comparing DDQN,
  FL-DDPG, Fed-DDQN, and Oracle on latency, SLA, rejection, and edge usage.
- Updated the Figure 20 caption and surrounding appendix text so the discussion
  now explains the metric tradeoff rather than a manuscript navigation map.
- Removed the later duplicate compact-metric figure block from the appendix.

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic 0.16.9 through the
  LaTeX plugin.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 25 pages, still above the requested 22-page minimum.
- `main.bbl` contains exactly 20 bibliography items.
- Severe log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing figures, emergency stops, float-too-large warnings, or
  overfull-box matches.

## Results-Section Page 17--18 Layout Repair

Updated on 2026-05-31 after the user flagged excessive whitespace and uneven
float spacing around pages 17 and 18.

Implemented fixes:

- Added consistent global float spacing in `main.tex` using `\textfloatsep`,
  `\floatsep`, and `\intextsep` so figure/table spacing is less uneven across
  the manuscript.
- Merged the standalone action-distribution figure into the main policy
  scorecard/tradeoff figure. This removed a separate float that was drifting
  away from the QoS discussion.
- Converted the scenario table from a full-width float into a compact
  in-column table so it no longer creates a mostly blank full-width float page.
- Grouped the scenario heatmap, Oracle-agreement matrix, and task-type
  edge-share plot into one compact full-width diagnostic figure.
- Converted the Fed-DDQN ablation table into an in-column table and kept the
  ablation CI plot close to its discussion.
- Moved the Stage-2 allocator comparison tables slightly later in the Resource
  Allocation subsection so explanatory allocator text and figures fill the
  page before the full-width allocator tables appear.

Verification:

- Bundled Tectonic 0.16.9 compiled `Paper_LATEX/ieee_access/main.tex`.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 23 pages, above the requested 22-page minimum.
- `main.bbl` contains exactly 20 bibliography items.
- Severe log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing figures, emergency stops, float-too-large warnings, or
  overfull-box matches.
- Visual previews were rendered in
  `Paper_LATEX/ieee_access/_page17_18_fix_final2/`.
- Visual previews for pages 22--23 were rendered under
  `Paper_LATEX/ieee_access/_fig20_replacement_audit/`.

## Review Consistency Fix Pass

Updated on 2026-05-31 after the approved review-fix plan for the active IEEE
Access branch.

Implemented fixes:

- Reconciled rejection, SLA miss, and broad QoS-failure notation. The compiled
  manuscript now treats reported rejection as selected-path feasibility or
  admission failure, while broad QoS failure is a separate union indicator used
  only where needed.
- Aligned reward prose, reward-term wording, evaluation metrics, scenario-table
  headings, and conclusion language with the selected rejection definition.
- Made the checkpointing algorithm use the same validation objective as the main
  validation-score equation, including latency, SLA miss, rejection, edge
  overuse, and heavy-task misuse.
- Clarified the Stage-2 allocator denominator as
  6,563 Fed-DDQN edge-selected rows out of 9,733 allocator-valid test rows.
- Defined the pre-decision QoS/admission-risk estimate and mapped the compact
  allocator readout notation back to the formal Stage-2 allocation equations.
- Qualified the federated communication-cost statement so it reports model
  transfer volume without claiming a universal byte-saving result.
- Removed final-model wording that incorrectly attributed prioritized replay to
  the proposed configuration.
- Replaced non-traceable allocator MAE macro prose with table-traceable values;
  a later manuscript-export sync refreshed these values directly from the saved
  Stage-2 allocator export.
- Moved the unused duplicate-label methodology file out of the active source
  tree to `Paper_LATEX/old/unused_sections/`.
- Removed the empty DOI macro; IEEE Access assigns DOI after acceptance.
- Author affiliations remain pending verified author-provided text and were not
  invented during this pass.

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic 0.16.9 through the
  LaTeX plugin.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 23 pages, above the requested minimum of 22 pages.
- `main.bbl` contains exactly 20 bibliography items.
- Final severe-warning scan found no fatal LaTeX errors, undefined citations,
  undefined references, missing included figures, emergency stops, float-too-large
  warnings, or overfull-box matches.
- Rendered pages 13--20 to
  `Paper_LATEX/ieee_access/_review_fix_audit/` for visual inspection.
- Active-source scan found no stale `QoS rejection`, `Dataset3`, `v6.x`,
  notebook, internal cache, stale communication-overclaim, or obsolete allocator
  MAE macro wording in the compiled manuscript paths.

## IEEE Access Float/Layout Stabilization

Updated on 2026-05-31 after a layout-focused pass on the active IEEE Access
draft.

Implemented fixes:

- Combined the policy scorecard and tradeoff-bubble diagnostics into one
  full-width results figure so the main comparison page no longer carries two
  cramped one-column floats.
- Restored the multi-seed ablation table as a readable full-width table and
  removed the earlier over-compressed one-column rendering.
- Relaxed the task-type and ablation figure placement so scenario and ablation
  floats no longer overfill the page bottom.
- Kept the allocator CDF inside the Stage-2 resource-allocation discussion
  instead of allowing it to float ahead of the section.
- Removed the results-section barrier that was holding back the resource
  allocation text and creating a sparse ablation page.
- Moved the deployment-reading table earlier in the conclusion and removed the
  forced appendix-start page break so conclusion and appendix content flow
  without a nearly empty page.

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic 0.16.9 through the
  LaTeX plugin.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 22 pages, satisfying the requested minimum of 22 pages.
- `main.bbl` contains exactly 20 bibliography items.
- Final severe-warning scan found no fatal LaTeX errors, undefined citations,
  undefined references, missing included figures, emergency stops, float-too-large
  warnings, or overfull-box matches.
- Visual audit pages were regenerated under
  `Paper_LATEX/ieee_access/_layout_audit/`.
- Ghostscript was not available on this machine during this pass; page rendering
  for visual inspection was performed with PyMuPDF.

## Empty-Column Layout Refinement

Updated on 2026-05-31 after the user identified remaining empty-column areas
around pages 13, 15, and 17.

Implemented fixes:

- Moved the policy action-distribution figure into the QoS/resource-tradeoff
  subsection so page 13's lower-right column carries a relevant visual instead
  of empty space.
- Added a short interpretation paragraph below that figure to connect edge
  usage with resource stability and rejection behavior.
- Converted the task-type edge-share visual from a full-width float to a
  one-column in-section figure, filling the right side of the scenario page and
  keeping it close to the Oracle-agreement discussion.
- Added a compact Stage-2 allocation formula/readout box in the resource
  allocation subsection:
  demand-proportional allocation plus learned residual correction, risk
  projection, and capacity projection.
- Added explanatory allocator text below the CDF/formula pair so page 17 no
  longer has a large unused lower section.

Verification:

- Recompiled `main.tex` successfully with bundled Tectonic 0.16.9 through the
  LaTeX plugin.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 23 pages, still above the requested 22-page minimum.
- `main.bbl` contains exactly 20 bibliography items.
- Regenerated visual previews for pages 13, 15, 17, and 18 in
  `Paper_LATEX/ieee_access/_layout_preview/`.
- Final log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing included figures, emergency stops, or overfull-box
  matches.
- Active-source scan found no stale `Dataset3`, `v6.x`, internal notebook/cache
  wording, AI-disclosure wording, or earlier internal caveat phrases in the
  compiled manuscript paths.

## v6.6 Notebook Hooks and Reproducibility Export Bundle

Updated on 2026-05-31 after adding notebook-side reproducibility hooks for the
active Fed-DDQN workflow.

Implemented notebook hooks:

- Added cache-preserving flags in `v6.6.ipynb` for gamma-zero ablation,
  DDQN/FL-DDPG baseline multi-seed runs, and manuscript export generation.
- Kept trained Stage-1 artifacts under `dataset3/_v64_cache`; new optional
  hook artifacts and manuscript exports are written under `dataset3/_v66_cache`.
- Extended the tensor replay buffer to store terminal `done` values and return
  them from normal and prioritized sampling.
- Updated proposed Fed-DDQN, ablation, centralized DDQN, and FL-DDPG-style
  training paths to use terminal-masked bootstrapping:
  `r + gamma * (1 - done) * Q_target(next_state)`.
- Added an optional `No Bootstrapping (Gamma=0)` ablation hook. It is disabled
  by default and is not reported in the manuscript unless a completed cache or
  export file exists.
- Added optional DDQN/FL-DDPG multi-seed hooks over seeds `[42, 77, 123]`.
  These are disabled by default and are not reported in the manuscript unless
  completed export files exist.
- Added a cache-only manuscript export cell that writes dataset checksums,
  split manifest, reward configuration, allocator target/risk specification,
  reproducibility manifest, and cached main comparison/ablation/scenario tables.

Generated export folder:

- `dataset3/_v66_cache/manuscript_exports/`

Generated exports in the smoke run:

- `dataset_checksums.csv`
- `split_manifest.json`
- `reward_config.json`
- `allocator_target_risk_spec.json`
- `main_policy_comparison_test_only.csv`
- `fed_ddqn_ablation_summary.csv`
- `fed_ddqn_multiseed_raw.csv`
- `scenario_wise_final_table.csv`
- `reproducibility_manifest.json`
- `exports_index.json`

Deferred optional exports:

- `gamma_zero_ablation_results.csv`
- `baseline_multiseed_raw.csv`
- `baseline_multiseed_summary.csv`

Manuscript policy:

- No gamma-zero or baseline-variance numbers were inserted into the IEEE Access
  paper in this pass.
- Current reported results remain the cached Stage-1 values already used by the
  manuscript.
- Terminal-masked target hooks affect future retraining; existing cached
  checkpoints were not silently relabeled as newly retrained models.

Verification:

- `v6.6.ipynb` remained valid JSON.
- All 38 code cells passed Python AST parsing.
- Static search found no stale unmasked training-target expressions in the
  updated training paths.
- ReplayBuffer smoke test confirmed five-field normal sampling and seven-field
  prioritized sampling with stored terminal masks.
- Cache-only export smoke test generated the manuscript bundle from existing
  saved caches without retraining.
- Bundled Tectonic was forced through the LaTeX plugin and compiled
  `Paper_LATEX/ieee_access/main.tex` successfully.
- Current PDF remains `Paper_LATEX/ieee_access/main.pdf`, 25 pages, with 20
  bibliography items.

## Fresh Manuscript Export Sync

Updated on 2026-05-31 after the user reran the notebook export workflow.

Applied results from:

- `dataset3/_v66_cache/manuscript_exports/main_policy_comparison_test_only.csv`
- `dataset3/_v66_cache/manuscript_exports/fed_ddqn_ablation_summary.csv`
- `dataset3/_v66_cache/manuscript_exports/fed_ddqn_multiseed_raw.csv`
- `dataset3/_v66_cache/manuscript_exports/allocator_target_risk_spec.json`
- `dataset3/_v66_cache/manuscript_exports/reproducibility_manifest.json`
- `dataset3/_v66_cache/manuscript_exports/exports_index.json`

Implemented manuscript updates:

- Confirmed the main test comparison values already matched the fresh export.
- Updated the multi-seed ablation table so all reported columns use the
  completed three-seed mean plus standard deviation values from the export.
- Refreshed Stage-2 allocator table values from the exported
  allocator-target/risk specification, including raw residual MAE, capacity
  normalization, under-allocation, capacity violation, SLA-risk, and efficiency
  values.
- Updated the reproducibility wording so the checksum manifest is described as
  an exported artifact rather than a planned future file.
- Updated local and shared canonical allocator macros to match the fresh
  allocator export.

Deferred optional results:

- `gamma_zero_ablation_results.csv` was not present in the export bundle.
- `baseline_multiseed_raw.csv` and `baseline_multiseed_summary.csv` were not
  present in the export bundle.
- No gamma-zero or baseline-variance numbers were added to the manuscript.

Verification:

- Bundled Tectonic 0.16.9 compiled `Paper_LATEX/ieee_access/main.tex`.
- Current output remains `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 25 pages.
- `main.bbl` contains exactly 20 bibliography items.
- Severe log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing figures, emergency stops, float-too-large warnings, or
  overfull-box matches.

## Max Two Images Per Row Layout Adjustment

Updated on 2026-05-31 after the user requested that grouped result figures use
at most two images per row.

Implemented layout changes:

- Updated the grouped policy scorecard/tradeoff/action-distribution figure so
  the first two panels appear side by side and the third panel appears centered
  below them.
- Updated the grouped scenario-diagnostics figure with the same two-plus-one
  layout.
- Added conservative float-placement controls in `main.tex` so wide grouped
  figures can sit cleanly near the top of float pages instead of being
  vertically centered with large top whitespace.

Verification:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex`.
- Current PDF: `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 25 pages.
- `main.bbl` contains exactly 20 bibliography items.
- Severe log scan found no fatal LaTeX errors, undefined citations, undefined
  references, missing figures, emergency stops, float-too-large warnings, or
  overfull-box matches.
- Source scan found no remaining three-across `0.32\textwidth` grouped image
  rows.
- Visual previews were written to
  `Paper_LATEX/ieee_access/_max_two_images_per_row_preview/`.

## Figure Placement and Missing-Graphic Audit

Updated on 2026-06-01 after the user reported figure descriptions appearing
without their visuals nearby.

Findings:

- All `\includegraphics` paths used by the active IEEE manuscript resolve to
  existing files under `Paper_LATEX/ieee_access/figures`.
- No undefined figure references were found in the active source files.
- The visible issue was float placement: some full-width result figures were
  deferred, making the explanatory text appear before the corresponding visual.

Implemented layout changes:

- Enabled bottom placement support for double-column floats with `stfloats`.
- Moved the Stage-1 latency-improvement figure to a bottom double-column float
  so it stays close to the main-results discussion.
- Added targeted `\FloatBarrier` guards after the grouped policy and scenario
  diagnostic figures so later prose does not run ahead of those visuals.

Verification:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex`.
- Current PDF: `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 25 pages.
- Static figure audit found zero missing `\includegraphics` files.

## Figure 10 Page-15 Right-Column Placement

Updated on 2026-06-01 after the user requested that Fig. 10 be reduced and
moved into the empty right-column space on page 15.

Implemented layout changes:

- Converted Fig. 10 from a large double-column result figure into a smaller
  single-column figure.
- Placed Fig. 10 after the main-results prose with a controlled column break so
  the figure, caption, and explanatory paragraph occupy the page-15 right
  column.
- Kept Table 12 in its original top double-column placement after testing and
  rejecting a bottom-table alternative that made the page less readable.

Verification:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex`.
- Current PDF: `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 24 pages.
- Page-15 render confirms Fig. 10 is smaller and placed in the right column
  beside the main-results discussion.

## Former Figure 11 Split Pass

Updated on 2026-06-01 after the user requested that the three images previously
clustered as one result figure be separated.

Implemented layout changes:

- Split the Stage-1 policy tradeoff bubble and policy action-distribution plots
  into two separate side-by-side result figures near the main test-comparison
  discussion.
- Kept the policy multi-objective scorecard as its own centered figure and
  increased it to a larger single display.
- Updated the surrounding discussion so each plot is referenced as an
  independent figure rather than as panels inside a clustered figure.

Verification:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex`.
- Current PDF: `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 24 pages.
- Page renders confirm the tradeoff and action-distribution figures appear
  together on page 15, while the scorecard is centered and enlarged on the next
  result page.

## Table 14 Two-Column Ablation Pass

Updated on 2026-06-01 after the user requested that Table 14 be made readable
as a central two-column table with the Multi-Seed Ablation subsection.

Implemented layout changes:

- Converted `tables/multiseed_ablation.tex` from a forced single-column `[H]`
  table to a top-positioned two-column `table*`.
- Replaced the compressed `\resizebox{\columnwidth}{!}{...}` layout with a
  wider `tabular*` at `0.96\textwidth`, using `\small` text and modest row
  spacing.
- Kept the table immediately after the Multi-Seed Ablation explanation and
  added a local float barrier before the ablation interval figure so the theory,
  table, and figure remain in the intended reading order.

Verification:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex`.
- Current PDF: `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 24 pages.
- Temporary TeX page-count probe reported `MAINPDFPAGES=24`; probe artifacts
  were removed after verification.

## Page 17-18 Single-Column Figure Reflow

Updated on 2026-06-01 after the user requested a tighter page-17/page-18
arrangement around the Multi-Seed Ablation and Resource Allocation
subsections.

Implemented layout changes:

- Changed the ablation interval plot from a forced `[H]` placement to a
  top-priority single-column float and increased it to full `\columnwidth` so
  it can occupy the spare right-column space more readably.
- Removed the barrier between the ablation conclusion paragraph and
  `\subsection{Resource Allocation}` so the subsection opening text can rise
  into the space previously consumed by the fixed figure.
- Changed the Stage-2 allocation readout figure from `[H]` to a top-priority
  single-column float and inserted a local barrier immediately before it so the
  first Resource Allocation paragraphs stay ahead of the figure while later
  pages remain anchored.

Verification:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex`.
- Current PDF: `Paper_LATEX/ieee_access/main.pdf`.
- Current page count: 24 pages.

Reverted on 2026-06-01:

- The last two page-17/page-18 reflow edits were undone at the user's request.
- Fig. 15 was restored to its earlier fixed `[H]` position immediately after
  Table 14, at `0.92\columnwidth`.
- The ablation conclusion text, the barrier before Resource Allocation, and
  the Stage-2 allocation readout were restored to the earlier order and sizing.
- Bundled Tectonic compiled the restored `main.tex`; current page count remains
  24 pages.

## Cross-Editor Compile Guard

Updated on 2026-06-01 after the user reported that compiling with other
software could show an older/different layout.

Implemented build changes:

- Added TeX root/program comments at the top of `main.tex` so TeX-aware editors
  know to compile `main.tex` with XeLaTeX and BibTeX.
- Added `.latexmkrc` in `Paper_LATEX/ieee_access` to force latexmk-compatible
  tools into XeLaTeX mode.
- Refreshed both `main.pdf` and `rebuild.pdf` from the same successful build.
- No manuscript content or reported values were changed.

Recommended external build target:

- Root file: `main.tex`
- Engine: XeLaTeX, or latexmk with the included `.latexmkrc`
- Bibliography: BibTeX
- If an editor still shows a previous layout, clean auxiliary files before
  rebuilding.

## Page-14-Onward Rebuild Verification Against `rebuild.pdf`

Updated on 2026-06-01 after the user requested that the active LaTeX reproduce
the `rebuild.pdf` layout from page 14 onward.

Implemented verification steps:

- Treated `Paper_LATEX/ieee_access/rebuild.pdf` as the authoritative reference
  layout.
- Created `Paper_LATEX/ieee_access/image_pdf/`.
- Downloaded PDF-rendering wheels into `Paper_LATEX/ieee_access/_wheels/` and
  manually extracted the working renderer into
  `Paper_LATEX/ieee_access/_pdf_renderer_vendor_manual/`.
- Rendered the reference PDF at 300 DPI as
  `image_pdf/page_01.png` through `image_pdf/page_24.png`.
- Compiled `Paper_LATEX/ieee_access/main.tex` with bundled Tectonic.
- Rendered the compiled PDF at 300 DPI as
  `image_pdf/compiled_page_01.png` through
  `image_pdf/compiled_page_24.png`.
- Compared every rendered page, with special focus on pages 14--24.

Verification result:

- `main.tex` compiled successfully with bundled Tectonic.
- `main.pdf` and `rebuild.pdf` were refreshed from the same verified build.
- Final page count: 24 pages.
- Rendered page dimensions: 2481 x 3508 pixels at 300 DPI.
- Pages 14--24 are pixel-identical between `main.pdf` and `rebuild.pdf`.
- A full 24-page image comparison also passed with zero pixel differences.
- No missing `\includegraphics` targets were found in the active IEEE source.
- Log scan after the final compile found no undefined citations or references.
  Two pre-existing overfull warnings remain outside the requested page-14+
  rebuild area: `sections/stage2_allocator.tex` line 55 and
  `tables/baselines.tex` line 20.
- No manuscript text, equations, reported values, captions, citations, table
  values, author metadata, or figure order were changed during this pass.

Notes:

- No LaTeX structural edits were required because the active source already
  reproduced the reference layout exactly after compilation.
- Broken experimental renderer target folders created during setup
  (`pymupdf_vendor`, `pdfium_vendor`, and
  `Paper_LATEX/ieee_access/_python_vendor`) were removed after the verified
  renderer path was established.

## Pasted Review Notation and Metric Fix Pass

Updated on 2026-06-01 after the user requested execution of
`docs/superpowers/plans/2026-06-01-ieee-access-notation-metric-fixes.md`.

Implemented manuscript fixes:

- Renamed the DDQN terminal-mask symbol from `d_i^{\mathrm{term}}` to
  `\zeta_i^{\mathrm{term}}` so it no longer conflicts with the task-size
  notation.
- Updated the generated queue carryover recurrence so the stress/recovery term
  is inside the nonnegative projection, and clarified that recovery effects are
  signed while queues remain nonnegative.
- Added the deadline-tightness definition used by the Stage-2 allocator and
  renamed the real-time flag to `\chi_i^{\mathrm{rt}}`.
- Defined the allocator-valid evaluation set
  `\mathcal{I}^{\mathrm{valid}}_e` and tied the allocator MAE denominator to
  that set.
- Reworded the scenario-table deadline flag as a deadline-admission predicate
  rather than a direct SLA-failure label.
- Clarified generator-native normalized units for bandwidth and resource
  pressure quantities.
- Added reward-range notation for `L_i^{\mathrm{best}}` and
  `L_i^{\mathrm{worst}}`.
- Calibrated baseline provenance language so faithful DDQN and the
  federated actor-critic-style comparator are separated from style-inspired
  scheduling/metaheuristic comparators.

Verification result:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex` successfully.
- Final page count: 24 pages.
- `main.pdf` and `rebuild.pdf` were refreshed from the same successful build
  and have matching SHA-256 hashes.
- Final log scan found no undefined citations, undefined references, missing
  figures, or overfull boxes.
- Spot-checked rendered pages 12--15 after compilation; the updated formulas,
  baseline table, metric table, and main-results note are readable.
- Reported result numbers, table data values, citation keys, author metadata,
  and figure files were not changed.

## T2-T7 Technical Review Repair Pass

Updated on 2026-06-01 after the user requested the manuscript-only fixes from
`Paper_LATEX/fixes-needed.pdf`, excluding T1, E1/E2, and external-verification
items.

Implemented manuscript fixes:

- Added a formal latency-reference Oracle rule in the system model and
  replaced broad "ceiling" wording with latency-specific language.
- Added complete selected-path feasibility predicates for edge and cloud
  execution, then tied selected-path rejection to `F_i` and `R_i`.
- Standardized Stage-2 notation around generated proxy targets
  `\mathbf{y}_i^{*}` and final predictions `\hat{\mathbf{y}}_i`.
- Rewrote the Stage-2 readout using the baseline allocation, residual
  correction, risk projection, and capacity projection terms.
- Replaced the channel-margin proxy with normalized dimensionless edge and
  cloud scores and noted that the learned Q-network, not the proxy, produces
  reported decisions.
- Calibrated the latency-ranking and baseline-fidelity wording so the claims
  refer to the main implemented comparison methods and the shared evaluation
  pipeline.
- Fixed prose/caption spacing around `\dataset{}` and the dataset schema
  caption.

Verification result:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex` successfully.
- Direct Tectonic compile with kept logs also passed.
- Final PDF page count: 25 pages.
- `main.pdf` and `rebuild.pdf` were refreshed from the same successful build
  and have matching SHA-256 hashes.
- Log scan found no undefined references, undefined citations, missing figure
  files, or overfull boxes.
- Source scan over manuscript `.tex` files found no stale phrases from the
  review-fix checklist. A broad scan over the full folder can still match
  generated `main.aux` entries because LaTeX serializes the dataset macro with
  an internal auxiliary-file space; the manuscript source and rendered caption
  are correct.
- Reported result numbers, citation keys, author metadata, table data values,
  and figure files were not changed.

## fix_needed.pdf Technical Repair Pass

Updated on 2026-06-01 after the user requested the active IEEE Access draft to
address `Paper_LATEX/fix_needed.pdf` major technical findings 1--5, notation
and implementation audit notes, proofing-sweep items, and highest-priority
items 1--4. Meaningful editorial/presentation findings and external
verification items were intentionally left out of scope.

Implemented manuscript fixes:

- Rebuilt `tables/scenario_table.tex` from
  `dataset3/_v66_cache/manuscript_exports/scenario_wise_final_table.csv` using
  Fed-DDQN rows only, with `N` capped at the valid policy-evaluation subset
  (`N=9,733`) and a note separating it from the raw temporal test split
  (`11,957` rows).
- Updated the Results discussion so scenario evidence is explicitly tied to
  the valid held-out policy-evaluation subset rather than full-benchmark
  descriptive counts.
- Standardized `\hat{\rho}_i` as a pre-decision QoS/admission-risk estimate,
  distinct from realized SLA miss `M_i`, selected-path rejection `R_i`, and
  union QoS failure `Q_i`.
- Aligned the Stage-2 risk-projection equations with the implementation:
  capacity-normalized residual branch, rejection-aware demand branch, fixed
  `0.10/0.90` blend, and group-wise capacity normalization over
  `\mathcal{G}^{\mathrm{valid}}_e(j,t)`.
- Cleaned feasibility, SLA, and rejection wording so Stage 1 selects an
  execution tier and is penalized when the selected path is infeasible.
- Preserved the allocator tradeoff in the abstract and conclusion: the
  rejection-aware demand rule has the lowest proxy-target MAE, while residual
  plus risk projection has the best efficiency score, lowest under-allocation,
  and zero capacity violation.
- Reformatted the Stage-2 base-allocation equation component-wise to remove a
  new overfull hbox warning from the edited formula.

Verification result:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex` successfully.
- Direct Tectonic compile with kept logs also passed.
- Final PDF page count: 25 pages.
- `main.pdf` and `rebuild.pdf` were refreshed from the same successful build
  and have matching SHA-256 hashes:
  `3284f7a965d85e7790ffc36534a60bf67b897390fa8786d302e2397603060031`.
- Scenario-table numeric check passed against the exported CSV; all scenario
  `N` values are `<= 9,733`.
- Source scans found none of the stale phrases requested in the repair plan.
- Log scan found no undefined citations, undefined references, or missing
  figure files. The log still reports the recurring page-height
  `Overfull \vbox (14.20158pt too high)` warning in `sections/system_model`;
  no overfull hbox remains from the Stage-2 equation changes.
- Reported result numbers, citation keys, author metadata, bibliography count,
  and figure files were not changed.

## Figure Text-Overlap Repair Pass

Updated on 2026-06-02 after a visual audit of all figures currently included
by the active IEEE Access draft.

Scope:

- Scanned all 22 active `\includegraphics` assets used by
  `Paper_LATEX/ieee_access/main.tex` and its included section files.
- Created audit contact sheets under
  `Paper_LATEX/ieee_access/_figure_text_audit/`.
- Preserved the LaTeX figure widths and the original pixel dimensions of the
  edited assets.

Figure assets repaired:

- `figures/diagrams/150_fig_a1_system_architecture.png`: moved crowded
  architecture callouts so the Stage-2 bypass note, edge-selected arrow label,
  and resource-adaptation label no longer collide.
- `figures/diagrams/151_fig_a2_temporal_split_protocol.png`: separated gap
  labels and staggered close boundary tick labels around the purged validation
  and test gaps.
- `figures/results/152_fig_a3_policy_tradeoff_bubble.png`: repositioned policy
  labels with clear callouts so Fed-DDQN, FL-DDPG, DDQN, Oracle, and the
  heuristic baseline labels do not overlap or clip.
- `figures/results/157_fig_a8_allocator_qos_tradeoff.png`: separated the top
  allocator-variant labels and kept right-edge annotations inside the plot.

Verification result:

- Bundled Tectonic compiled `Paper_LATEX/ieee_access/main.tex` successfully.
- Final PDF page count is 25 pages.
- `main.pdf` and `rebuild.pdf` were refreshed from the same successful build
  and have matching SHA-256 hashes:
  `c2032a6a2e6fb9a47290f93af1372999af3232d82955ed8f2ecf57808f32751b`.
- PDF pages were rendered to
  `Paper_LATEX/ieee_access/_figure_text_audit/pdf_pages_after/` and checked at
  manuscript scale.
- Log scan found no undefined citations, undefined references, or missing
  figure files. The recurring page-height `Overfull \vbox (14.20158pt too
  high)` warning remains; no figure-file errors were introduced.
