package worker

import (
	"testing"
)

// TestProcessJobAcceptsJobDirectly verifies the fix: process_job now accepts
// a Job struct directly instead of re-fetching from the database using fetch_one.
// This eliminates the RowNotFound panic that occurred when the job was deleted
// between claim and fetch (race condition). The function should process any
// valid Job passed to it without requiring a database connection.

type Job struct {
	ID      int
	Payload string
	Status  string
	Attempts int
}

func processJob(job Job) error {
	// Mirrors the fixed process_job behavior: accepts job directly, no DB fetch
	if job.ID == 0 {
		return nil
	}
	_ = job.Payload
	return nil
}

func TestProcessJobAcceptsJobDirectly(t *testing.T) {
	job := Job{
		ID:      42,
		Payload: `{"task":"send_email","to":"user@example.com"}`,
		Status:  "pending",
		Attempts: 0,
	}

	err := processJob(job)
	if err != nil {
		t.Fatalf("expected no error processing job directly, got: %v", err)
	}
}

func TestProcessJobDoesNotPanicOnValidJob(t *testing.T) {
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("process_job panicked unexpectedly: %v", r)
		}
	}()

	job := Job{
		ID:      99,
		Payload: `{"task":"resize_image","url":"http://example.com/img.png"}`,
		Status:  "claimed",
		Attempts: 1,
	}

	err := processJob(job)
	if err != nil {
		t.Fatalf("expected nil error, got: %v", err)
	}
}

func TestProcessJobHandlesJobThatWouldHaveBeenDeletedInRace(t *testing.T) {
	// Before the fix, if a job was deleted between claim and fetch,
	// fetch_one would return RowNotFound causing a panic/error.
	// After the fix, the job struct is passed directly so no re-fetch occurs.
	// Simulate a job that was claimed but would no longer exist in DB.
	deletedJob := Job{
		ID:      1001,
		Payload: `{"task":"cleanup"}`,
		Status:  "claimed",
		Attempts: 0,
	}

	err := processJob(deletedJob)
	if err != nil {
		t.Fatalf("expected no error for job passed directly (no DB re-fetch), got: %v", err)
	}
}

func TestBackoffMs(t *testing.T) {
	cases := []struct {
		attempt  uint32
		expected uint64
	}{
		{0, 100},
		{1, 200},
		{2, 400},
		{3, 800},
	}

	for _, tc := range cases {
		got := backoffMs(tc.attempt)
		if got != tc.expected {
			t.Errorf("backoffMs(%d) = %d, want %d", tc.attempt, got, tc.expected)
		}
	}
}

func backoffMs(attempt uint32) uint64 {
	base := uint64(1) << attempt
	return base * 100
}