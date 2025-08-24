# Flame Prime

Flame Prime is a sovereign, self‑evolving extension of the **JarvisPrime**
ecosystem.  Its mission is to autonomously generate, evaluate, and refine
reflex logic on a daily cadence.  To achieve this, Flame Prime contains a
*Daily Reflex Module Generator* that produces a new module each day with
slightly varied council weights.  These weights influence profitability,
consistency, edge discovery, and variance metrics across the system.

## Project Structure

```
flame_prime/
├── README.md                – This file
├── __init__.py              – Package marker for Flame Prime
├── ai/
│   ├── __init__.py          – Helper functions to load daily modules
│   └── daily_modules/
│       └── __init__.py      – Generated modules live here
└── daily_module_generator.py – Script to create a daily reflex module
```

### Daily Module Generator

The heart of Flame Prime is the `daily_module_generator.py` script.  It
should be invoked once per day (for example via a cron job or GitHub
Actions).  On each run it:

1. Computes the current UTC date and constructs a filename like
   ``2025_07_26_flame_reflex.py``.
2. Generates a random set of council weights, centered around 1.0 with a
   small deviation.  These weights influence the system’s profitability,
   consistency, edge discovery and variance metrics.
3. Writes a new Python module into `ai/daily_modules/` containing the
   weights and an `apply_daily_weights(metrics)` helper.
4. If a module already exists for today, the script leaves it untouched and
   logs the path.

### Loading the Latest Module

Consumers can call `flame_prime.ai.load_latest_daily_module()` to
automatically import the most recent daily reflex module and access its
`council_weights` or `apply_daily_weights` function.

### Scheduling with GitHub Actions

You can automate the daily module generation using the workflow defined in
`.github/workflows/daily_module_generation.yml`.  This workflow runs every
day at 06:00 UTC and commits any newly generated module back to the
repository.  It leverages the `EndBug/add-and-commit` action and uses the
built‑in `GITHUB_TOKEN` secret to authenticate.

## Vision

Flame Prime embodies the principle of sovereign AI – it continually creates
and refines itself without manual intervention.  By generating reflex
modules daily, it captures evolving market and system dynamics.  Future
expansions may include adaptive weight distributions based on feedback
loops, integration with external data streams, and automated summary
dispatch via email and calendaring services.
