# Decision

## Title

Hand-written SVG for the system diagram and metrics chart

## Date

2026-07-25

## Status

accepted

## Decision

Implement the system architecture diagram (4 fixed nodes, 3 edges) and the error-rate line chart as
small hand-written SVG React components instead of adding a visualization library.

## Context

SmartHR UI has no diagram or chart components; requirements section 16 explicitly allows custom
implementations for these. The diagram topology is fixed and the chart renders one deterministic
series with a deploy marker.

## Alternatives

- react-flow / dagre for the diagram; recharts / visx for the chart.

## Reason

The fixed layout makes a library strictly more code surface and dependency risk than ~100 lines of
SVG (requirements section 23 priorities 1-3). Custom SVG also makes the color + icon + label
redundancy of requirement 18 straightforward.

## Consequences

No pan/zoom or automatic layout; acceptable for a fixed 4-node demo. Spacing, font sizes, and status
colors must be kept consistent with SmartHR UI tokens manually.

## Revisit Conditions

Revisit if scenarios introduce variable topologies or multi-series charts.

## Related

`.plans/resilience-arena-mvp.md`
