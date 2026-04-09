// SPDX-License-Identifier: MIT
pragma solidity >=0.8.26;

// NoteId (uint256) — bit-packed, fully reversible
// Mirrors Panoptic's TokenId pattern for range accrual note parameters.
//
// From LSB to MSB:
// ===== 1 time (same for all notes) ============================
//   Property          Size     Offset    Comment
//   poolIndex         40 bits  0         keccak(source, poolId) truncated + collision counter
//   vegoid            8 bits   40        Spread parameter (Panoptic convention)
//   epochLength       16 bits  48        Blocks per epoch (analogous to tickSpacing)
// ===== 1 time (the note "leg") ================================
//   extensionFlag     3 bits   64        VANILLA=0, ACCRUAL_DECRUAL=1, TARN=2, BARRIERS=3, ...
//   notionalRatio     7 bits   71        Notional units per note (like optionRatio)
//   isLong            1 bit    78        0=short (sell theta), 1=long (buy theta)
//   tokenType         1 bit    79        Coupon denomination (0=token0, 1=token1)
//   reserved          2 bits   80        Future: riskPartner for multi-note strategies
//   tickLower         24 bits  82        int24 lower tick
//   tickUpper         24 bits  106       int24 upper tick
//   epochId           40 bits  130       uint40 epoch number (block-number-based)
// ===== reserved ===============================================
//   [unused]          86 bits  170       Future extensions
// ==============================================================

type NoteId is uint256;

// ── Masks ──

uint256 constant POOL_INDEX_MASK = 0xFFFFFFFFFF; // 40 bits

// ── ExtensionFlag constants ──

uint8 constant VANILLA = 0;
uint8 constant ACCRUAL_DECRUAL = 1;
uint8 constant TARN = 2;
uint8 constant BARRIERS = 3;
uint8 constant CALLABLE = 4;
uint8 constant BASKET_UNDERLIER = 5;
uint8 constant FLOATING_COUPON = 6;

// ── Errors ──

error InvalidRange(int24 tickLower, int24 tickUpper);
error InvalidNotionalRatio();

// ── Header fields (bits 0–63) ──

function addPoolIndex(NoteId self, uint64 _poolIndex) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_poolIndex) & POOL_INDEX_MASK));
    }
}

function poolIndex(NoteId self) pure returns (uint64) {
    unchecked {
        return uint64(NoteId.unwrap(self) & POOL_INDEX_MASK);
    }
}

function addVegoid(NoteId self, uint8 _vegoid) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_vegoid) << 40));
    }
}

function vegoid(NoteId self) pure returns (uint8) {
    unchecked {
        return uint8(NoteId.unwrap(self) >> 40);
    }
}

function addEpochLength(NoteId self, uint16 _epochLen) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_epochLen) << 48));
    }
}

function epochLen(NoteId self) pure returns (uint16) {
    unchecked {
        return uint16(NoteId.unwrap(self) >> 48);
    }
}

// ── Leg fields (bits 64–169) ──

function addExtensionFlag(NoteId self, uint8 _flag) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_flag & 0x07) << 64));
    }
}

function extensionFlag(NoteId self) pure returns (uint8) {
    unchecked {
        return uint8((NoteId.unwrap(self) >> 64) & 0x07);
    }
}

function addNotionalRatio(NoteId self, uint8 _ratio) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_ratio & 0x7F) << 71));
    }
}

function notionalRatio(NoteId self) pure returns (uint8) {
    unchecked {
        return uint8((NoteId.unwrap(self) >> 71) & 0x7F);
    }
}

function addIsLong(NoteId self, uint8 _isLong) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_isLong & 0x01) << 78));
    }
}

function isLong(NoteId self) pure returns (uint8) {
    unchecked {
        return uint8((NoteId.unwrap(self) >> 78) & 0x01);
    }
}

function addTokenType(NoteId self, uint8 _tokenType) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_tokenType & 0x01) << 79));
    }
}

function tokenType(NoteId self) pure returns (uint8) {
    unchecked {
        return uint8((NoteId.unwrap(self) >> 79) & 0x01);
    }
}

function addTickLower(NoteId self, int24 _tickLower) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(uint24(_tickLower)) << 82));
    }
}

function tickLower(NoteId self) pure returns (int24) {
    unchecked {
        return int24(int256(NoteId.unwrap(self) >> 82));
    }
}

function addTickUpper(NoteId self, int24 _tickUpper) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(uint24(_tickUpper)) << 106));
    }
}

function tickUpper(NoteId self) pure returns (int24) {
    unchecked {
        return int24(int256(NoteId.unwrap(self) >> 106));
    }
}

function addEpochId(NoteId self, uint40 _epochId) pure returns (NoteId) {
    unchecked {
        return NoteId.wrap(NoteId.unwrap(self) | (uint256(_epochId) << 130));
    }
}

function epochId(NoteId self) pure returns (uint40) {
    unchecked {
        return uint40(NoteId.unwrap(self) >> 130);
    }
}

// ── Validation ──

/// @notice Validates a NoteId's structural integrity.
/// @dev Mirrors Panoptic's TokenId.validate() pattern.
function validate(NoteId self) pure {
    int24 tL = self.tickLower();
    int24 tU = self.tickUpper();
    if (tL >= tU) revert InvalidRange(tL, tU);
    if (self.notionalRatio() == 0) revert InvalidNotionalRatio();
}

// ── Global using ──

using {
    addPoolIndex, poolIndex,
    addVegoid, vegoid,
    addEpochLength, epochLen,
    addExtensionFlag, extensionFlag,
    addNotionalRatio, notionalRatio,
    addIsLong, isLong,
    addTokenType, tokenType,
    addTickLower, tickLower,
    addTickUpper, tickUpper,
    addEpochId, epochId,
    validate
} for NoteId global;
