import argparse
import http
import re
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urljoin

from aiohttp import ClientSession, web
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader, Template

BASE_URL = 'https://t.me/s/'
TITLE_LENGTH = 80


class Config(NamedTuple):
    """Application config."""

    host: str
    port: int
    ttl: int


class Feed(NamedTuple):
    """RSS feed."""

    title: str
    description: str
    pub_date: str
    link: str
    author: str


class Rss(NamedTuple):
    """RSS headers."""

    title: str
    description: str
    link: str
    last_build_date: str
    ttl: int
    feeds: list[Feed]


@cache
def get_template() -> Template:
    """Load template from file."""
    template_loader = FileSystemLoader(searchpath=Path(__file__).parent)
    template_env = Environment(  # noqa: S701, content is trusted
        loader=template_loader,
    )
    return template_env.get_template('rss.j2')


async def get_channel_content(url: str) -> str:
    """Get HTML content of channel."""
    async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status != http.HTTPStatus.OK:
                raise web.HTTPNotFound()
            return await response.text()


def parse_content(raw_news: str) -> BeautifulSoup:
    """Parse raw html content to BeautifulSoup object."""
    return BeautifulSoup(raw_news, 'html.parser')


def parse_rss(soup: Tag, url: str, feeds: list[Feed], ttl: int) -> Rss:
    """Extract title, description, link from root tag."""
    return Rss(
        title=soup.find('meta', {'property': 'og:title'})['content'],
        description=soup.find('meta', {'property': 'og:description'})['content'],
        link=url.replace('t.me/s/', 't.me/'),
        last_build_date=datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
        ttl=ttl,
        feeds=feeds,
    )


def parse_reply(reply: Tag) -> str:
    """Parse reply from reply tag."""
    author = reply.find('span', {'class': 'tgme_widget_message_author_name'}).decode_contents()
    text = reply.find('div', {'class': 'tgme_widget_message_text'}).decode_contents()

    return f"""<div class="rsshub-quote">
        <blockquote>
            <p><a href="{reply["href"]}"><b>{author}</b>:</a></p>
            <p>{text}</p>
        </blockquote>
    </div>"""


def parse_image(image: Tag) -> str:
    """Parse image from image tag."""
    image_style = image['style']
    image_link_match = re.search(r"url\('(.*)'\)", image_style)
    if not image_link_match:
        return ''

    image_link = image_link_match.group(1)
    return f'<img src="{image_link}" referrerpolicy="no-referrer">'


def parse_preview(preview: Tag) -> str:
    """Parse preview of inline link."""
    site_name = preview.find('div', {'class': 'link_preview_site_name'}).decode_contents()

    image = preview.find('i', {'class': 'link_preview_image'})
    image_text = ''
    if image:
        image_text = parse_image(image)

    preview_title = preview.find('div', {'class': 'link_preview_title'})
    preview_title_text = '<a href="{href}">{title}</a>'.format(
        href=preview['href'],
        title=preview_title.decode_contents() if preview_title else site_name,
    )

    preview_description = preview.find(
        'div', {'class': 'link_preview_description'},
    )
    preview_description_text = ''

    if preview_description:
        preview_description_text = '<p>{description}</p>'.format(
            description=preview_description.decode_contents(),
        )

    return f"""<blockquote>
        <b>{site_name}</b><br>
        <b>{preview_title_text}</b><br>
        {preview_description_text}
        {image_text}
    </blockquote>"""


def parse_feed(feed_tag: Tag) -> Feed:
    """Parse feed from message tag."""
    text_content = feed_tag.find('div', {'class': 'js-message_text'})
    description = ''
    if text_content:
        description = text_content.decode_contents()

    image = feed_tag.find('a', {'class': 'tgme_widget_message_photo_wrap'})
    if image:
        image_text = parse_image(image)
        description = f'{description}\n{image_text}'

    title = description[:TITLE_LENGTH]
    reply = feed_tag.find('a', {'class': 'tgme_widget_message_reply'})
    preview = feed_tag.find('a', {'class': 'tgme_widget_message_link_preview'})

    if reply:
        description = '{reply_text}\n{description}'.format(
            reply_text=parse_reply(reply),
            description=description,
        )

    if preview:
        description = '{description}\n{preview_text}'.format(
            description=description,
            preview_text=parse_preview(preview),
        )

    author = feed_tag.find('span', {'class': 'tgme_widget_message_from_author'})
    if not author:
        author = feed_tag.find('a', {'class': 'tgme_widget_message_owner_name'})

    return Feed(
        title=f'{title}...',
        description=f'{description}',
        pub_date=feed_tag.find('time', {'class': 'time'})['datetime'],
        link=feed_tag.find('a', {'class': 'tgme_widget_message_date'})['href'],
        author=author.text,
    )


def parse_feeds(soup: BeautifulSoup) -> list[Feed]:
    """Parse feeds from root tag."""
    feeds: list[Feed] = []

    feed_tag: Tag
    for feed_tag in soup.find_all('div', {'class': 'tgme_widget_message_wrap'}):
        feed = parse_feed(feed_tag)
        feeds.append(feed)

    return feeds


def render_rss(rss: Rss) -> str:
    """Render rss in RSS format."""
    template = get_template()
    return template.render(rss=rss)


async def get_rss_feed(channel: str, config: Config) -> str:
    """Get RSS feed from telegram channel in specified format."""
    url = urljoin(BASE_URL, channel)

    channel_content = await get_channel_content(url)
    soup = parse_content(channel_content)

    feeds = parse_feeds(soup)
    rss = parse_rss(soup, url, feeds, config.ttl)

    return render_rss(rss)


async def handler(request: web.Request) -> web.Response:  # noqa: WPS110, service has one handler
    """Get feed from telegram channel."""
    channel: str = request.match_info['channel']
    config: Config = request.app['config']

    rss_content = await get_rss_feed(channel, config)
    return web.Response(body=rss_content, content_type='application/xml')


def parse_args() -> Config:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='tfeed',
        description='Get RSS feed from public telegram channel without API key.',
    )
    parser.add_argument('--host', default='localhost', help='Host')
    parser.add_argument('--port', default=80, type=int, help='Port')  # noqa: WPS432, it's port
    parser.add_argument('--ttl', default=1, type=int, help='Cache TTL (in minutes)')
    args = parser.parse_args()
    return Config(host=args.host, port=args.port, ttl=args.ttl)


def create_app(config: Config) -> web.Application:
    """Create aiohttp application."""
    app = web.Application()
    route = web.get('/{channel}', handler)
    app.add_routes([route])
    app['config'] = config
    return app


if __name__ == '__main__':
    config = parse_args()
    app = create_app(config)
    web.run_app(app, host=config.host, port=config.port)
