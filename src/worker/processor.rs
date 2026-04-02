use tracing::info;

use crate::errors::AppError;

pub async fn process_job(job: crate::db::jobs::Job) -> Result<(), AppError> {
    info!("Processing job {} with payload: {:?}", job.id, job.payload);
    Ok(())
}
