import pytest
from bs4 import BeautifulSoup

from tfeed.app import TITLE_LENGTH, Feed, parse_feed


def generate_preview(
    site_name: str,
    link: str,
    description: str,
    title: str | None = None,
    image: str | None = None,
) -> tuple[str, str]:
    """Generate preview."""
    image_text = ''
    image_feed = ''
    title_text = f'<div class="link_preview_title" dir="auto">{title}</div>' if title else ''

    if image:
        image_text = f'<i class="link_preview_image" style="background-image:url(\'{image}\')"></i>'
        image_feed = f'<img src="{image}" referrerpolicy="no-referrer">'

    preview_text = f"""
        <a class="tgme_widget_message_link_preview" href="{link}">
        {title_text}
        <div class="link_preview_site_name accent_color" dir="auto">{site_name}</div>
        {image_text}
        <div class="link_preview_description" dir="auto">{description}</div>
        </a>
    """

    preview_feed = f"""\n<blockquote>
        <b>{site_name}</b><br>
        <b><a href="{link}">{title if title else site_name}</a></b><br>
        <p>{description}</p>
        {image_feed}
    </blockquote>"""

    return preview_text, preview_feed


def generate_reply(
    text: str,
    author: str,
    link: str,
) -> tuple[str, str]:
    """Generate reply."""
    reply_text = f"""
        <a class="tgme_widget_message_reply" href="{link}" >
            <div class="tgme_widget_message_author accent_color">
                <span class="tgme_widget_message_author_name">{author}</span>
            </div>
            <div class="tgme_widget_message_text js-message_reply_text">{text}</div>
        </a>
    """

    reply_feed = f"""<div class="rsshub-quote">
        <blockquote>
            <p><a href="{link}"><b>{author}</b>:</a></p>
            <p>{text}</p>
        </blockquote>
    </div>\n"""

    return reply_text, reply_feed


def generate_test(  # noqa: PLR0913, too many arguments, but it's ok for test
    description: str,
    pub_date: str,
    link: str,
    author: str,
    images: list[str] | None = None,
    reply: tuple[str, str] | None = None,
    preview: tuple[str, str] | None = None,
    video: str | None = None,
) -> tuple[str, Feed]:
    """Generate test."""
    reply = reply or ('', '')
    preview = preview or ('', '')
    images = images or []
    title = description[:TITLE_LENGTH]

    image_text = ''.join(
        f'<a class="tgme_widget_message_photo_wrap" style="background-image:url(\'{image}\')"></a>'
        for image in images
    )

    image_feed = '\n'.join(
        f'<img src="{image}" referrerpolicy="no-referrer">'
        for image in images
    )

    video_text = ''
    video_feed = ''
    if video:
        video_text = f"""
            <a
                class="tgme_widget_message_video_player js-message_video_player"
                href="https://t.me/channel/0"><i class="tgme_widget_message_video_thumb"
                style="background-image:url('https://cdn4.telegram-cdn.org/file/preview_image')
            "></i>
            <div class="tgme_widget_message_video_wrap">
                <video
                    src="https://cdn4.telegram-cdn.org/file/{video}.mp4?token=token"
                    class="tgme_widget_message_video js-message_video"
                ></video>
            </div>
            </a>
        """
        video_feed = (
            '\n<p><b>The message contain video, for watch it please visit the channel.</b></p>'
        )

    raw_feed = f"""
        <div class="tgme_widget_message_wrap js-widget_message_wrap">
            <div class="tgme_widget_message text_not_supported_wrap js-widget_message">
            <div class="tgme_widget_message_bubble">
            <div class="tgme_widget_message_author accent_color">
                <a class="tgme_widget_message_owner_name" href="https://t.me/channel">{author}</a>
            </div>
            <div class="tgme_widget_message_grouped_wrap js-message_grouped_wrap">
                <div class="tgme_widget_message_grouped js-message_grouped">
                    <div class="tgme_widget_message_grouped_layer js-message_grouped_layer">
                        {image_text}
                    </div>
                </div>
            </div>
            <div class="tgme_widget_message_text js-message_text" dir="auto">
                <div class="tgme_widget_message_text js-message_text" dir="auto">{description}</div>
            </div>
            {reply[0]}
            {preview[0]}
            {video_text}
            <div class="tgme_widget_message_footer compact js-message_footer">
                <div class="tgme_widget_message_info short js-message_info">
                    <span class="tgme_widget_message_meta">
                        <a class="tgme_widget_message_date" href="{link}">
                            <time class="time" datetime="{pub_date}">00:00</time>
                        </a>
                    </span>
                </div>
            </div>
            </div>
            </div>
        </div>
"""
    if images:
        description += f'\n{image_feed}'

    description = f'{reply[1]}{description}{video_feed}{preview[1]}'

    feed = Feed(
        title=f'{title}...',
        description=description,
        pub_date=pub_date,
        link=link,
        author=author,
    )

    return raw_feed, feed


