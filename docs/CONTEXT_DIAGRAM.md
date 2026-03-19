


## Guidelines

Inclusion criteria:
- Entities that jointly with the SuD achieve composite system goals
- Entities where the SuD attempts to cause desired effects
- Entities providing information the SuD needs

Exclusion criteria:
- Entities whose effects do not contribute to composite system goals
- Internal contracts used by entry-point integrators (include only the direct interface, e.g., UniversalRouter, not contracts it calls internally)

Design requirements:
- The context (domain) must be a containing rectangle holding all context entities
- Communication channels represent abstracted communication without assuming specific semantics
- Flows abstract away delay, distortion, misdirection, and loss
- Reference the Mission Statement environment boundary to define relevant context
- Structure must correspond to system functionality
