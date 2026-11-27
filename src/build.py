#!/usr/bin/env python3
"""Render data.json into index.html.

Usage: python3 -I /home/claude/site/build.py
Every string from data.json is HTML-escaped. No game material, links to it, or instructions are emitted.

Design: redesigned on 23 Nov 2026 to the written rules of the "design-taste-frontend" skill (tasteskill 2.5.1,
public copy), built by hand: the skill's own scripts and kit files are not used here.
Deal, drawn at random from the skill's libraries: palette stone-blueprint, type onest (Onest with JetBrains
Mono), radius sharp, buttons tonal, mark initial, nav-centre (nav-mega was dealt; it needs a photograph for
its panel and the page has none), footer-statement, close-word, rhythm dark-band (the forecast section).
Rules kept: one accent, sentence case, text 16px and up, labels 13px, nothing under 13px, one button pair,
one row recipe, equal edges on one 12-column grid, the hero alone on the first screen, no fade-in on scroll.

Added 25 Nov 2026 from the repository's issues and pull requests: every clock time is a <time data-t> that
page.js can show in the reader's own zone (issue 5, pull request 7), a note on how to ask for a change, and a
link to star the page's repository (the secondary button, with a star count read at build time from stars.txt).

Added 25 Nov 2026 from issue 8: three lanes (picture, speed, stability) under the stage meter of every project
that is in-game, each step read from what the project reports, and a key to them under the section's title.
Since 13:30 UTC that day the rows of the in-game stage are ordered by those lanes alone (rank_key below): the
order in data.json and its "pos" values no longer place them, and the hero names whichever project comes first.
"""
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Optional arguments, for previews: build.py [data file] [output file]
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "data.json"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "index.html"
data = json.loads(DATA.read_text(encoding="utf-8"))


def esc(value):
    return html.escape(str(value), quote=True)


UNIT = re.compile(r"(\d) (?=(?:GB|MB|UTC|fps|frames?|seconds?|minutes?|hours?|days?|weeks?|in 10|of \d)\b)")


CLOCK = re.compile(r"\b(\d{1,2}):(\d{2})\b(?: UTC(?: on (\d{1,2}) (Nov|November|Dec|December)\b)?)?")
MONTH_NO = {"Nov": 11, "November": 11, "Dec": 12, "December": 12}


def txt(value, base=None):
    """Escaped prose in which a number never breaks from its unit, and in which every clock time is a <time>
    element that page.js can show in the reader's own zone (asked for in a follow-up on issue 5). The prose
    states its times in UTC. "base" is the stamp of the entry the prose belongs to: it dates a clock time that
    is written without a day."""
    ref = parse(base or data["checked"])

    def wrap(m):
        hour, minute = int(m.group(1)), int(m.group(2))
        if hour > 23 or minute > 59:
            return m.group(0)
        kind = "clock-bare"
        try:
            when = ref.replace(hour=hour, minute=minute, second=0)
            if " UTC" in m.group(0):
                kind = "clock"
            if m.group(3):
                kind = "clock-day"
                when = when.replace(month=MONTH_NO[m.group(4)], day=int(m.group(3)))
        except ValueError:
            return m.group(0)
        return f'<time datetime="{when.strftime("%Y-%m-%dT%H:%M:%SZ")}" data-t="{kind}">{m.group(0)}</time>'

    return UNIT.sub("\\1&nbsp;", CLOCK.sub(wrap, esc(value)))


SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
URL = re.compile(r"^https://[A-Za-z0-9.-]+/[A-Za-z0-9_./-]+$")


def repo_href(repo, url=None):
    """Address of a project's public source repository, or None. An explicit https "url" wins over the slug."""
    if url and URL.match(url):
        return url
    if SLUG.match(repo):
        return f"https://github.com/{repo}"
    return None


def name_link(repo, text, url=None, link=True):
    """A project's name, linked to its repository unless the entry says it has none to link to."""
    href = repo_href(repo, url) if link else None
    if not href:
        return esc(text)
    return f'<a class="name" href="{esc(href)}" rel="noopener">{esc(text)}</a>'


def parse(iso):
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def clock(iso):
    return parse(iso).strftime("%H:%M")


