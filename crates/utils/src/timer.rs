use std::{future::Future, time::Instant};

pub fn time_fn<F, O>(f: F) -> (O, u128)
where
    F: FnOnce() -> O
{
    let now = Instant::now();
    let res = f();
    let elapsed = now.elapsed().as_millis();
    (res, elapsed)
}

pub async fn async_time_fn<F, O, D>(f: F) -> (O, u128)
where
    F: FnOnce() -> D,
    D: Future<Output = O>
{
    let now = Instant::now();
    let res = f().await;
    let elapsed = now.elapsed().as_millis();
    (res, elapsed)
}
