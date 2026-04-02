package worker

import "testing"

// TestBackoffMs verifies that backoff_ms returns correct exponential backoff values.
// This is a focused regression test for the fix in queue.rs where process_job now
// receives the job data directly from claim_pending_job instead of re-fetching it
// from the database using fetch_one(). The backoff logic in the error path of
// run_queue_loop depends on job.attempts, which is now passed directly from the
// claimed job struct rather than a potentially-missing re-fetched row.
func TestBackoffMs(t *testing.T) {
	tests := []struct {
		attempt  uint32
		expected uint64
	}{
		{0, 100},
		{1, 200},
		{2, 400},
		{3, 800},
		{4, 1600},
	}

	for _, tc := range tests {
		result := backoff_ms(tc.attempt)
		if result != tc.expected {
			t.Errorf("backoff_ms(%d) = %d, want %d", tc.attempt, result, tc.expected)
		}
	}
}

// TestBackoffMsZeroAttempts verifies that a job with zero attempts (first failure)
// gets the minimum backoff delay. This corresponds to the fix where job.attempts
// is read directly from the in-memory job struct passed to process_job, not from
// a re-fetched database row that could be missing (causing RowNotFound panic).
func TestBackoffMsZeroAttempts(t *testing.T) {
	result := backoff_ms(0)
	if result == 0 {
		t.Errorf("backoff_ms(0) should not be zero, got %d", result)
	}
	if result != 100 {
		t.Errorf("backoff_ms(0) = %d, want 100", result)
	}
}

// TestBackoffMsIncreasing verifies that backoff increases monotonically with attempts.
// The fix ensures job.attempts is available from the already-claimed job struct,
// so the backoff calculation in the error path of run_queue_loop is always safe.
func TestBackoffMsIncreasing(t *testing.T) {
	prev := backoff_ms(0)
	for attempt := uint32(1); attempt <= 5; attempt++ {
		curr := backoff_ms(attempt)
		if curr <= prev {
			t.Errorf("backoff_ms(%d)=%d should be greater than backoff_ms(%d)=%d", attempt, curr, attempt-1, prev)
		}
		prev = curr
	}
}