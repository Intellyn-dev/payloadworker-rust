use axum::{
    extract::State,
    http::{HeaderMap, StatusCode},
    Json,
};
use serde::{Deserialize, Serialize};

use crate::{db::jobs::insert_job, errors::AppError, AppState};
use crate::crypto::signature::verify_signature;

#[derive(Debug, Deserialize)]
pub struct WebhookPayload {
    pub event: String,
    pub data: serde_json::Value,
}

#[derive(Serialize)]
pub struct WebhookResponse {
    pub job_id: uuid::Uuid,
    pub status: String,
}

pub async fn handle_webhook(
    State(state): State<AppState>,
    headers: HeaderMap,
    body: axum::body::Bytes,
) -> Result<(StatusCode, Json<WebhookResponse>), AppError> {
    let signature = headers
        .get("x-webhook-signature")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");

    if !state.webhook_secret.is_empty()
        && !verify_signature(&body, signature, &state.webhook_secret)
    {
        return Err(AppError::Unauthorized("Invalid webhook signature".to_string()));
    }

    let payload: WebhookPayload = serde_json::from_slice(&body)
        .map_err(|e| AppError::Validation(format!("Invalid JSON: {e}")))?;

    let job = insert_job(&state.pool, serde_json::to_value(&payload.data).unwrap())
        .await
        .map_err(AppError::Database)?;

    Ok((
        StatusCode::ACCEPTED,
        Json(WebhookResponse {
            job_id: job.id,
            status: job.status,
        }),
    ))
}
