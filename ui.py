import gradio as gr
import subprocess
import os

def generate_video(youtube_url, speaker_id, suno_tags, prompt_style, tts_voice, subtitle_style, video_filter):
    """
    Executes the auto_run.py script passing the UI parameters.
    Yields output lines dynamically so the user can see progress in the UI.
    """
    cmd = [
        "python", "auto_run.py",
        "--url", youtube_url,
        "--speaker", speaker_id,
        "--tags", suno_tags,
        "--prompt-style", prompt_style,
        "--voice", tts_voice,
        "--subtitle-style", subtitle_style,
        "--video-filter", video_filter
    ]

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
        gr.Markdown("Automated, high-performance content pipeline converting YouTube speech to audio-reactive music videos.")

        with gr.Row():
            with gr.Column():
                youtube_url = gr.Textbox(label="YouTube URL", placeholder="https://www.youtube.com/watch?v=...", info="The video containing the speech to extract.")
                speaker_id = gr.Textbox(label="Target Speaker ID", value="SPEAKER_01", info="WhisperX diarization ID (usually SPEAKER_00 for host, SPEAKER_01 for guest).")
                suno_tags = gr.Textbox(label="Suno Music Tags", value="psytrance, Goa trance, Ajja style, 145 bpm, rolling bassline, acid squelches, hypnotic tribal percussion, continuous groove, instrumental", info="Prompt tags for local Suno API generation.")

            with gr.Column():
                prompt_style = gr.Textbox(label="LLM Prompt Style", value="rhythmic spoken-word stanzas", info="Instructions for DeepSeek to format the transcript.")
                tts_voice = gr.Dropdown(label="Kokoro TTS Voice", choices=["af_heart", "af_bella", "am_adam", "am_michael"], value="af_heart", info="Voice profile for synthesis.")
                subtitle_style = gr.Textbox(label="Subtitle Style (FFmpeg force_style)", value="FontName=Arial,FontSize=24,PrimaryColour=&H00FFFF,Bold=1", info="Stylize the burned-in SRT text.")
                video_filter = gr.Textbox(label="Background Video Filter", value="mandelbrot=size=1920x1080:rate=30", info="FFmpeg generative background string.")

        generate_btn = gr.Button("🚀 Generate Psychedelic Videos", variant="primary")

        log_console = gr.Textbox(label="Execution Logs", lines=15, interactive=False)

        generate_btn.click(
            generate_video,
            inputs=[youtube_url, speaker_id, suno_tags, prompt_style, tts_voice, subtitle_style, video_filter],
            outputs=[log_console]
        )

    return app

if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860)