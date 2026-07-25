#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://down.mptext.top';

function usage() {
  console.error(`Usage:
  node mptext_fetch.js --account "公众号名称" --from 2025-06-05 --to 2026-06-05 --out work/articles.json
  node mptext_fetch.js --fakeid MTkyNTM0MzA4MQ== --from 2025-06-05 --to 2026-06-05 --keyword AI

Options:
  --auth-key <key>       MPText API key. Prefer env MPTEXT_AUTH_KEY.
  --account <keyword>    Official account nickname or alias keyword.
  --fakeid <fakeid>      Account fakeid; skips account search.
  --from YYYY-MM-DD      Inclusive start date in Asia/Shanghai.
  --to YYYY-MM-DD        Inclusive end date in Asia/Shanghai.
  --keyword <keyword>    Optional article title keyword for article-list API.
  --out <path>           Output JSON path. Defaults to work/mptext_articles.json.
  --no-download          Fetch metadata only.
  --concurrency <n>      Body download concurrency. Defaults to 4.
  --max-pages <n>        Max article-list pages. Defaults to 50.
`);
}

function parseArgs(argv) {
  const args = {
    authKey: process.env.MPTEXT_AUTH_KEY || '',
    account: '',
    fakeid: '',
    from: '',
    to: '',
    keyword: '',
    out: 'work/mptext_articles.json',
    download: true,
    concurrency: 4,
    maxPages: 50,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => argv[++i] || '';
    if (arg === '--auth-key') args.authKey = next();
    else if (arg === '--account') args.account = next();
    else if (arg === '--fakeid') args.fakeid = next();
    else if (arg === '--from') args.from = next();
    else if (arg === '--to') args.to = next();
    else if (arg === '--keyword') args.keyword = next();
    else if (arg === '--out') args.out = next();
    else if (arg === '--no-download') args.download = false;
    else if (arg === '--concurrency') args.concurrency = Math.max(1, Number(next()) || 4);
    else if (arg === '--max-pages') args.maxPages = Math.max(1, Number(next()) || 50);
    else if (arg === '--help' || arg === '-h') {
      usage();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!args.authKey) throw new Error('Missing API key. Use --auth-key or env MPTEXT_AUTH_KEY.');
  if (!args.fakeid && !args.account) throw new Error('Provide --account or --fakeid.');
  if (!args.from || !args.to) throw new Error('Provide --from and --to.');
  return args;
}

function epochStartShanghai(date) {
  return Math.floor(new Date(`${date}T00:00:00+08:00`).getTime() / 1000);
}

function epochEndShanghai(date) {
  return Math.floor(new Date(`${date}T23:59:59+08:00`).getTime() / 1000);
}

function formatShanghai(epochSeconds) {
  const d = new Date(epochSeconds * 1000 + 8 * 60 * 60 * 1000);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
}

async function apiJson(pathname, authKey) {
  const res = await fetch(`${BASE_URL}${pathname}`, {
    headers: { 'X-Auth-Key': authKey },
  });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`Expected JSON from ${pathname}, got HTTP ${res.status}: ${text.slice(0, 200)}`);
  }
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${pathname}: ${text.slice(0, 200)}`);
  return json;
}

async function apiText(pathname, authKey) {
  const res = await fetch(`${BASE_URL}${pathname}`, {
    headers: { 'X-Auth-Key': authKey },
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${pathname}: ${text.slice(0, 200)}`);
  return text;
}

async function validateKey(authKey) {
  const json = await apiJson('/api/public/v1/authkey', authKey);
  if (json.code !== 0) throw new Error(`Invalid or expired MPText API key: ${JSON.stringify(json)}`);
}

