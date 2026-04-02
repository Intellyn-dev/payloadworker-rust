use payloadworker::errors::AppError;
use payloadworker::worker::processor::process_job;

/// Verifies the fix: process_job now accepts a Job struct directly instead of
/// re-fetching from the database by ID. This means no fetch_one() panic can occur
/// when a job is deleted between claim and process. The function should accept a
/// fully constructed Job and return Ok(()) without any database interaction.
#[test]
fn test_process_job_accepts_job_struct_and_returns_ok() {
    use payloadworker::db::jobs::Job;
    use uuid::Uuid;
    use chrono::Utc;
    use serde_json::json;

    let job = Job {
        id: Uuid::new_v4(),
        payload: json!({"task": "send_email", "to": "user@example.com"}),
        status: "pending".to_string(),
        attempts: 0,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    // The fix passes the Job struct directly to process_job, eliminating the
    // redundant fetch_one() call that would panic if the job was deleted.
    // We verify the function signature accepts a Job and returns Result<(), AppError>.
    let rt = tokio::runtime::Runtime::new().unwrap();
    let result: Result<(), AppError> = rt.block_on(process_job(job));
    assert!(result.is_ok(), "process_job should return Ok(()) for a valid job struct");
}

#[test]
fn test_process_job_with_multiple_attempts_returns_ok() {
    use payloadworker::db::jobs::Job;
    use uuid::Uuid;
    use chrono::Utc;
    use serde_json::json;

    // Verify that a job with multiple attempts (retry scenario) is handled correctly
    // without any database re-fetch that could panic.
    let job = Job {
        id: Uuid::new_v4(),
        payload: json!({"task": "process_payment", "amount": 100}),
        status: "pending".to_string(),
        attempts: 3,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    let rt = tokio::runtime::Runtime::new().unwrap();
    let result: Result<(), AppError> = rt.block_on(process_job(job));
    assert!(result.is_ok(), "process_job should return Ok(()) regardless of attempt count");
}

#[test]
fn test_process_job_with_empty_payload_returns_ok() {
    use payloadworker::db::jobs::Job;
    use uuid::Uuid;
    use chrono::Utc;
    use serde_json::json;

    // Verify that a job with a minimal/empty payload does not cause a panic
    // and returns Ok(()), confirming no fragile fetch_one() is involved.
    let job = Job {
        id: Uuid::new_v4(),
        payload: json!({}),
        status: "pending".to_string(),
        attempts: 0,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    let rt = tokio::runtime::Runtime::new().unwrap();
    let result: Result<(), AppError> = rt.block_on(process_job(job));
    assert!(result.is_ok(), "process_job should return Ok(()) for a job with empty payload");
}