def day(iso):
    d = parse(iso)
    return f"{d.day} {d.strftime('%b')}"


stages = data["stages"]
top = len(stages) - 1
fc = data["forecast"]
# data["paused"]: ISO time at which automatic checks were paused; absent while they run. While paused the
# estimate does not count down (page.js leaves a target it cannot read alone) and the copy says so.
PAUSED = data.get("paused")
# fc["met"]: set when a report meets the playable bar: {"t": ISO time of the check that counted it, "line": a sentence
# or two on whose report it is and what nobody has checked}. The estimate then stops counting down (page.js leaves a
# target it cannot read alone), its headings change and the chances are left out. Absent until then.
MET = fc.get("met")
fc_count = "paused" if (PAUSED or MET) else fc["target"]
last_rev = fc["revisions"][0]

# ---------------------------------------------------------------- lanes, and the order they give
# Lanes: three finer readings of a project that is in-game (issue 8 on the page's repository). A lane's step comes
# from a figure the project reports (speed: the average over the newest session of play of 10 minutes or more that
# it reports, entered as "low" = "high", or with no such session the middle of the frame rates it reports in play,
# "low" to "high", in rendered frames a second; stability: "minutes", its longest session without a crash) or, for the picture, from
# the written steps below. "bar" is the first step that meets the page's playable bar on that lane; the picture has
# none, because the bar asks nothing of it.
LANES = [
    {"key": "picture", "name": "Picture", "what": "What the project says is on screen in the game's world.",
     "steps": ["Mostly dark or unlit", "Lit where the sun falls, shadows black or dark",
               "Lit in light and shade, with visible faults", "Lit and whole, small faults only",
               "The console's picture, ray tracing included"]},
    {"key": "speed", "name": "Speed",
     "what": "The average it reports over a session of play of 10 minutes or more, or with no such session the "
             "middle of the frame rates it reports in play, in rendered frames a second (fps).",
     "edges": [0, 2, 5, 10, 20, 30], "bar": 5, "goal": 6,
     "steps": ["Under 2 fps", "2 fps or more", "5 fps or more", "10 fps or more", "20 fps or more",
               "30 fps or more, the console's rate"]},
    {"key": "stability", "name": "Stability", "what": "The longest session it reports without a crash.",
     "field": "minutes", "edges": [0, 10, 30, 60], "bar": 3, "goal": 4,
     "steps": ["Under 10 minutes", "10 minutes or more", "30 minutes or more", "An hour or more"]},
]
BY_KEY = {lane["key"]: lane for lane in LANES}
INGAME = stages.index("In-game") if "In-game" in stages else top - 1
# A project counted as playable (the top stage) keeps its lanes and is read against the next goal instead of the
# bar: the top step of the speed lane (30 frames a second or more) and of the stability lane (an hour or more).
PLAYABLE = top
LANE_STAGES = (INGAME, PLAYABLE)


def has_lanes(p):
    return p["stage"] in LANE_STAGES


def target_key(p):
    """The lane field that holds the step a row is measured against: the bar in-game, the next goal when playable."""
    return "goal" if p["stage"] == PLAYABLE else "bar"


def lane_value(lane, reading):
    """The figure a lane steps on: the middle of the entered range for speed (a session average is entered as
    one figure, low and high the same), the minutes for stability."""
    if lane["key"] == "speed":
        low, high = reading.get("low"), reading.get("high")
        return None if low is None or high is None else (low + high) / 2
    return reading.get(lane.get("field", ""))


def lane_step(lane, reading):
    """The step a reading reaches: counted from its figure where the lane has one, else the step it names."""
    if "edges" in lane:
        value = lane_value(lane, reading)
        return 0 if value is None else sum(1 for edge in lane["edges"] if value >= edge)
    return int(reading.get("step") or 0)


def lane_steps(p):
    read = p.get("lanes") or {}
    return {lane["key"]: min(lane_step(lane, read.get(lane["key"]) or {}), len(lane["steps"])) for lane in LANES}


def short_of_bar(p):
    """How many lane steps a project is short of what its row is measured against (the playable bar in-game, the
    next goal when playable), on the lanes that ask something of it."""
    steps = lane_steps(p)
    key = target_key(p)
    return sum(max(0, lane[key] - steps[lane["key"]]) for lane in LANES if lane.get(key))


