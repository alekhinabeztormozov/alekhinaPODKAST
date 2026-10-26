from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from config import Settings
from media import sfx
from reels import conveyor, publish, render, scenarios, store
from reels.render import loudest_start
from reels.subtitles import Word, ass_time, build_ass, group_lines, words_from_segments

SCENARIO = {
    "kind": "why_buy",
    "title": "Почему мы любим <картошку>",
    "trigger": "вкус из детства",
    "hook": "Вы не голодны, но берете фри",
    "scenes": [
        {"seconds": 3, "voiceover": "Вы не голодны.", "on_screen": "ЗАЧЕМ ФРИ?", "visual": "крупный план"},
        {"seconds": 20, "voiceover": "Срабатывает запах.", "on_screen": "", "visual": "шляпа-фри"},
    ],
    "lyrics": "",
    "hat": "шляпа в форме картошки фри",
    "caption": "Почему фри берут сытыми. Подробнее в выпуске",
    "hashtags": ["нейромаркетинг", "#макдоналдс", "бизнес идеи"],
}


class FakeBot:
    def __init__(self) -> None:
        self.videos: list[tuple] = []
        self.messages: list[tuple] = []

    async def send_video(self, chat_id, video, **kwargs):
        self.videos.append((chat_id, kwargs.get("caption", "")))

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text))


def test_ass_time_format():
    assert ass_time(0) == "0:00:00.00"
    assert ass_time(75.456) == "0:01:15.46"
    assert ass_time(3661.5) == "1:01:01.50"


def test_group_lines_splits_on_size_punctuation_and_pause():
    words = [
        Word(0.0, 0.3, "Вы"), Word(0.3, 0.6, "не"), Word(0.6, 0.9, "голодны."),
        Word(1.0, 1.3, "Но"), Word(2.5, 2.8, "берете"), Word(2.8, 3.1, "фри"),
    ]
    lines = [[word.text for word in line] for line in group_lines(words)]
    assert lines == [["Вы", "не", "голодны."], ["Но"], ["берете", "фри"]]


def test_build_ass_has_hook_and_karaoke_upper():
    ass = build_ass([Word(0.5, 1.0, "привет{x}")], hook="Хук")
    assert "Style: Sub,Oswald" in ass
    assert "Hook,,0,0,0,,ХУК" in ass
    assert "{\\kf50}ПРИВЕТ(X)" in ass


def test_words_from_segments_spreads_evenly():
    words = words_from_segments([{"start": 0, "end": 2, "text": "раз два"}])
    assert [(word.start, word.end, word.text) for word in words] == [(0, 1, "раз"), (1, 2, "два")]


def test_loudest_start_finds_peak_window():
    levels = [-60, -60, -20, -10, -10, -60, -60]
    assert loudest_start(levels, 3) == 2.0
    assert loudest_start([-10, -10], 5) == 0.0


def test_default_counts_keeps_total():
    assert scenarios.default_counts(6) == {"why_buy": 3, "trigger_song": 2, "carousel": 1}
    assert scenarios.default_counts(1) == {"why_buy": 0, "trigger_song": 1, "carousel": 0}


def test_card_text_escapes_html():
    card = scenarios.card_text(SCENARIO)
    assert "&lt;картошку&gt;" in card
    assert "[ЗАЧЕМ ФРИ?]" in card
    assert "#нейромаркетинг #макдоналдс" in card


def test_build_request_includes_examples(tmp_path, monkeypatch):
    (tmp_path / "1.txt").write_text("Пример сценария Юлии", encoding="utf-8")
    monkeypatch.setattr(scenarios, "EXAMPLES_DIR", tmp_path)
    prompt = scenarios.build_request("Мак Э2", "расшифровка", {"why_buy": 4, "trigger_song": 2})
    assert "why_buy: 4, trigger_song: 2" in prompt
    assert "Пример сценария Юлии" in prompt
    assert prompt.endswith("расшифровка")


def test_voiceover_text_joins_scenes():
    assert scenarios.voiceover_text(SCENARIO) == "Вы не голодны. Срабатывает запах."


def test_post_text_normalizes_hashtags():
    assert publish.post_text(SCENARIO).endswith("#нейромаркетинг #макдоналдс #бизнес_идеи")


def test_next_free_slot_skips_taken_and_past():
    slots = [(12, 0), (19, 0)]
    after = datetime(2026, 10, 26, 10, 0, tzinfo=store.MSK).astimezone(UTC)
    first = store.next_free_slot(after, slots, set())
    assert first == datetime(2026, 10, 26, 12, 0, tzinfo=store.MSK).astimezone(UTC)
    second = store.next_free_slot(after, slots, {first})
    assert second == datetime(2026, 10, 26, 19, 0, tzinfo=store.MSK).astimezone(UTC)
    late = datetime(2026, 10, 26, 20, 0, tzinfo=store.MSK).astimezone(UTC)
    assert store.next_free_slot(late, slots, set()).astimezone(store.MSK).day == 27


async def test_approve_song_waits_for_track(db):
    song = {**SCENARIO, "kind": "trigger_song"}
    why_id, song_id = await store.add_drafts("mac-e2", "Мак Э2", [SCENARIO, song])
    assert (await store.approve(why_id)).status == store.APPROVED
    assert (await store.approve(song_id)).status == store.NEED_TRACK
    await store.update(song_id, track_path="t.mp3")
    assert (await store.approve(song_id)).status == store.APPROVED
    assert await store.counts() == {store.APPROVED: 2}


