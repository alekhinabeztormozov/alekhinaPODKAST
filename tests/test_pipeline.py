from __future__ import annotations

from pathlib import Path

from media.pipeline import AudioProfile, PipelineInputs, build_filter_complex


def test_voice_only_no_concat_no_mix():
    filt, label = build_filter_complex(PipelineInputs(voice=Path("v.mp3")))
    assert label == "[out]"
    assert "anull[body]" in filt
    assert "concat" not in filt
    assert "sidechaincompress" not in filt


def test_music_adds_ducking_and_split():
    filt, _ = build_filter_complex(PipelineInputs(voice=Path("v.mp3"), music=Path("m.mp3")))
    assert "asplit=2[vmain][vside]" in filt
    assert "sidechaincompress" in filt
    assert "amix=inputs=2:duration=first:normalize=0[body]" in filt


def test_intro_outro_concat_three():
    filt, _ = build_filter_complex(
        PipelineInputs(voice=Path("v.mp3"), intro=Path("i.mp3"), outro=Path("o.mp3"))
    )
    assert "concat=n=3:v=0:a=1[cat]" in filt


def test_loudnorm_always_last():
    profile = AudioProfile()
    filt, _ = build_filter_complex(PipelineInputs(voice=Path("v.mp3"), profile=profile))
    assert f"loudnorm=I={profile.loudness_i}" in filt


def test_input_order_matches_indices():
    inp = PipelineInputs(
        voice=Path("v.mp3"), intro=Path("i.mp3"), music=Path("m.mp3"), outro=Path("o.mp3")
    )
    filt, _ = build_filter_complex(inp)
    assert filt.startswith("[0:a]aformat")
    assert "[3:a]aformat" in filt


def test_voice_cleanup_applies_only_to_voice():
    profile = AudioProfile()
    filt, _ = build_filter_complex(
        PipelineInputs(voice=Path("v.mp3"), intro=Path("i.mp3"), profile=profile)
    )
    voice_part = next(part for part in filt.split(";") if part.endswith("[voicef]"))
    intro_part = next(part for part in filt.split(";") if part.endswith("[introf]"))
    assert profile.voice_cleanup in voice_part
    assert profile.voice_cleanup not in intro_part


def test_voice_cleanup_can_be_disabled():
    filt, _ = build_filter_complex(
        PipelineInputs(voice=Path("v.mp3"), profile=AudioProfile(voice_cleanup=""))
    )
    assert "afftdn" not in filt


def test_intro_and_voice_normalized_separately_before_concat():
    filt, _ = build_filter_complex(PipelineInputs(voice=Path("v.mp3"), intro=Path("i.mp3")))
    assert "[introf]loudnorm" in filt
    assert "[body]loudnorm" in filt
    assert filt.index("[body]loudnorm") < filt.index("concat")
    assert filt.endswith("[out]")


def test_jingle_wraps_clean_voice_without_mixing():
    filt, _ = build_filter_complex(
        PipelineInputs(voice=Path("v.mp3"), intro=Path("i.mp3"), jingle=Path("j.mp3")),
        jingle_end=47.0,
    )
    assert "sidechaincompress" not in filt
    assert "amix" not in filt
    assert "concat=n=4:v=0:a=1[cat]" in filt
    assert filt.index("[introfn]") < filt.index("[jopenn]") < filt.index("[bodyn]") < filt.index("[jclosen]")


def test_jingle_closer_ends_where_track_sound_ends():
    profile = AudioProfile()
    filt, _ = build_filter_complex(
        PipelineInputs(voice=Path("v.mp3"), jingle=Path("j.mp3"), profile=profile), jingle_end=47.0,
    )
    closer_start = 47.0 - profile.jingle_close_seconds
    assert f"atrim={closer_start:.3f}:47.000" in filt
    assert f"[jopenraw]atrim=0:{profile.jingle_open_seconds}" in filt


def test_jingle_normalized_quieter_than_voice():
    profile = AudioProfile()
    filt, _ = build_filter_complex(PipelineInputs(voice=Path("v.mp3"), jingle=Path("j.mp3"), profile=profile))
    assert f"[jopen]loudnorm=I={profile.jingle_loudness_i}" in filt
    assert f"[body]loudnorm=I={profile.loudness_i}" in filt