def rank_key(p):
    """Order inside the in-game stage and inside the playable stage, from the lanes alone: fewest steps short of the
    bar (or of the next goal), then the better picture, the higher frame rate and the longer session. Nothing here
    is set by hand."""
    read = p.get("lanes") or {}
    speed = lane_value(BY_KEY["speed"], read.get("speed") or {}) or 0
    minutes = (read.get("stability") or {}).get("minutes") or 0
    return (short_of_bar(p), -lane_steps(p)["picture"], -speed, -minutes)


# Display order: by stage, as listed in data.json, except inside the in-game and playable stages, which follow rank_key.
projects = sorted(data["projects"], key=lambda p: (-p["stage"], rank_key(p) if has_lanes(p) else ()))


def positions(ordered):
    """Position labels in display order. Level projects share a number with an equals sign: in the in-game stage
    when their rank keys are equal, elsewhere when data.json gives them the same "N=" position."""
    labels, i = [], 0
    while i < len(ordered):
        p, j = ordered[i], i + 1
        if has_lanes(p):
            while j < len(ordered) and ordered[j]["stage"] == p["stage"] and rank_key(ordered[j]) == rank_key(p):
                j += 1
        elif isinstance(p.get("pos"), str) and p["pos"].endswith("="):
            while j < len(ordered) and ordered[j].get("pos") == p["pos"]:
                j += 1
        labels.extend([str(i + 1) if j == i + 1 else f"{i + 1}="] * (j - i))
        i = j
    return labels


place = dict(zip((p["name"] for p in projects), positions(projects)))
lead = projects[0]

# ---------------------------------------------------------------- hero: the stage ladder (the page's own data)
ladder = []
LAD_MAX = 5  # a rung names its first few projects and counts the rest: the standings below list them all
for n in range(top, 0, -1):
    here = [p for p in projects if p["stage"] == n]
    names = ", ".join(esc(p["name"]) for p in here[:LAD_MAX])
    if len(here) > LAD_MAX:
        names += f' <span class="lad__more">and&nbsp;{len(here) - LAD_MAX}&nbsp;more</span>'
    state = "lead" if n == lead["stage"] else ("has" if here else ("past" if n < lead["stage"] else "ahead"))
    ladder.append(
        f'<li class="lad__row lad__row--{state}" style="--i:{top - n}">'
        f'<span class="lad__n">{n}</span><span class="lad__stage">{esc(stages[n])}</span>'
        f'<span class="lad__who">{names}</span></li>'
    )

WORDS = ["No", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
         "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty",
         "Twenty-one", "Twenty-two", "Twenty-three", "Twenty-four", "Twenty-five", "Twenty-six", "Twenty-seven",
         "Twenty-eight", "Twenty-nine", "Thirty"]
public = [p for p in projects if not p.get("private")]
private = [p for p in projects if p.get("private")]
count = WORDS[len(public)] if len(public) < len(WORDS) else str(len(public))
# A private build has no repository to read: it is counted apart from the open-source projects.
extra = ""
if private:
    extra = f" and {WORDS[len(private)].lower()} private build{'' if len(private) == 1 else 's'}"

hero_fact = (
    f"Playable: {esc(data['playable']).lower()}. "
    f"{esc(lead.get('lead') or lead['name'])} is furthest, at stage&nbsp;{lead['stage']}&nbsp;of&nbsp;{top}."
)

# ---------------------------------------------------------------- standings


def meter(stage):
    cells = "".join(f'<span class="meter__seg{" is-on" if i <= stage else ""}"></span>' for i in range(1, top + 1))
    label = f"Stage {stage} of {top}: {stages[stage]}"
    return (
        f'<div class="meter" role="img" aria-label="{esc(label)}">{cells}</div>'
        f'<p class="label">{esc(label)}</p>'
    )


