
# Usage

spec OS uses slash commands to guide you through the specification process.
Each command is a conversation—the AI asks questions, you provide direction, and together you shape your specification.

## The Design Workflow

Spec OS follows a structured sequence. Each step builds on the previous one.
> All documents are on spec/

### Phase 1: Business Model


1. **Purpose** — 
2. **Business Model**
3. **GoalTree**

See [Busines Modeling](business-modeling.md) for details on each command.

(Async)
### Phase 2: Functional Requirements

1. **Domain Modeling**
3. **Event-List**
2. **MissionStament**
3. **FunctionRefinement**

### Phase 3: System Decomposition


1. **ERD**
2. **Context Modeling**
3. **Data Flow**
4. **Requirements**


### Phase 4: Behavior Specification

1. **State-Transition-Table**
2. **Activity-Flow-Diagram** 

### Phase 5: Arquitecture

Follow [IDD](./IDD.md) and [TDD](./TDD.md)

4. Certora Specification

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/product-vision` | Define product overview, roadmap sections, and data shape |
| `/design-tokens` | Choose colors and typography |
| `/design-shell` | Design navigation and layout |
| `/shape-section` | Define a section's scope, requirements, and generate sample data + types |
| `/design-screen` | Create screen design components |
| `/screenshot-design` | Capture screenshots |
| `/export-product` | Generate the complete handoff package |
| `/product-roadmap` | Update product sections (after initial creation) |
| `/data-shape` | Update data entities (after initial creation) |
| `/sample-data` | Update sample data and types (after initial creation) |

## Tips

- **Follow the sequence** — Each step builds on the previous. Don't skip ahead.
- **Be specific** — The more detail you provide, the better the output.
- **Iterate** — Each command is a conversation. Refine until you're happy.
- **Restart the dev server** — After creating new components, restart to see changes.