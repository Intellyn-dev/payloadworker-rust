use axum::{
    routing::{get, post},
    Router,
};
use sqlx::PgPool;
use std::sync::Arc;
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod crypto;
mod db;
mod errors;
mod handlers;
mod worker;

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub webhook_secret: String,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    dotenvy::dotenv().ok();

    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://postgres:postgres@localhost:5432/payloadworker".to_string());

    let pool = db::pool::create_pool(&database_url).await?;
    let webhook_secret = std::env::var("WEBHOOK_SECRET").unwrap_or_default();

    let state = AppState {
        pool: pool.clone(),
        webhook_secret,
    };

    let queue_pool = pool.clone();
    tokio::spawn(async move {
        worker::queue::run_queue_loop(queue_pool).await;
    });

    let app = Router::new()
        .route("/health", get(health))
        .route("/webhook", post(handlers::webhook::handle_webhook))
        .route("/jobs/:id", get(handlers::jobs::get_job_status))
        .with_state(state)
        .layer(TraceLayer::new_for_http());

    let addr = std::env::var("BIND_ADDR").unwrap_or_else(|_| "0.0.0.0:8084".to_string());
    tracing::info!("payloadworker listening on {addr}");
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

async fn health() -> axum::Json<serde_json::Value> {
    axum::Json(serde_json::json!({ "status": "ok", "service": "payloadworker" }))
}