async def test_schedule_takes_consecutive_slots(db):
    first, second = await store.add_drafts("mac-e2", "Мак Э2", [SCENARIO, SCENARIO])
    now = datetime(2026, 10, 26, 10, 0, tzinfo=store.MSK).astimezone(UTC)
    slot_one = await store.schedule(first, [(12, 0), (19, 0)], now)
    slot_two = await store.schedule(second, [(12, 0), (19, 0)], now)
    assert slot_two - slot_one == timedelta(hours=7)


async def test_publish_due_reels_sends_to_channel_and_owner(db, tmp_path, monkeypatch):
    video = tmp_path / "reel.mp4"
    video.write_bytes(b"fake")
    (reel_id,) = await store.add_drafts("mac-e2", "Мак Э2", [SCENARIO])
    past = datetime.now(UTC) - timedelta(minutes=1)
    await store.update(reel_id, status=store.READY, publish_at=past, video_path=str(video))
    monkeypatch.setattr(publish, "FSInputFile", lambda path: path)
    settings = Settings(open_channel_id="@open", admin_tg_ids="1", reels_targets="tg,vk,ig", bot_token="x")
    monkeypatch.setattr(publish, "get_settings", lambda: settings)

    bot = FakeBot()
    assert await conveyor.publish_due_reels(bot, settings) == 1

    reel = await store.get(reel_id)
    assert reel.status == store.PUBLISHED
    assert reel.published == ["tg", "ig"]
    assert "vk" in reel.error
    assert bot.videos[0][0] == "@open"
    assert bot.videos[1][0] == 1
    assert any("вышел не везде" in text for _, text in bot.messages)


async def test_weekly_report_counts_published(db):
    from reels.report import weekly_report_text

    (reel_id,) = await store.add_drafts("mac-e2", "Мак Э2", [SCENARIO])
    await store.update(reel_id, status=store.PUBLISHED, published=["tg", "ig"])
    await store.add_drafts("mac-e3", "Мак Э3", [SCENARIO])
    text = await weekly_report_text()
    assert "Роликов вышло: 1" in text
    assert "(Telegram, Instagram)" in text
    assert "Сценариев ждут вашей проверки: 1" in text


def test_song_visual_picks_first_media(tmp_path, monkeypatch):
    monkeypatch.setattr(conveyor, "SONG_VISUALS_DIR", tmp_path)
    assert conveyor.song_visual() is None
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "b.png").write_bytes(b"x")
    (tmp_path / "a.jpg").write_bytes(b"x")
    assert conveyor.song_visual() == Path(tmp_path / "a.jpg")


def test_idea_request_puts_image_first():
    content = scenarios.idea_request("Ваза на стене", b"jpg", "- Мак Э2")
    assert [block["type"] for block in content] == ["image", "text"]
    assert content[0]["source"]["data"] == "anBn"
    assert "Ваза на стене" in content[1]["text"]
    assert "- Мак Э2" in content[1]["text"]


def test_idea_request_text_only():
    content = scenarios.idea_request("Шоколад внутри", None, "")
    assert len(content) == 1
    assert "Выпуски подкаста" not in content[0]["text"]


def test_scene_offsets_scale_to_real_length():
    scenes = [{"seconds": 5}, {"seconds": 10}, {"seconds": 5}]
    assert conveyor.scene_offsets(scenes, 40.0) == [0.0, 10.0, 30.0]


def test_scene_offsets_without_plan_start_at_zero():
    assert conveyor.scene_offsets([{"seconds": 0}, {}], 30.0) == [0.0, 0.0]


async def test_scene_sounds_skip_without_key():
    settings = Settings(elevenlabs_api_key="")
    scenario = {**SCENARIO, "scenes": [{**SCENARIO["scenes"][0], "sfx": "cash register ding"}]}
    assert await conveyor.scene_sounds(settings, scenario, 20.0) == []


async def test_scene_sounds_place_sound_at_its_scene(tmp_path, monkeypatch):
    calls = []

    async def fake_generate(description, seconds=None):
        calls.append(description)
        return tmp_path / "ding.mp3"

    monkeypatch.setattr(conveyor, "generate_sound", fake_generate)
    scenes = [SCENARIO["scenes"][0], {**SCENARIO["scenes"][1], "sfx": "chips bag crunch"}]
    sounds = await conveyor.scene_sounds(Settings(elevenlabs_api_key="key"), {**SCENARIO, "scenes": scenes}, 46.0)
    assert calls == ["chips bag crunch"]
    assert sounds == [(tmp_path / "ding.mp3", 6.0)]


def test_card_text_marks_sound():
    scenario = {**SCENARIO, "scenes": [{**SCENARIO["scenes"][0], "sfx": "cash register ding"}]}
    assert "🔊 cash register ding" in scenarios.card_text(scenario)


def test_avatar_audio_chain_mixes_delayed_sounds():
    chain = render.avatar_audio_chain([0.0, 6.5])
    assert "[2:a]adelay=6500|6500" in chain
    assert "amix=inputs=3" in chain
    assert render.avatar_audio_chain([]).startswith("[0:a]loudnorm")


def test_sfx_cache_path_ignores_case_and_spaces():
    assert sfx.sfx_path(" Cash Register ", 2) == sfx.sfx_path("cash register", 2.0)
    assert sfx.sfx_path("cash register", 2) != sfx.sfx_path("cash register", None)


def test_sound_request_clamps_duration():
    assert sfx.sound_request("ding", 60)["duration_seconds"] == sfx.MAX_SECONDS
    assert "duration_seconds" not in sfx.sound_request("ding", None)
