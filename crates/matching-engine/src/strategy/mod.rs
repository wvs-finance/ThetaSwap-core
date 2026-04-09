mod binary_search;
// mod simplecheckpoint;
pub use binary_search::BinarySearchStrategy;
// pub use simplecheckpoint::SimpleCheckpointStrategy;

// Basic trait to describe a matching strategy
// pub trait MatchingStrategy<'a> {
//     /// Utility function to run this strategy against an order book.  Does
// the     /// book's standard fill operation and then attempts to run the
// provided     /// `finalize()` method to do our "last mile" computation
//     fn run(book: &'a OrderBook) -> Option<VolumeFillMatcher<'a>> {
//         let mut solver = VolumeFillMatcher::new(book);
//         solver.run_match();
//         Self::finalize(solver)
//     }
//
//     /// Finalization function to make sure our book is in a valid state and,
// if     /// not, do a "last mile" computation to get it there.  Will return
//     /// `None` if the book is considered unsolveable.
//     fn finalize(solver: VolumeFillMatcher) -> Option<VolumeFillMatcher>;
// }
