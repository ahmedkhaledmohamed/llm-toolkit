# Agent terminal badge contribution

## Problem Framing

Developers running several coding agents in an editor need a way to identify sessions that are working, need attention, or have finished without opening every terminal tab.

## Approach

Use a standalone Python launcher and agent lifecycle hooks to update terminal titles with a small set of coloured status symbols. Keep the utility independent of document-conversion dependencies and preserve existing hook configuration during setup.

## Key Decisions

Use explicit agent events rather than silence to infer state, isolate each launched session, and distinguish recoverable tool failures from failed agent sessions. Extend the existing toolkit with a standalone utility while leaving repository naming and package installation unchanged.

## Pivots

The target surface was clarified as an editor's integrated terminal rather than a separate terminal application. The prototype therefore uses title symbols instead of terminal-specific tab colour APIs.

## Outcome

Implemented and locally installed the prototype, observed all four changing titles in a real editor terminal, and checked hook delivery, terminal interaction, configuration preservation and CLI launch paths. Publish it as an early prototype with explicit limits: authenticated agent flows and some waiting states remain unverified.
