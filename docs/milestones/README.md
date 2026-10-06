# Milestone Tracking

Milestones (`M##`) are the unit of work. The [macro dashboard](project_plan.md) explains priorities; each `scope.md` is the execution contract, and each `completion_report.md` records delivery evidence. Detailed bead tasks belong only in the scope.

The [bead design review](design_review.md) records the pre-implementation audit and rationale. Beads are numbered Markdown work chunks; no external task service is required. Keep commands and observed onboarding friction current as each milestone ships.

## Current milestones (planned or active)

No milestone is Active yet.

- M01 – Bootstrap and smoke-test: Planned — [scope](M01_bootstrap/scope.md), [report](M01_bootstrap/completion_report.md)
- M02 – Prepare one dataset in two formats: Planned — [scope](M02_dataset_preparation/scope.md), [report](M02_dataset_preparation/completion_report.md)
- M03 – Select a reproducible training subset: Planned — [scope](M03_subset_selection/scope.md), [report](M03_subset_selection/completion_report.md)
- M04 – Produce real PyTorch batches: Planned — [scope](M04_pytorch_batches/scope.md), [report](M04_pytorch_batches/completion_report.md)
- M05 – Measure without overstating results: Planned — [scope](M05_benchmark/scope.md), [report](M05_benchmark/completion_report.md)
- M06 – Package the cookbook: Planned — [scope](M06_cookbook/scope.md), [report](M06_cookbook/completion_report.md)

## Layout

```text
docs/
`-- milestones/
    |-- README.md
    |-- project_plan.md
    |-- M01_bootstrap/          # M02–M06 use the same layout
    |   |-- scope.md
    |   `-- completion_report.md
    `-- archive/
        `-- README.md
```

## Lifecycle

1. **Plan:** Create the scope and report. Both may be `Planned` until execution begins; do not imply work or tests have happened.
2. **Start:** Mark scope and report `Active`, move the dashboard entry to Active, and update dates and this index. Confirm dependencies and define baseline guardrails before feature work.
3. **Execute:** Complete independently shippable or verifiable beads. Record shipped changes, decisions, exact test commands/results, ops notes, and outstanding work in the report. Add review/checklist artifacts only as needed.
4. **Reprioritize:** Update dashboard summaries, ordering, risks, and next steps when priorities change. Keep detailed tasks in scopes.
5. **Complete:** Require evidence for all exit criteria. Mark scope and report `Complete (YYYY-MM-DD)`, update dashboard status/date and a 1–2 line outcome, remove the milestone from this current list, and move the entire folder into `archive/`. Repair links (including report links to shared planning documents) and add archive entries in the same change.

Update report dates whenever evidence changes and the dashboard date whenever priorities or status change. Use relative links so specs and reports remain connected when their folder moves. Do not reimplement completed milestones unless explicitly asked.

## Completed milestones

None. See the [archive index](archive/README.md) for completed delivery records.
