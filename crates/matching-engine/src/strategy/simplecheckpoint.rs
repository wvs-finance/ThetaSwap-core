use super::MatchingStrategy;
use crate::matcher::VolumeFillMatcher;

/// Very simple strategy where we just roll the solver back to the last "good
/// solve" checkpoint and presume we're done there.
pub struct SimpleCheckpointStrategy {}

impl MatchingStrategy<'_> for SimpleCheckpointStrategy {
    fn finalize(solver: VolumeFillMatcher) -> Option<VolumeFillMatcher> {
        solver.from_checkpoint()
    }
}
