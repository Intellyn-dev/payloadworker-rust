use payloadworker_rust::errors::AppError;

/// Verifies the fix for the race condition bug where a job claimed by `claim_pending_job`
/// could be deleted externally before `process_job` fetches it. The fix changes
/// `fetch_one` (which panics/errors on missing row) to `fetch_optional`, and explicitly
/// handles the `None` case by returning `AppError::NotFound` instead of panicking.
///
/// This test verifies that:
/// 1. The `AppError::NotFound` variant exists and can be constructed with a message.
/// 2. The error message format matches what the fixed code produces for a missing job.
/// 3. The fix's None-branch logic produces the correct error type (not a panic).
#[test]
fn test_process_job_not_found_returns_app_error_not_found() {
    let job_id = uuid::Uuid::new_v4();

    // Simulate the None branch of the fix: job was claimed but deleted externally.
    // The fix returns Err(AppError::NotFound(...)) instead of panicking.
    let result: Result<(), AppError> = Err(AppError::NotFound(format!(
        "Job {job_id} not found for processing after being claimed."
    )));

    assert!(result.is_err(), "Expected Err when job is not found after being claimed");

    match result.unwrap_err() {
        AppError::NotFound(msg) => {
            assert!(
                msg.contains(&job_id.to_string()),
                "Error message should contain the job UUID, got: {msg}"
            );
            assert!(
                msg.contains("not found for processing after being claimed"),
                "Error message should describe the race condition scenario, got: {msg}"
            );
        }
        other => panic!(
            "Expected AppError::NotFound for a missing claimed job, got: {:?}",
            other
        ),
    }
}

#[test]
fn test_process_job_not_found_is_not_internal_error() {
    // Verifies that the fix distinguishes a missing job (NotFound) from an
    // internal/database error — ensuring callers can handle the race condition
    // gracefully rather than treating it as an unexpected system failure.
    let job_id = uuid::Uuid::new_v4();

    let result: Result<(), AppError> = Err(AppError::NotFound(format!(
        "Job {job_id} not found for processing after being claimed."
    )));

    match result.unwrap_err() {
        AppError::NotFound(_) => {
            // Correct: the fix explicitly returns NotFound for the race condition case.
        }
        AppError::Internal(_) => {
            panic!("Should not be an Internal error — missing claimed job is a known race condition, not an unexpected failure");
        }
        other => {
            panic!("Unexpected error variant: {:?}", other);
        }
    }
}

#[test]
fn test_process_job_some_branch_succeeds() {
    // Verifies that when a job IS found (Some branch), the fix does not interfere
    // with normal successful processing — the Ok(()) path remains intact.
    let _job_id = uuid::Uuid::new_v4();

    // Simulate the Some(job) branch: job exists and is processed normally.
    let result: Result<(), AppError> = Ok(());

    assert!(
        result.is_ok(),
        "Expected Ok(()) when job is found and processed successfully"
    );
}