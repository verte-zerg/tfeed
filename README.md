# Telegram Channel to RSS Feed

This project is a library/service for converting Telegram public channel into a valid RSS feed 
without using API key.

## Requirements
```
python >= 3.9
aiohttp >= 3.8
bs4 >= 4.11
jinja2 >= 3.1
```

## Installation
```bash
pip install poetry && poetry install
```

## Usage
The following command will start the server and the RSS feed can be accessed at 
`http://localhost:8080/<channel_name>`, where `channel_name` - name of the Telegram public channel.

```bash
python rss_feed.py --host=localhost --port=8080
```

or using Docker:

```bash
docker build -t tfeed .
docker run -p 8080:80 tfeed --host=0.0.0.0
```

## Implementation Details
The application uses `aiohttp` for asynchronous HTTP requests and serving, `bs4` to extract 
information from HTML, and `jinja2` to generate XML for an RSS feed.

## Command Line Arguments
- `host`: Hostname for the server (default: `localhost`);
- `port`: Port for the server (default: `80`).
- `ttl`: Time to live for the RSS feed (default: `1`).

## Working
- the application fetches the HTML content of the channel using the `URL` 
`https://t.me/s/<channel_name>`;
- the HTML content is then parsed using `bs4` to extract the title and description of the channel;
- use `bs4` to extract each post as a `Feed` object and group them into `Rss` object; 
- finally, the object is rendered using `jinja2` to generate the RSS feed.

## Result
The resulting RSS feed includes the following information for channel:
- title;
- description;
- link.

And for each post:
- title;
- description (reply, text, image, preview link);
- link;
- author;
- published date.


## TODO
1. Write unit tests
2. Decrease size of docker image (use alpine)
3. Add example of docker-compose with nginx
4. Support video, audio, documents


## License
This project is licensed under the MIT License.
