use sqlx::PgPool;
use tokio::time::{sleep, Duration};
use tracing::{error, info};

use crate::db::jobs::{claim_pending_job, update_job_status};
use super::processor::process_job;

pub fn backoff_ms(attempt: u32) -> u64 {
    let base = 2u32.pow(attempt);
    base as u64 * 100
}

pub async fn run_queue_loop(pool: PgPool) {
    info!("Queue worker started");
    loop {
        match claim_pending_job(&pool).await {
            Ok(Some(job)) => {
                info!("Processing job {}", job.id);
                match process_job(job.clone()).await {
                    Ok(_) => {
                        if let Err(e) = update_job_status(&pool, job.id, "completed").await {
                            error!("Failed to mark job completed: {e}");
                        }
                    }
                    Err(e) => {
                        error!("Job {} failed: {e}", job.id);
                        let delay = backoff_ms(job.attempts as u32);
                        sleep(Duration::from_millis(delay)).await;
                        let _ = update_job_status(&pool, job.id, "failed").await;
                    }
                }
            }
            Ok(None) => {
                sleep(Duration::from_secs(1)).await;
            }
            Err(e) => {
                error!("Queue poll error: {e}");
                sleep(Duration::from_secs(5)).await;
            }
        }
    }
}
