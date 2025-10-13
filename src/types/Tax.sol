// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


import {Actions} from 
// 200 poolId || rate uint24  || action (base) uint8 || free space 32 

type Tax is uint256;

using TaxLibrary for Tax global;

library TaxLibrary{

    function poolId(Tax) internal view returns(bytes25){

    }

    function set_poolId(Tax, bytes25 truncated_pool_id) internal{
        
    }

    
    
    function rate(Tax) internal view returns(uint24){

    }

    function set_rate(Tax, uint24 taxRate) internal{
        // NOTE: We have the Tax as uint 256 and need to replace the
        // first 24 bits of data with taxRate

        // Tax ->   0xghghgdsfsdfsdfdsfdsfdsffsdf
        // mask ->  0xFFFFFFFFFFFFFFFF
        assembly("memory-safe"){
            let mask := 0xFFFFFFFFFFFFFFFF
            // Empty the most-left 24 bits
            // This is doing AND on the first 24 bits and or on the remaining
            // data 
        
        }
    }

    function set_base(Tax, uint256 action) internal returns(uint8){

    }

    function get_base(Tax) internal view returns(uint256){

    }

    // NOTE: This can take other data values important for tax creation

    function free_space(Tax) internal view returns(uitn256){

    }
}
