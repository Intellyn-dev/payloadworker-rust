//! Regression test for the backoff_ms pure logic in queue.rs.
//!
//! The fix ensures that:
//! 1. The queue loop passes the full Job struct directly to process_job
//!    instead of re-fetching by ID (which could panic with fetch_one if the row
//!    was deleted between claim and process).
//! 2. The redundant spawn_blocking + block_on wrapping of an async sqlx query
//!    is removed.
//!
//! Since the queue loop and process_job require a live database, this test
//! focuses on the pure `backoff_ms` function exported from queue.rs, verifying
//! that the exponential backoff calculation is correct and that the module
//! compiles and exports the function as expected after the fix.

use payloadworker::worker::queue::backoff_ms;

#[test]
fn test_backoff_ms_attempt_zero() {
    // 2^0 * 100 = 100ms
    assert_eq!(backoff_ms(0), 100);
}

#[test]
fn test_backoff_ms_attempt_one() {
    // 2^1 * 100 = 200ms
    assert_eq!(backoff_ms(1), 200);
}

#[test]
fn test_backoff_ms_attempt_two() {
    // 2^2 * 100 = 400ms
    assert_eq!(backoff_ms(2), 400);
}

#[test]
fn test_backoff_ms_attempt_three() {
    // 2^3 * 100 = 800ms
    assert_eq!(backoff_ms(3), 800);
}

#[test]
fn test_backoff_ms_increases_exponentially() {
    // Verify that each successive attempt doubles the delay,
    // confirming the exponential backoff logic is intact after the fix.
    let delays: Vec<u64> = (0..5).map(backoff_ms).collect();
    for i in 1..delays.len() {
        assert_eq!(
            delays[i],
            delays[i - 1] * 2,
            "Expected delay at attempt {} to be double the delay at attempt {}",
            i,
            i - 1
        );
    }
}

#[test]
fn test_backoff_ms_returns_u64() {
    // Ensure the return type is u64 (no truncation or overflow for small attempts)
    let result: u64 = backoff_ms(4);
    // 2^4 * 100 = 1600
    assert_eq!(result, 1600u64);
}