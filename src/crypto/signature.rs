use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

fn compute_hmac(payload: &[u8], secret: &str) -> String {
    let mut mac = HmacSha256::new_from_slice(secret.as_bytes())
        .expect("HMAC can take key of any size");
    mac.update(payload);
    hex::encode(mac.finalize().into_bytes())
}

pub fn verify_signature(payload: &[u8], signature: &str, secret: &str) -> bool {
    let computed = compute_hmac(payload, secret);
    computed == signature
}

pub fn generate_signature(payload: &[u8], secret: &str) -> String {
    compute_hmac(payload, secret)
}