def test_parse_simple_feed() -> None:
    """Test parse_feed."""
    feed_raw, feed = generate_test(
        description='Test description',
        pub_date='2021-01-01T00:00:00+00:00',
        link='https://t.me/channel/1',
        author='Test author',
    )

    assert parse_feed(BeautifulSoup(feed_raw, 'html.parser')) == feed


@pytest.mark.parametrize(
    'images', [
        [],
        ['image_0'],
        ['image_0', 'image_1'],
        ['image_0', 'image_1', 'image_2'],
    ],
)
def test_parse_feed_with_image(images: list[str]) -> None:
    """Test parse_feed."""
    feed_raw, feed = generate_test(
        description='Test description',
        pub_date='2021-01-01T00:00:00+00:00',
        link='https://t.me/channel/1',
        author='Test author',
        images=images,
    )

    assert parse_feed(BeautifulSoup(feed_raw, 'html.parser')) == feed


def test_parse_feed_with_reply() -> None:
    """Test parse_feed."""
    reply = generate_reply(
        text='Test reply',
        author='Test reply author',
        link='https://t.me/channel/1',
    )
    feed_raw, feed = generate_test(
        description='Test description',
        pub_date='2021-01-01T00:00:00+00:00',
        link='https://t.me/channel/1',
        author='Test author',
        reply=reply,
    )

    assert parse_feed(BeautifulSoup(feed_raw, 'html.parser')) == feed


@pytest.mark.parametrize(
    ('image','title'), [
        ('image_0', 'Test preview title'),
        (None, 'Test preview title'),
        ('image_0', None),
        (None, None),
    ],
)
def test_parse_feed_with_preview(title: str | None, image: str | None) -> None:
    """Test parse_feed."""
    preview = generate_preview(
        site_name='Test preview site name',
        description='Test preview description',
        title=title,
        image=image,
        link='https://google.com',
    )

    feed_raw, feed = generate_test(
        description='Test description',
        pub_date='2021-01-01T00:00:00+00:00',
        link='https://t.me/channel/1',
        author='Test author',
        preview=preview,
    )

    assert parse_feed(BeautifulSoup(feed_raw, 'html.parser')) == feed


def test_parse_feed_with_video() -> None:
    """Test parse_feed."""
    feed_raw, feed = generate_test(
        description='Test description',
        pub_date='2021-01-01T00:00:00+00:00',
        link='https://t.me/channel/1',
        author='Test author',
        video='video',
    )

    assert parse_feed(BeautifulSoup(feed_raw, 'html.parser')) == feed


def test_parse_feed_with_reply_preview_video() -> None:
    """Test parse_feed."""
    reply = generate_reply(
        text='Test reply',
        author='Test reply author',
        link='https://t.me/channel/1',
    )
    preview = generate_preview(
        site_name='Test preview site name',
        description='Test preview description',
        title='Test preview title',
        image='image_0',
        link='https://google.com',
    )

    feed_raw, feed = generate_test(
        description='Test description',
        pub_date='2021-01-01T00:00:00+00:00',
        link='https://t.me/channel/1',
        author='Test author',
        reply=reply,
        preview=preview,
        video='video',
    )

    assert parse_feed(BeautifulSoup(feed_raw, 'html.parser')) == feed
