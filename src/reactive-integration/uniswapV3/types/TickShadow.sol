// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

struct TickShadow {
    int24 tick;
    bool isSet;
}

function getTick(TickShadow storage ts) view returns (int24 tick, bool isSet) {
    tick = ts.tick;
    isSet = ts.isSet;
}

function setTick(TickShadow storage ts, int24 tick) {
    ts.tick = tick;
    ts.isSet = true;
}
