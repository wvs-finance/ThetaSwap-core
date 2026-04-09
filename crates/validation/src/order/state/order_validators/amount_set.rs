use angstrom_types::{primitive::OrderValidationError, sol_bindings::RawPoolOrder};

use super::{OrderValidation, OrderValidationState};

#[derive(Copy, Clone, Debug, PartialEq, Eq, Default)]
pub struct EnsureAmountSet;

impl OrderValidation for EnsureAmountSet {
    fn validate_order<O: RawPoolOrder>(
        &self,
        state: &mut OrderValidationState<O>
    ) -> Result<(), OrderValidationError> {
        if state.order().min_amount() == 0 {
            Err(OrderValidationError::NoAmountSpecified)
        } else {
            Ok(())
        }
    }
}

#[cfg(test)]
mod test {
    use angstrom_types::sol_bindings::grouped_orders::AllOrders;

    use super::*;
    #[test]
    fn test_no_amount_specified_error() {
        use angstrom_types::primitive::OrderValidationError;

        use crate::order::state::order_validators::{
            EnsureAmountSet, OrderValidationState, make_base_order
        };

        let mut order = make_base_order();
        if let AllOrders::PartialStanding(ref mut o) = order {
            o.min_amount_in = 0; // This is the value checked by min_amount()
        }

        let validator = EnsureAmountSet;
        let mut state = OrderValidationState::new(&order);
        let result = validator.validate_order(&mut state);
        assert_eq!(result, Err(OrderValidationError::NoAmountSpecified));
    }
}
