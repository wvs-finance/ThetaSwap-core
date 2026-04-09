use angstrom_types::{primitive::OrderValidationError, sol_bindings::RawPoolOrder};

use super::{OrderValidation, OrderValidationState};

#[derive(Copy, Clone, Debug, PartialEq, Eq, Default)]
pub struct EnsureGasSet;

impl OrderValidation for EnsureGasSet {
    fn validate_order<O: RawPoolOrder>(
        &self,
        state: &mut OrderValidationState<O>
    ) -> Result<(), OrderValidationError> {
        if state.order().max_gas_token_0() == 0 {
            Err(OrderValidationError::NoGasSpecified)
        } else {
            Ok(())
        }
    }
}

#[cfg(test)]
mod test {
    use super::*;
    #[test]
    fn test_no_gas_specified_error() {
        use angstrom_types::primitive::OrderValidationError;

        use crate::order::{
            AllOrders,
            state::order_validators::{EnsureGasSet, OrderValidationState, make_base_order}
        };

        let mut order = make_base_order();
        if let AllOrders::PartialStanding(ref mut o) = order {
            o.max_extra_fee_asset0 = 0; // This is the value checked by min_amount()
        }

        let validator = EnsureGasSet;
        let mut state = OrderValidationState::new(&order);
        let result = validator.validate_order(&mut state);
        assert_eq!(result, Err(OrderValidationError::NoGasSpecified));
    }
}