def lanes(p):
    """Three small meters for a project that carries lane readings, and how far they leave it from the bar."""
    read = p.get("lanes")
    if not read:
        return ""
    out = []
    for lane in LANES:
        reading = read.get(lane["key"]) or {}
        n = len(lane["steps"])
        step = min(lane_step(lane, reading), n)
        bar = lane.get(target_key(p))
        cells = "".join(
            f'<span class="meter__seg{" is-on" if i <= step else ""}{" is-bar" if bar and i >= bar else ""}"></span>'
            for i in range(1, n + 1)
        )
        head = f"{lane['name']} {step} of {n}:" if step else f"{lane['name']}:"
        out.append(
            f'<div class="lane"><div class="meter meter--lane" aria-hidden="true">{cells}</div>'
            f'<p class="label lane__label"><span class="lane__name">{esc(head)}</span> '
            f'{txt(reading.get("text") or "nothing reported")}</p></div>'
        )
    n = short_of_bar(p)
    if p["stage"] == PLAYABLE:
        short = f"{n} step{'' if n == 1 else 's'} short of the next goal" if n else "At the next goal on speed and stability"
    else:
        short = f"{n} step{'' if n == 1 else 's'} short of the playable bar" if n else "At the playable bar on speed and stability"
    return f'<div class="lanes">{"".join(out)}<p class="label lane__short">{esc(short)}</p></div>'


def lane_key():
    """The key to the lanes: what each reads and its steps, the ones that meet the playable bar marked."""
    cols = []
    for lane in LANES:
        bar = lane.get("bar")
        items = ""
        for i, s in enumerate(lane["steps"], 1):
            cls = ' class="is-bar"' if bar and i >= bar else ""
            items += f'<li{cls}><span class="steps__n">{i}</span><span>{txt(s)}</span></li>'
        cols.append(
            f'<div class="key__lane"><h3 class="t-card">{esc(lane["name"])}</h3>'
            f'<p class="small muted">{txt(lane["what"])}</p><ol class="steps">{items}</ol></div>'
        )
    return "".join(cols)


def after_colon(text):
    """A source line as it reads after "Source:": its first word in lower case, unless that word is a name."""
    first = text.split(" ", 1)[0]
    return text[0].lower() + text[1:] if first[1:].islower() else text


# What a project is reported to have been run on (issue 12): shown on its row and offered as a filter. "tested" in
# data.json holds {"os": [...], "gpu": [...]} from the project's own report; an empty list means nothing is reported.
OS_ORDER = ["Windows", "Linux", "Mac"]
GPU_ORDER = ["NVIDIA", "AMD", "Intel"]


def tested_of(p):
    t = p.get("tested") or {}
    return [x for x in OS_ORDER if x in (t.get("os") or [])], [x for x in GPU_ORDER if x in (t.get("gpu") or [])]


def tested_line(p):
    systems, cards = tested_of(p)
    parts = [", ".join(group) for group in (systems, cards) if group]
    return f'<p class="small muted">Tested on {esc(" · ".join(parts))}</p>' if parts else ""


def row_attrs(p):
    """What the filters read: the systems and cards a row reports and, for a row that is in-game, its lane steps."""
    systems, cards = tested_of(p)
    attrs = f' data-os="{esc(" ".join(x.lower() for x in systems))}" data-gpu="{esc(" ".join(x.lower() for x in cards))}"'
    if has_lanes(p):
        steps = lane_steps(p)
        attrs += "".join(f' data-{lane["key"]}="{steps[lane["key"]]}"' for lane in LANES)
    return attrs


def filter_panel():
    """Filters over the standings (issues 12 and 13): closed until asked for, one row of choices when open. A choice
    is offered only if some row can meet it."""
    systems = [x for x in OS_ORDER if any(x in tested_of(p)[0] for p in projects)]
    cards = [x for x in GPU_ORDER if any(x in tested_of(p)[1] for p in projects)]
    picks = [("os", "System", [(x.lower(), x) for x in systems]), ("gpu", "Card", [(x.lower(), x) for x in cards])]
    for lane in LANES:
        count = len(lane["steps"])
        if "edges" in lane:
            names = [lane["steps"][i - 1].split(",")[0] for i in range(2, count + 1)]
            choices = [(str(i), name[:1].lower() + name[1:]) for i, name in zip(range(2, count + 1), names)]
        else:
            choices = [(str(i), f"{i} of {count} or better" if i < count else f"{i} of {count}") for i in range(2, count + 1)]
        picks.append((lane["key"], lane["name"], choices))
    selects = "".join(
        f'<label class="pick"><span class="pick__name">{esc(name)}</span><select data-f="{key}"><option value="">any</option>'
        + "".join(f'<option value="{esc(value)}">{esc(label)}</option>' for value, label in choices)
        + "</select></label>"
        for key, name, choices in picks
    )
    return f"""
        <details class="more filter" id="filter" hidden>
          <summary><span class="link">Filter the table</span><span class="label muted" id="filter-count" aria-live="polite"></span></summary>
          <div class="filter__row">{selects}<button class="textbtn textbtn--chip" type="button" id="filter-clear" hidden>Clear</button></div>
          <p class="small muted filter__note">Systems and cards are the ones a project or its testers report running it on, and it may run on others. A choice on a lane leaves only projects that are in-game or counted as playable. Filters were suggested in issues <a class="link" href="{REPO}/issues/12" rel="noopener">12</a> and <a class="link" href="{REPO}/issues/13" rel="noopener">13</a> on this page&rsquo;s repository.</p>
        </details>"""


