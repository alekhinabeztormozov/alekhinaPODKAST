from __future__ import annotations

from datetime import UTC, datetime, timedelta

from PIL import Image

from config import Settings
from pdf.carousel import carousel_html, render_carousel
from reels import conveyor, publish, scenarios, store

SLIDES = [
    {"kicker": "Макдоналдс", "title": "Почему дети тянут вас туда?", "text": ""},
    {"kicker": "Триггер", "title": "Сюрприз <внутри>", "text": "Ребенок хочет открыть."},
    {"kicker": "", "title": "Слушайте выпуск", "text": "Напишите боту слово HAPPY."},
]
CAROUSEL = {
    "kind": "carousel", "title": "Детство в коробке", "trigger": "сюрприз", "hook": "Почему дети тянут?",
    "scenes": [], "lyrics": "", "hat": "", "slides": SLIDES,
    "caption": "Разбираем Happy Meal", "hashtags": ["нейромаркетинг"],
}


class FakeBot:
    def __init__(self) -> None:
        self.albums: list[tuple] = []
        self.messages: list[tuple] = []

    async def send_media_group(self, chat_id, media, **kwargs):
        self.albums.append((chat_id, len(media), media[0].caption))

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text))


def test_html_has_cover_body_and_cta():
    html = carousel_html(SLIDES, "AlekhinaU_bot")
    assert html.count('<section class="slide') == 3
    assert "<h1>Почему дети тянут вас туда?</h1>" in html
    assert "Сюрприз &lt;внутри&gt;" in html
    assert '<div class="cta">@AlekhinaU_bot</div>' in html
    assert "2/3" in html


def test_render_makes_png_per_slide(tmp_path):
    images = render_carousel(SLIDES, tmp_path, "AlekhinaU_bot")
    assert [path.name for path in images] == ["slide_01.png", "slide_02.png", "slide_03.png"]
    assert Image.open(images[0]).size == (1080, 1350)
    assert not (tmp_path / "slide.pdf").exists()


def test_card_lists_slides():
    card = scenarios.card_text(CAROUSEL)
    assert "Карусель: Детство в коробке" in card
    assert "Слайд 2: <b>Сюрприз &lt;внутри&gt;</b> - Ребенок хочет открыть." in card


async def test_carousel_goes_from_approval_to_album(db, tmp_path, monkeypatch):
    monkeypatch.setattr(conveyor, "REELS_DIR", tmp_path)
    settings = Settings(open_channel_id="@open", admin_tg_ids="1", report_tg_ids="2", reels_targets="tg,ig")
    monkeypatch.setattr(publish, "get_settings", lambda: settings)
    (reel_id,) = await store.add_drafts("mac-e3", "Мак Э3", [CAROUSEL])
    assert (await store.approve(reel_id)).status == store.APPROVED

    bot = FakeBot()
    assert await conveyor.start_renders(bot, settings) == 1
    reel = await store.get(reel_id)
    assert reel.status == store.READY
    assert len(publish.slide_paths(conveyor.Path(reel.video_path))) == 3
    assert bot.albums[0][0] == 2

    await store.update(reel_id, publish_at=datetime.now(UTC) - timedelta(minutes=1))
    assert await conveyor.publish_due_reels(bot, settings) == 1
    reel = await store.get(reel_id)
    assert reel.published == ["tg", "ig"]
    assert ("@open", 3) == bot.albums[1][:2]
    assert bot.albums[1][2].startswith("Разбираем Happy Meal")
