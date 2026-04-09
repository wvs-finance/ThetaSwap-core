#!/bin/bash


ANG_DIR=/root/angstrom
PROD_BIN=/root/prod-bin
INSTALL_DEBUG_DIR=/usr/lib/debug/.build-id

# Build with full debuginfo + frame pointers + a guaranteed Build-ID note.
# (Don't rely on profile defaults; force it here so symbols always line up.)
RUSTFLAGS="-C target-cpu=native -C force-frame-pointers=yes -C debuginfo=2 -C link-arg=-Wl,--build-id -C link-arg=-Wl,--no-keep-memory" \
  cargo build \
  --bin angstrom \
  --profile maxperf-ss-debug \
  --features jemalloc \
  --manifest-path ${ANG_DIR}/Cargo.toml \
  --config 'profile.maxperf-ss-debug.lto="thin"' \
  --config profile.maxperf-ss-debug.codegen-units=4 \
  -j 4

# Ensure core dumps are captured by systemd-coredump
ulimit -c unlimited
systemctl restart systemd-coredump.socket

systemctl stop angstrom

# ---------------------------
# (do not change this shuffle)
# ---------------------------
BIN=${PROD_BIN}/angstrom-new
DBG=${BIN}.debug

cp ${BIN} ${PROD_BIN}/angstrom-old
cp ${ANG_DIR}/target/maxperf-ss-debug/angstrom ${BIN}
# ---------------------------

# Extract symbols to a separate file
objcopy --only-keep-debug "$BIN" "$DBG"

# Strip debug from the deployed binary (keeps .note.gnu.build-id)
strip --strip-debug --preserve-dates "$BIN"

# Add a link in the binary that points to the external debug file
objcopy --add-gnu-debuglink="$DBG" "$BIN"

# Install the .debug by Build-ID so coredumpctl/gdb can auto-find it:
#   /usr/lib/debug/.build-id/ab/cdef....debug
buildid=$(readelf -n "$BIN" | awk '/Build ID/ {print $3; exit}')
prefix=${buildid:0:2}; rest=${buildid:2}
install -D -m 0644 "$DBG" "${INSTALL_DEBUG_DIR}/${prefix}/${rest}.debug"

systemctl restart angstrom