rows = []
for p in projects:
    rows.append(
        f"""
        <li class="board__row"{row_attrs(p)}>
          <p class="board__pos" aria-label="Position {esc(place[p['name']])}">{esc(place[p['name']])}</p>
          <div class="board__who">
            <h3 class="t-card">{name_link(p['repo'], p['name'], p.get('url'), not p.get('nolink'))}</h3>
            <p class="small muted">{esc(p['kind'])}</p>
            {tested_line(p)}
            {meter(p['stage'])}
            {lanes(p)}
          </div>
          <div class="board__where">
            <p class="measure">{txt(p['status'], p['changed'])}</p>
            <p class="small muted">Source: {esc(after_colon(p['basis']))}. Changed <time datetime="{esc(p['changed'])}" data-t="clock">{clock(p['changed'])} UTC</time>.</p>
          </div>
        </li>"""
    )

IDLE = "No GTA VI work published"
active = [w for w in data["watching"] if IDLE not in w["note"]]
idle = [w for w in data["watching"] if IDLE in w["note"]]
watching = "".join(
    f'<li><span class="rows__name">{name_link(w["repo"], w["name"], w.get("url"), not w.get("nolink"))}</span><p>{txt(w["note"])}</p></li>'
    for w in active
)
idle_line = ""
if idle:
    names = [name_link(w["repo"], w["name"], w.get("url")) for w in idle]
    joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    idle_line = f'<p class="small muted measure idle">Also checked, with no GTA VI work published: {joined}.</p>'

# ---------------------------------------------------------------- forecast
fc_odds = "".join(
    f'<li><span class="rows__name">{esc(o["by"][0].upper() + o["by"][1:])}</span><span class="rows__value">{esc(o["chance"])}</span></li>'
    for o in fc["odds"]
)
fc_steps = "".join(
    f'<li><span class="rows__name">{esc(s["name"])}</span><span class="rows__value">{esc(s["when"])}, {esc(s["date"])}</span></li>'
    for s in fc["steps"]
)
fc_basis = "".join(f"<li>{txt(b, last_rev['t'])}</li>" for b in fc["basis"][:6])
foot_name = "Playable bar" if MET else "Best estimate to playable"
fc_head = "Playable, by one project's own report" if MET else "Time to playable"
fc_lead = (
    f'<p class="lead">{txt(MET["line"], MET["t"])}</p>' if MET else
    f'<p class="lead">Around <time datetime="{esc(fc["target"])}">{esc(fc["date_label"])}</time>.</p>'
)
basis_head = "What the report says and what nobody has checked" if MET else "What the estimate rests on"
# fc["next_goal"]: what a playable row is read against next, in a sentence or two (absent: nothing is printed).
fc_next = f'\n          <p class="measure">{txt(fc["next_goal"])}</p>' if fc.get("next_goal") else ""
fc_odds_block = f'<h3 class="t-card">Chances</h3>\n          <ul class="rows">{fc_odds}</ul>' if fc["odds"] else ""
fc_small = (
    "This page's reading of one project's report, made by the AI that compiles the page. It can be wrong, and nobody outside the project has verified the report."
    if MET else
    "A forecast by the AI that compiles this page. It can be badly wrong, and it moves when the evidence does."
)

