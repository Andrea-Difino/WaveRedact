use pyo3::prelude::*;

#[pyfunction]
fn censor_audio(
    audio_bytes: &[u8],
    sample_rate: u32,
    channels: u16,
    sample_width: u16,
    timestamps: Vec<(f64, f64)>,
    mode: &str
) -> PyResult<Vec<u8>> {

    let mut modified_audio = audio_bytes.to_vec();

    let bytes_per_frame = (channels as usize) * (sample_width as usize);
    let bytes_per_second = (sample_rate as usize) * bytes_per_frame;

    for (start, end) in timestamps {
        let raw_start = (start * (bytes_per_second as f64)) as usize;
        let raw_end = (end * (bytes_per_second as f64)) as usize;

        let safe_start = raw_start - (raw_start % bytes_per_frame);
        let safe_end = raw_end - (raw_end % bytes_per_frame);

        let max_len = modified_audio.len();
        let final_start = safe_start.min(max_len);
        let final_end = safe_end.min(max_len);
        
        if final_start < final_end {
            match mode {
                "silence" => modified_audio[final_start..final_end].fill(0),
                "beep" => {
                    let freq = 600.0;
                    let amplitude = 16000.0;

                    let slice = &mut modified_audio[final_start..final_end];

                    for (i,frame) in slice.chunks_exact_mut(bytes_per_frame).enumerate() {

                        let time = i as f64 / sample_rate as f64;
                        
                        let sine_value = (time * freq * 2.0 * std::f64::consts::PI).sin();
                        let sample_i16 = (sine_value * amplitude) as i16;
                        
                        let sample_bytes = sample_i16.to_le_bytes();
                        
                        for ch in 0..(channels as usize) {
                            let offset = ch * (sample_width as usize);

                            if sample_width == 2 {
                                frame[offset] = sample_bytes[0];
                                frame[offset + 1] = sample_bytes[1];
                            }
                        }
                    }
                },
                _ => {}
            }
        }

        
    }

    Ok(modified_audio)           
}

#[pymodule]
fn waveredact_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(censor_audio, m)?)?;
    Ok(())
} 