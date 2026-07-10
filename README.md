# Money Intel Daily — Blog

Static blog for the [Money Intel Daily](https://www.youtube.com/@MoneyIntelDaily) YouTube channel.
Live at **https://youfuxu.github.io/money-intel-daily/**

- `posts_md/` — source Markdown (`YYYY-MM-DD-slug.md`), copied automatically from
  `intel-bots/output/<session>/blog_post.md` by `intel-bots/core/blog_publisher.py`
  after each successful daily upload.
- `build.py` — rebuilds `posts/`, `index.html`, `feed.xml`, `sitemap.xml`, `robots.txt`.
  Re-run any time; it is idempotent.
- Email edition stays on [Beehiiv](https://moneyintel.beehiiv.com) (manual).

Manual rebuild:

```
python build.py
```