# ---------------------------------------------------------------- updates


def entry(u):
    pre = "about " if u.get("approx") else ""
    when = pre + clock(u["t"])
    points = "".join(f"<li>{txt(pt, u['t'])}</li>" for pt in u["points"])
    return f"""
        <li class="log__row">
          <p class="log__when"><time datetime="{esc(u['t'])}" data-t="log" data-pre="{esc(pre)}">{esc(when)}</time> <span>{esc(day(u['t']))}</span></p>
          <div class="log__what">
            <h3 class="t-card">{esc(u['title'])}</h3>
            <ul class="points measure">{points}</ul>
          </div>
        </li>"""


SHOWN = 4
recent = "".join(entry(u) for u in data["updates"][:SHOWN])
older_list = data["updates"][SHOWN:]
older = ""
if older_list:
    older = f"""
      <details class="more">
        <summary><span class="link">See {len(older_list)} earlier updates</span></summary>
        <ol class="log">{''.join(entry(u) for u in older_list)}
        </ol>
      </details>"""

# ---------------------------------------------------------------- method
notes = []
for n in data["notes"]:
    if isinstance(n, dict):
        # A note may end in one link: {"href": an https address, "link": its words}.
        more = ""
        if n.get("href") and n.get("link") and URL.match(n["href"]):
            more = f' <a class="link" href="{esc(n["href"])}" rel="noopener">{esc(n["link"])}</a>.'
        notes.append(f'<li><span class="rows__name">{esc(n["label"])}</span><p>{txt(n["text"])}{more}</p></li>')
    else:
        notes.append(f"<li><p>{txt(n)}</p></li>")
notes = "".join(notes)

CSS = (HERE / "page.css").read_text(encoding="utf-8")
JS = (HERE / "page.js").read_text(encoding="utf-8")

# ---------------------------------------------------------------- the page's own repository: a link to star it
REPO = "https://github.com/vuyp/gta6-pc-race"
STAR = (
    '<svg class="btn__icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 3.6l2.6 5.27 5.82.85-4.21 4.1.99 5.8L12 16.88l-5.2 2.74.99-5.8-4.21-4.1 5.82-.85z"/></svg>'
)
# publish.sh writes the star count to stars.txt before each build; without it the buttons carry no number.
stars = None
try:
    raw = (HERE / "stars.txt").read_text(encoding="utf-8").strip()
    if raw.isdigit() and int(raw) > 0:
        stars = int(raw)
except OSError:
    pass
star_count = f'<span class="btn__count">{stars:,}</span>' if stars else ""
star_said = f" ({stars:,} so far)" if stars else ""
star_nav = (
    f'<a class="btn btn--secondary nav__star" href="{REPO}" rel="noopener" '
    f'aria-label="Star this tracker on GitHub{star_said}">{STAR}<span class="btn__word">Star</span>{star_count}</a>'
)
star_foot = (
    f'<a class="btn btn--secondary" href="{REPO}" rel="noopener" '
    f'aria-label="Star this tracker on GitHub{star_said}">{STAR}<span>Star on GitHub</span>{star_count}</a>'
)
# Shown by page.js only where the reader's clock differs from UTC.
TZ_BTN = '<button class="textbtn" type="button" data-tz aria-pressed="false" hidden>Show local time</button>'
# The look follows the device unless the reader picks one here (issues 11 and 15). The button is shown by page.js,
# and THEME_EARLY applies a saved choice before the first paint so a dark page never flashes light.
THEME_BTN = '<button class="textbtn textbtn--chip" type="button" data-theme-btn hidden>Theme: auto</button>'
THEME_EARLY = '<script>try{var t=localStorage.getItem("gta6race.theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}</script>'

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='5' fill='%2326251e'/%3E"
    "%3Ctext x='16' y='22.5' text-anchor='middle' font-family='Helvetica,Arial,sans-serif' font-size='19' "
    "font-weight='600' fill='%23dfdedb'%3EG%3C/text%3E%3C/svg%3E"
)

