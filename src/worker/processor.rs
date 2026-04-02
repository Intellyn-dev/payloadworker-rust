use sqlx::PgPool;
use tracing::info;
use uuid::Uuid;

use crate::db::jobs::get_job;
use crate::errors::AppError;

pub async fn process_job(pool: PgPool, job_id: Uuid) -> Result<(), AppError> {
    let job = tokio::task::spawn_blocking(move || {
        tokio::runtime::Handle::current().block_on(
            sqlx::query_as!(
                crate::db::jobs::Job,
                "SELECT id, payload, status, attempts, created_at, updated_at FROM jobs WHERE id = $1",
                job_id
            )
            .fetch_optional(&pool)
        )
    })
    .await
    .map_err(|e| AppError::Internal(format!("Task join error: {e}")))?
    .map_err(AppError::Database)?;

    match job {
        Some(job) => {
            info!("Processing job {} with payload: {:?}", job.id, job.payload);
            Ok(())
        }
        None => {
            info!("Job {} not found after being claimed, likely deleted externally", job_id);
            Err(AppError::NotFound(format!("Job {job_id} not found for processing after being claimed.")))
        }
    }
}
