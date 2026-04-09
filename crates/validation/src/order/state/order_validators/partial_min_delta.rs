use angstrom_types::{primitive::OrderValidationError, sol_bindings::RawPoolOrder};

use super::{OrderValidation, OrderValidationState};

pub const MAX_RATIO_PCT: f64 = 0.8;

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct PartialMinDelta;

impl OrderValidation for PartialMinDelta {
    fn validate_order<O: RawPoolOrder>(
        &self,
        state: &mut OrderValidationState<O>
    ) -> Result<(), OrderValidationError> {
        if !state.order.is_partial() {
            return Ok(());
        }

        let max = state.order().amount();
        let min = state.order().min_amount();

        if max == 0 {
            return Err(OrderValidationError::NoAmountSpecified);
        }

        let ratio = min as f64 / max as f64;

        if ratio > MAX_RATIO_PCT {
            return Err(OrderValidationError::MinDeltaToSmall);
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use angstrom_types::sol_bindings::grouped_orders::AllOrders;

    use super::*;
    use crate::order::state::order_validators::make_base_order;

    #[test]
    fn test_partial_order_with_valid_delta_passes() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 1000;
                o.min_amount_in = 800;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(validator.validate_order(&mut state), Ok(()));
    }

    #[test]
    fn test_partial_order_at_boundary_passes() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 10000;
                o.min_amount_in = 8000;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(validator.validate_order(&mut state), Ok(()));
    }

    #[test]
    fn test_partial_order_with_insufficient_delta_fails() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 1000;
                o.min_amount_in = 801;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(
            validator.validate_order(&mut state),
            Err(OrderValidationError::MinDeltaToSmall)
        );
    }

    #[test]
    fn test_partial_order_with_90_percent_ratio_fails() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 1000;
                o.min_amount_in = 900;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(
            validator.validate_order(&mut state),
            Err(OrderValidationError::MinDeltaToSmall)
        );
    }

    #[test]
    fn test_partial_order_with_small_delta_passes() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 1000;
                o.min_amount_in = 100;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(validator.validate_order(&mut state), Ok(()));
    }

    #[test]
    fn test_partial_order_with_large_values() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = u128::MAX;
                o.min_amount_in = (u128::MAX as f64 * 0.79) as u128;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(validator.validate_order(&mut state), Ok(()));
    }

    #[test]
    fn test_partial_order_with_large_values_fails() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = u128::MAX;
                o.min_amount_in = (u128::MAX as f64 * 0.81) as u128;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(
            validator.validate_order(&mut state),
            Err(OrderValidationError::MinDeltaToSmall)
        );
    }

    #[test]
    fn test_edge_case_min_amount_zero() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 1000;
                o.min_amount_in = 0;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(validator.validate_order(&mut state), Ok(()));
    }

    #[test]
    fn test_precision_around_boundary() {
        let mut order = make_base_order();
        match &mut order {
            AllOrders::PartialStanding(o) => {
                o.max_amount_in = 1_000_000;
                o.min_amount_in = 800_001;
            }
            _ => unreachable!()
        }

        let mut state = OrderValidationState::new(&order);
        let validator = PartialMinDelta;
        assert_eq!(
            validator.validate_order(&mut state),
            Err(OrderValidationError::MinDeltaToSmall)
        );
    }
}