hero_reads = (
    f"This page read their public repositories every {esc(data['cadence_minutes'])} minutes and says how far each had got when its automatic checks were paused."
    if PAUSED else
    f"This page reads their public repositories every {esc(data['cadence_minutes'])} minutes and says how far each has got."
)
checked_word = "Last checked" if PAUSED else "Checked"
close_head = "Automatic checks are paused" if PAUSED else f"Standings checked every {esc(data['cadence_minutes'])} minutes"
TITLE = "GTA VI PC Race: live tracker of unofficial PC ports"
DESC = (
    "How far each open-source project has got in running the Xbox build of GTA VI on a PC, "
    + ("as of the last check before automatic checks were paused, " if PAUSED else f"checked every {esc(data['cadence_minutes'])} minutes, ")
    + ("and the first report of a playable session, by the project's own account." if MET else "with a best estimate of when it becomes playable.")
)
SITE = "https://vuyp.github.io/gta6-pc-race/"

page = f"""<!DOCTYPE html>
<html lang="en" data-type="software" data-radius="sharp" data-buttons="tonal">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(TITLE)}</title>
<meta name="description" content="{esc(DESC)}">
<meta name="page-type" content="software">
<meta name="site-kind" content="software">
<meta name="color-scheme" content="light dark">
{THEME_EARLY}
<meta name="theme-color" content="#dfdedb" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1c1b16" media="(prefers-color-scheme: dark)">
<meta property="og:title" content="{esc(TITLE)}">
<meta property="og:description" content="{esc(DESC)}">
<meta property="og:type" content="website">
<meta property="og:image" content="{SITE}share.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{FAVICON}">
<link rel="preload" href="fonts/onest-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>
{CSS}
</style>
</head>
<body>
<!-- deal: palette stone-blueprint · type onest · radius sharp · buttons tonal · mark initial · nav-centre · footer-statement · close-word · rhythm dark-band (forecast) -->
<header class="nav nav--centre">
  <div class="wrap nav__bar">
    <a class="skip-link" href="#top">Skip to content</a>
    <a class="nav__logo" href="#top" aria-label="GTA VI PC Race, top of page"><span class="mark mark--initial" aria-hidden="true">G</span><span>GTA VI PC Race</span></a>
    <nav class="nav__links" id="menu" aria-label="Sections">
      <a href="#standings">Standings</a>
      <a href="#forecast">Forecast</a>
      <a href="#updates">Updates</a>
      <a href="#method">Method</a>
    </nav>
    <div class="nav__actions">
      {star_nav}
      <a class="btn btn--primary" href="#standings">See the standings</a>
      <button class="btn btn--secondary nav__toggle" type="button" aria-expanded="false" aria-controls="menu" aria-label="Menu"><span aria-hidden="true"></span></button>
    </div>
  </div>
</header>

<main id="top">
  <section class="hero" data-enter>
    <div class="wrap grid">
      <div class="hero__words">
        <h1 class="enter">GTA VI PC port tracker</h1>
        <p class="lead hero__fact enter">{hero_fact}</p>
        <p class="hero__how enter">{count} open-source projects{extra} are trying to run the game&rsquo;s Xbox build on a PC. {hero_reads} <span class="muted">{checked_word} <time id="checked" datetime="{esc(data['checked'])}" data-t="clock-day">{clock(data['checked'])} UTC on {esc(day(data['checked']))}</time><span id="ago"></span>. {TZ_BTN}</span></p>
        <div class="btn-row enter">
          <a class="btn btn--primary" href="#standings">See the standings</a>
          <a class="btn btn--secondary" href="#updates">Read the latest update</a>
        </div>
      </div>
      <div class="hero__visual enter">
        <div class="frame" role="group" aria-label="The seven stages and which projects have reached each">
          <p class="frame__head"><span>Stages reached</span><time class="mono" datetime="{esc(data['checked'])}" data-t="clock">{clock(data['checked'])} UTC</time></p>
          <ol class="lad" reversed>{''.join(ladder)}</ol>
          <p class="frame__foot"><span>{foot_name}</span><span id="fc-short" data-target="{esc(fc_count)}">{esc(fc['label'])}</span></p>
        </div>
      </div>
    </div>
  </section>

  <section id="standings">
    <div class="wrap">
      <div class="head">
        <h2>Standings</h2>
        <details class="more">
          <summary><span class="link">How the lanes and the order are read</span></summary>
          <p class="measure">A project that is in-game, at stage&nbsp;{INGAME}, is also read on three lanes. Each step is this page&rsquo;s reading of what the project reports about itself, or of the source its row names, and an empty meter means no figure is reported. Blue marks the steps that meet the playable bar: 20&nbsp;frames a second and 30&nbsp;minutes without a crash. A project counted as playable, at stage&nbsp;{PLAYABLE}, keeps its lanes and is read against the next goal instead, which blue then marks: 30&nbsp;frames a second or more and an hour or more without a crash.</p>
          <p class="measure">Rows at those stages are ordered by their lanes and nothing else, each stage on its own: fewest steps short of the bar, or of the next goal, on speed and stability together, then the better picture, the higher frame rate and the longer session. The lanes were suggested in <a class="link" href="{REPO}/issues/8" rel="noopener">issue&nbsp;8</a> on this page&rsquo;s repository.</p>
          <div class="key">{lane_key()}</div>
        </details>{filter_panel()}
      </div>
      <ol class="board">{''.join(rows)}
      </ol>
      <p class="small muted" id="filter-none" hidden>No project matches these choices.</p>
      <h3 class="sub">Also watched</h3>
      <ul class="pairs">{watching}</ul>
      {idle_line}
    </div>
  </section>

  <section id="forecast" class="ground-inverse">
    <div class="wrap">
      <h2>{esc(fc_head)}</h2>
      <div class="grid fc">
        <div class="fc__main">
          <p class="stat" id="fc-rel" data-target="{esc(fc_count)}">{esc(fc['label'])}</p>
          {fc_lead}
          <p class="measure">{txt(fc['definition'])}</p>{fc_next}
          <h3 class="t-card">{basis_head}</h3>
          <ul class="points measure">{fc_basis}</ul>
        </div>
        <div class="fc__side">
          {fc_odds_block}
          <h3 class="t-card">Milestones</h3>
          <ul class="rows">{fc_steps}</ul>
          <p class="small muted">{esc(fc_small)} Last revised <time datetime="{esc(last_rev['t'])}" data-t="clock-day">{clock(last_rev['t'])} UTC on {esc(day(last_rev['t']))}</time>: {txt(last_rev['note'], last_rev['t'])}</p>
        </div>
      </div>
    </div>
  </section>

  <section id="updates">
    <div class="wrap">
      <h2>Updates</h2>
      <ol class="log">{recent}
      </ol>{older}
    </div>
  </section>

  <section id="method">
    <div class="wrap">
      <h2>Method and limits</h2>
      <ul class="rows rows--spec">{notes}</ul>
    </div>
  </section>
</main>

<footer class="footer closing footer--statement">
  <div class="wrap slab">
    <div class="close close--word">
      <div class="close__head">
        <h2>{close_head}</h2>
        <div class="btn-row">
          <a class="btn btn--primary" href="#standings">See the standings</a>
          {star_foot}
        </div>
      </div>
      <p class="close__name" aria-hidden="true">GTA VI PC Race</p>
    </div>
    <p class="legal small muted">GTA VI PC Race, 2026. Not affiliated with Rockstar Games or Take-Two Interactive. <span id="tz-note">Times are UTC.</span> {TZ_BTN} {THEME_BTN}</p>
  </div>
</footer>
<script>
{JS}
</script>
</body>
</html>
"""

OUT.write_text(page, encoding="utf-8")
# The in-game order as computed, for whoever edits data.json next (not published).
(HERE / "order.txt").write_text(
    "".join(
        f"{place[p['name']]} {p['name']} | {short_of_bar(p)} short of the {'next goal' if p['stage'] == PLAYABLE else 'bar'} | speed "
        f"{lane_value(BY_KEY['speed'], (p.get('lanes') or {}).get('speed') or {})} step {lane_steps(p)['speed']} | "
        f"stability {((p.get('lanes') or {}).get('stability') or {}).get('minutes')} step {lane_steps(p)['stability']} | "
        f"picture {lane_steps(p)['picture']}\n"
        for p in projects if has_lanes(p)
    ),
    encoding="utf-8",
)
print(f"wrote {OUT} ({len(page.encode('utf-8'))} bytes), checked {data['checked']}")