async function resolveAccount(args) {
  if (args.fakeid) {
    return { fakeid: args.fakeid, nickname: '', alias: '', candidates: [] };
  }

  const json = await apiJson(`/api/public/v1/account?keyword=${encodeURIComponent(args.account)}`, args.authKey);
  const list = json.list || [];
  if (!list.length) throw new Error(`No account found for keyword: ${args.account}`);

  const exact =
    list.find((item) => item.nickname === args.account) ||
    list.find((item) => item.alias === args.account) ||
    list[0];

  return {
    fakeid: exact.fakeid,
    nickname: exact.nickname,
    alias: exact.alias,
    candidates: list.map((item) => ({
      fakeid: item.fakeid,
      nickname: item.nickname,
      alias: item.alias,
      signature: item.signature,
      verify_status: item.verify_status,
    })),
  };
}

async function fetchArticleList(args, account) {
  const fromTs = epochStartShanghai(args.from);
  const toTs = epochEndShanghai(args.to);
  const all = [];

  for (let page = 0; page < args.maxPages; page += 1) {
    const begin = page * 20;
    let url = `/api/public/v1/article?fakeid=${encodeURIComponent(account.fakeid)}&begin=${begin}&size=20`;
    if (args.keyword) url += `&keyword=${encodeURIComponent(args.keyword)}`;

    const json = await apiJson(url, args.authKey);
    const articles = json.articles || [];
    if (!articles.length) break;

    all.push(...articles);

    const minTs = Math.min(...articles.map((item) => item.update_time || item.create_time || 0));
    if (minTs < fromTs) break;
    await sleep(250);
  }

  return all
    .filter((article) => !article.is_deleted)
    .filter((article) => {
      const ts = article.update_time || article.create_time || 0;
      return ts >= fromTs && ts <= toTs;
    })
    .map((article) => ({
      aid: article.aid,
      title: article.title,
      link: article.link,
      digest: article.digest || '',
      update_time: article.update_time,
      create_time: article.create_time,
      datetime: formatShanghai(article.update_time || article.create_time),
      author_name: article.author_name || '',
      itemidx: article.itemidx,
      item_show_type: article.item_show_type,
      copyright_type: article.copyright_type,
    }));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function downloadBodies(args, articles) {
  let next = 0;
  let failed = 0;
  const results = articles.map((article) => ({ ...article, text: '' }));

  async function worker() {
    while (next < articles.length) {
      const index = next;
      next += 1;
      const article = articles[index];
      try {
        const text = await apiText(
          `/api/public/v1/download?url=${encodeURIComponent(article.link)}&format=text`,
          args.authKey,
        );
        results[index].text = text;
        results[index].text_length = text.length;
      } catch (error) {
        failed += 1;
        results[index].download_error = error.message;
        results[index].text_length = 0;
      }
      if ((index + 1) % 20 === 0 || index + 1 === articles.length) {
        console.error(`downloaded ${index + 1}/${articles.length}, failed=${failed}`);
      }
      await sleep(150);
    }
  }

  await Promise.all(Array.from({ length: args.concurrency }, () => worker()));
  return { articles: results, failed };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  await validateKey(args.authKey);
  const account = await resolveAccount(args);
  const articles = await fetchArticleList(args, account);

  let finalArticles = articles;
  let downloadFailed = 0;
  if (args.download) {
    const downloaded = await downloadBodies(args, articles);
    finalArticles = downloaded.articles;
    downloadFailed = downloaded.failed;
  }

  const output = {
    source: 'mptext',
    base_url: BASE_URL,
    account,
    request: {
      account: args.account,
      fakeid: args.fakeid || account.fakeid,
      from: args.from,
      to: args.to,
      keyword: args.keyword,
      downloaded_bodies: args.download,
    },
    stats: {
      article_count: finalArticles.length,
      download_failed: downloadFailed,
      image_or_short_text_count: finalArticles.filter((article) => (article.text_length || 0) < 100).length,
    },
    articles: finalArticles,
  };

  fs.mkdirSync(path.dirname(args.out), { recursive: true });
  fs.writeFileSync(args.out, JSON.stringify(output, null, 2), 'utf8');
  console.log(JSON.stringify(output.stats, null, 2));
  console.error(`saved ${args.out}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
