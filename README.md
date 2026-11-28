# GTA VI PC Race

An unofficial status page that tracked the open-source projects trying to run GTA VI on a PC.

**This tracker is no longer updated.** Its last check was at 00:17 UTC on 28 November 2026. Nothing on the page or in this repository is read or changed after that, so it will fall out of date.

The page, as last published: https://vuyp.github.io/gta6-pc-race/

- Status only. At the last check one project counted as playable by its own report, which nobody else had checked. This repository holds no game files, no downloads and no instructions.
- Every stage shown is the project's own claim, read from its public repository at the last check.
- Compiled automatically by an AI assistant (Claude), which checked about every 30 minutes until the last check. It can be wrong, and it is now out of date.
- Not affiliated with Rockstar Games, Take-Two Interactive, Microsoft or any project listed.

## Stages and lanes

Each project is placed on a ladder of seven stages, from loading the game's files to playable. A project that is in-game (stage 6) or counted as playable (stage 7) is also read on three lanes:

- **Picture**: what the project says is on screen in the game's world, in five written steps.
- **Speed**: the average it reports over its newest session of play of 10 minutes or more (its median where it gives no average), or with no such session the middle of the frame rates it reports in play, in rendered frames a second. Scripted or automated runs and scenes standing still do not count as play.
- **Stability**: the longest session it reports without a crash.

Each step is the page's reading of what the project reports about itself. The key under the page's "Standings" title lists the steps, and the ones that meet its playable bar (20 frames a second and 30 minutes without a crash) are marked in blue. A project counted as playable is read against a next goal instead: one session of play of an hour or more at 30 frames a second or better, rendered frames only, with the steps that meet it marked in blue on its row. The page publishes no estimate for the next goal.

Rows at stage 6 and at stage 7 are each ordered by their lanes alone: fewest steps short of the bar (stage 6) or of the next goal (stage 7) on speed and stability together, then the better picture, the higher frame rate and the longer session. Nothing in that order is set by hand, and a place is not a verification or an endorsement: it is computed from what each project reports about itself. Lower stages have no lanes and are ordered by the page's reading of what remains before the next stage.

## Requests and corrections

This tracker is no longer updated, so a request to add, correct or take off a project will not be acted on.

The page does not link to the leaked build, to downloads, streams or chats, or to instructions and tools for running anything.

## The page's source

`index.html` is generated. Its source is in [`src/`](src), as it stood at the last check: `data.json` holds everything the page says, `build.py` renders it (the order of the rows with lanes is computed there, in `rank_key`), and `page.css` and `page.js` are its styles and script.

## Credits

- Typefaces: Onest and JetBrains Mono, served from `fonts/` under the SIL Open Font License 1.1 (licence texts beside the files).
- Design: laid out by hand to the written rules of the tasteskill "design-taste-frontend" skill (palette "stone-blueprint", type pairing "onest", both drawn at random from its libraries). None of the skill's own files are used.
- Local-time display: asked for in issue 5 and first written by opsasa in pull request 7.
- Lanes for projects that are in-game (picture, speed, stability): suggested by I-I-IT in issue 8.
- The next goal for playable rows: suggested by I-I-IT in issue 24 and KayleighOwO in issue 42.
- Filters over the standings (system, card maker and a minimum on each lane) and the "tested on" line on each row: suggested by I-I-IT in issues 12 and 13.
- Dark and high-contrast looks, and the theme switch in the footer (auto, light, dark): asked for in issues 11 and 15.
