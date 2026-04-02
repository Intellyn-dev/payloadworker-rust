use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Job {
    pub id: Uuid,
    pub payload: serde_json::Value,
    pub status: String,
    pub attempts: i32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

pub async fn insert_job(pool: &PgPool, payload: serde_json::Value) -> Result<Job, sqlx::Error> {
    sqlx::query_as!(
        Job,
        r#"
        INSERT INTO jobs (id, payload, status, attempts, created_at, updated_at)
        VALUES ($1, $2, 'pending', 0, NOW(), NOW())
        RETURNING id, payload, status, attempts, created_at, updated_at
        "#,
        Uuid::new_v4(),
        payload,
    )
    .fetch_one(pool)
    .await
}

pub async fn get_job(pool: &PgPool, id: Uuid) -> Result<Option<Job>, sqlx::Error> {
    sqlx::query_as!(
        Job,
        "SELECT id, payload, status, attempts, created_at, updated_at FROM jobs WHERE id = $1",
        id
    )
    .fetch_optional(pool)
    .await
}

pub async fn update_job_status(
    pool: &PgPool,
    id: Uuid,
    status: &str,
) -> Result<(), sqlx::Error> {
    sqlx::query!(
        "UPDATE jobs SET status = $1, updated_at = NOW(), attempts = attempts + 1 WHERE id = $2",
        status,
        id
    )
    .execute(pool)
    .await?;
    Ok(())
}

pub async fn claim_pending_job(pool: &PgPool) -> Result<Option<Job>, sqlx::Error> {
    sqlx::query_as!(
        Job,
        r#"
        UPDATE jobs SET status = 'processing', updated_at = NOW()
        WHERE id = (
            SELECT id FROM jobs WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, payload, status, attempts, created_at, updated_at
        "#
    )
    .fetch_optional(pool)
    .await
}
