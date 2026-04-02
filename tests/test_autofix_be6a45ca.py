use payloadworker::errors::AppError;
use payloadworker::worker::processor::process_job;

/// Verifies the fix: process_job now accepts a Job struct directly (no re-fetch from DB),
/// so it cannot panic with RowNotFound when a job is deleted between claim and process.
/// The function should return Ok(()) for a valid Job passed in-memory, without any DB access.
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

    // Run the async function in a single-threaded runtime without any DB dependency.
    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("Failed to build runtime");

    let result = rt.block_on(process_job(job));

    assert!(
        result.is_ok(),
        "process_job should return Ok(()) when given a valid Job struct; got: {:?}",
        result
    );
}

#[test]
fn test_process_job_with_null_payload_returns_ok() {
    use payloadworker::db::jobs::Job;
    use uuid::Uuid;
    use chrono::Utc;
    use serde_json::Value;

    let job = Job {
        id: Uuid::new_v4(),
        payload: Value::Null,
        status: "pending".to_string(),
        attempts: 0,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("Failed to build runtime");

    let result = rt.block_on(process_job(job));

    assert!(
        result.is_ok(),
        "process_job should handle null payload gracefully without panicking; got: {:?}",
        result
    );
}

#[test]
fn test_process_job_does_not_require_database_connection() {
    use payloadworker::db::jobs::Job;
    use uuid::Uuid;
    use chrono::Utc;
    use serde_json::json;

    // This test verifies the core fix: the old code required a PgPool and re-fetched
    // the job via fetch_one(), which would panic on RowNotFound. The fixed version
    // takes the Job directly, so no pool is needed at all.
    let job = Job {
        id: Uuid::new_v4(),
        payload: json!({"action": "process", "item_id": 42}),
        status: "claimed".to_string(),
        attempts: 1,
        created_at: Utc::now(),
        updated_at: Utc::now(),
    };

    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .expect("Failed to build runtime");

    // If this compiles and runs without a PgPool argument, the fix is confirmed.
    let result = rt.block_on(process_job(job));
    assert!(result.is_ok());
}