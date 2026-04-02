use axum::{
    extract::{Path, State},
    Json,
};
use uuid::Uuid;

use crate::{db::jobs::get_job, errors::AppError, AppState};

pub async fn get_job_status(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<crate::db::jobs::Job>, AppError> {
    let job = get_job(&state.pool, id)
        .await
        .map_err(AppError::Database)?
        .ok_or_else(|| AppError::NotFound(format!("Job {id} not found")))?;
    Ok(Json(job))
}
