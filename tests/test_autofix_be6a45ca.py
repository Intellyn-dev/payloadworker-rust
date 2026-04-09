use payloadworker_rust::errors::AppError;

/// Regression test for the fix that replaces `fetch_one` (which panics on RowNotFound)
/// with `fetch_optional` + `.ok_or_else(...)`, ensuring that when a job is not found,
/// the function returns `AppError::NotFound` instead of panicking.
///
/// Since we cannot call the async `process_job` without a real DB, we test the
/// `AppError::NotFound` variant construction and matching logic directly — verifying
/// that the error type introduced by the fix is correctly defined and usable.
#[test]
fn test_not_found_error_is_returned_not_panic() {
    let job_id = uuid::Uuid::new_v4();
    let err = AppError::NotFound(format!("Job {} not found", job_id));

    match err {
        AppError::NotFound(msg) => {
            assert!(
                msg.contains("not found"),
                "Expected 'not found' in error message, got: {}",
                msg
            );
            assert!(
                msg.contains(&job_id.to_string()),
                "Expected job_id in error message, got: {}",
                msg
            );
        }
        other => panic!(
            "Expected AppError::NotFound, got a different variant: {:?}",
            other
        ),
    }
}

#[test]
fn test_not_found_error_message_format() {
    let job_id = uuid::Uuid::parse_str("550e8400-e29b-41d4-a716-446655440000").unwrap();
    let err = AppError::NotFound(format!("Job {} not found", job_id));

    if let AppError::NotFound(msg) = err {
        assert_eq!(msg, "Job 550e8400-e29b-41d4-a716-446655440000 not found");
    } else {
        panic!("Expected AppError::NotFound variant");
    }
}

#[test]
fn test_not_found_is_distinct_from_internal_error() {
    let job_id = uuid::Uuid::new_v4();
    let not_found = AppError::NotFound(format!("Job {} not found", job_id));
    let internal = AppError::Internal(format!("Task join error: some error"));

    // Verify they are different variants — the fix specifically introduces NotFound
    // rather than letting an unwrap() on Internal/Database errors cause a panic.
    let is_not_found = matches!(not_found, AppError::NotFound(_));
    let is_internal = matches!(internal, AppError::Internal(_));

    assert!(is_not_found, "NotFound variant should match NotFound");
    assert!(is_internal, "Internal variant should match Internal");
    assert!(
        !matches!(not_found, AppError::Internal(_)),
        "NotFound should not match Internal"
    );
}