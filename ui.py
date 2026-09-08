import gradio as gr
import subprocess

def generate_video(youtube_url, speaker_id, style, count, prompt_style, tts_voice, visual, original_voice):
    """
    Executes the auto_run.py batch pipeline passing the UI parameters.
    Yields output lines dynamically so the user can see progress in the UI.
    """
    cmd = [
        "python", "auto_run.py",
        "--url", youtube_url,
        "--speaker", speaker_id,
        "--style", style,
        "--count", str(count),
        "--prompt-style", prompt_style,
        "--voice", tts_voice,
        "--visual", visual
    ]
    if original_voice:
        cmd.append("--original-voice")

    # Run the process and yield stdout line-by-line
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    log_output = ""
    for line in iter(process.stdout.readline, ''):
        log_output += line
        yield log_output

    process.stdout.close()
    process.wait()

    if process.returncode == 0:
        log_output += "\n\n✅ Rendering Complete! Check the root folder for the generated variations."
    else:
        log_output += "\n\n❌ Pipeline failed. Check the logs above."

    yield log_output

def create_ui():
    with gr.Blocks(title="Psychedelic Speech Engine") as app:
        gr.Markdown("# 🌀 Psychedelic Speech-to-Music Video Engine")
        gr.Markdown("Automated pipeline converting YouTube speech into music videos.")

        with gr.Row():
            with gr.Column():
                youtube_url = gr.Textbox(label="YouTube URL", placeholder="https://www.youtube.com/watch?v=...", info="The video containing the speech to extract.")
                speaker_id = gr.Textbox(label="Target Speaker ID", value="auto", info="WhisperX diarization ID, or 'auto' to pick whoever talks the most.")
                style = gr.Dropdown(label="Psytrance Style", choices=["random", "fullon", "darkpsy", "hitech"], value="random", info="Sub-style used for Suno track generation.")

            with gr.Column():
                count = gr.Slider(label="Psytrance Track Count", minimum=1, maximum=12, value=4, step=1, info="Number of psytrance tracks to generate.")
                prompt_style = gr.Textbox(label="LLM Prompt Style", value="rhythmic spoken-word stanzas", info="Instructions for DeepSeek to format the transcript.")
                tts_voice = gr.Dropdown(label="Kokoro TTS Voice", choices=["am_onyx", "am_adam", "am_michael", "af_heart", "af_bella"], value="am_onyx", info="Voice profile for synthesis.")
                visual = gr.Dropdown(label="Visual Style Layer", choices=["default", "acid", "mirror", "kaleido", "layered"], value="default", info="render_beat visual style (acid = hue cycling, mirror/kaleido = kaleidoscope, layered = psychedelic base + Mandelbrot).")
                original_voice = gr.Checkbox(label="Use speaker's natural voice", value=False, info="Use original audio clips instead of TTS re-voicing.")

        generate_btn = gr.Button("🚀 Generate Psychedelic Videos", variant="primary")

        log_console = gr.Textbox(label="Execution Logs", lines=15, interactive=False)

        generate_btn.click(
            generate_video,
            inputs=[youtube_url, speaker_id, style, count, prompt_style, tts_voice, visual, original_voice],
            outputs=[log_console]
        )

    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)
