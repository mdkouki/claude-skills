# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-06-23

### Added
- 🦎 **Chameleon** — initial release
  - Stratified random sampling with census script
  - Four coverage modes: Quick, Standard (default), Deep, Custom %
  - Per-stratum focus override (`focus deep on <stratum>`)
  - Systematic random sampling with hash-derived offset (avoids A-name bias)
  - Detects: formatting & code style, naming conventions, design patterns,
    SQL & data access, decoupling & architecture, error handling, testing,
    convention over configuration depth
  - Per-finding confidence markers (✅ ⚠️ 🔍) in output
  - Sampling coverage table in `CONVENTIONS.md`
  - Quick-Reference Card (top 10 rules, ✅ confidence only)
  - Low-Confidence Signals section for weak observations
