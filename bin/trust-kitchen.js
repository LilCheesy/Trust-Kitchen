#!/usr/bin/env node
/*
 * Trust Kitchen installer (Node, zero dependencies): `npx github:LilCheesy/Trust-Kitchen install`.
 *
 * WHAT:       Same behaviour as installer/install.py, driven by the same installer/targets.json: copies skills to each
 *             chosen agent's skills folder, personas for agents with subagents, scripts to .trust-kitchen/scripts, the
 *             eval runner and example cases to .trust-kitchen/evals, a default policy (only if missing), `/tk` command
 *             files, a marked block in AGENTS.md and agent rule files; records every written file (with its sha256)
 *             and every folder it created in .trust-kitchen/install.json. Commands: install, update, uninstall,
 *             status, list.
 * WHY:        One command that works for any agent, without publishing to a registry.
 * RUNS WHEN:  `npx github:LilCheesy/Trust-Kitchen install [--agents a,b | 1,2] [--dir PATH] [--yes] [--no-color]`
 * AFFECTS:    Writes inside the target project only. Never overwrites a file it did not write or one the user changed
 *             (skipped); never deletes a changed file (kept) or a folder the user already had; keeps line endings.
 * CAUTION:    Keep in step with installer/install.py — tests/test_installer.py compares the two byte for byte.
 *             Exit codes: 0 ok · 1 nothing installed (update) · 2 bad input.
 * CHANGED:    2026-11-20 · v0.2 · new
 *             2026-11-20 · v0.3: `/tk` command files (putCommands), skipped files reported
 *             2026-11-21 · eval runner installed; user files never overwritten; edited files kept on uninstall
 *                          (sha256 in the manifest); exit 2 on bad input. Mirrors installer/install.py.
 *             2026-11-21 · second review: example cases installed; update keeps user edits; CRLF kept; only
 *                          created folders removed; agent numbers accepted (like Python)
 *             2026-11-21 · Linux container test: uninstall also removes the bytecode the installed scripts produced
 */
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

const SRC = path.resolve(__dirname, '..');
const TARGETS = JSON.parse(fs.readFileSync(path.join(SRC, 'installer', 'targets.json'), 'utf8'));
const START = '<!-- trust-kitchen:start -->';
const END = '<!-- trust-kitchen:end -->';

const args = process.argv.slice(2);
const flag = (name) => args.includes(`--${name}`);
const opt = (name) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : undefined; };
const useColor = !flag('no-color') && process.stdout.isTTY && !process.env.NO_COLOR;
const c = (code, s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : s);
const teal = (s) => c('38;2;20;196;150', s);
const dim = (s) => c('2', s);
const bold = (s) => c('1', s);

function banner() {
  const mark = [
    '  ██████  ██████  ██   ██',
    '    ██    ██  ██  ██  ██ ',
    '    ██    ██████  █████  ',
    '    ██    ██  ██  ██  ██ ',
    '    ██    ██  ██  ██   ██',
  ];
  console.log('');
  console.log(teal(mark.join('\n')));
  console.log(`  ${bold('Trust Kitchen')} ${dim('v' + TARGETS.version)}  ${dim('·')}  Ship fast. Prove it.`);
  console.log('');
}

const rel = (p, root) => path.relative(root, p).split(path.sep).join('/');
const sha = (p) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const isFile = (p) => fs.existsSync(p) && fs.statSync(p).isFile();
const isDir = (p) => fs.existsSync(p) && fs.statSync(p).isDirectory();
const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

/*
 * WHAT:       What one install run has written, skipped and created, plus the previous manifest it must respect.
 * CAUTION:    Mirrors class _Run in installer/install.py; the byte-for-byte test compares both.
 */
function newRun(project, prev) {
  const run = { project, prev, files: [], skipped: [], createdDirs: [] };
  run.r = (p) => rel(p, project);
  // may Trust Kitchen write `r`? only if new, or written by Trust Kitchen and unchanged since (sha256 matches)
  run.mine = (r, out) => {
    if (!fs.existsSync(out) || run.files.includes(r)) return true;
    if (!(prev.files || []).includes(r)) return false;
    const recorded = (prev.hashes || {})[r];
    return !recorded || sha(out) === recorded;
  };
  run.ensureDir = (d) => {
    const missing = [];
    while (d !== project && !fs.existsSync(d)) { missing.push(d); d = path.dirname(d); }
    for (const m of missing.reverse()) { fs.mkdirSync(m); run.createdDirs.push(run.r(m)); }
  };
  run.copyFile = (src, out) => {
    const r = run.r(out);
    if (!run.mine(r, out)) { run.skipped.push(r); return; }
    run.ensureDir(path.dirname(out));
    fs.copyFileSync(src, out);
    if (!run.files.includes(r)) run.files.push(r);
  };
  run.copyTree = (src, dst, skip = []) => {
    if (!fs.existsSync(src)) return;
    const all = [];
    const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
      const p = path.join(dir, e.name);
      if (e.name === '__pycache__') return;
      if (e.isDirectory()) return walk(p);
      all.push(p);
    });
    walk(src);
    all.filter((p) => !skip.includes(rel(p, src).split('/')[0]))
      .sort((a, b) => cmp(rel(a, src), rel(b, src)))
      .forEach((p) => run.copyFile(p, path.join(dst, path.relative(src, p))));
  };
  run.writeText = (out, text) => {
    const r = run.r(out);
    if (!run.mine(r, out)) { run.skipped.push(r); return; }
    run.ensureDir(path.dirname(out));
    fs.writeFileSync(out, text, 'utf8');
    if (!run.files.includes(r)) run.files.push(r);
  };
  return run;
}

function putBlock(run, file, body, front) {
  const created = !fs.existsSync(file);
  const old = created ? '' : fs.readFileSync(file, 'utf8');
  const block = `${START}\n${body.trim()}\n${END}\n`;
  let next;
  if (old.includes(START) && old.includes(END)) {
    next = old.slice(0, old.indexOf(START)) + block + old.slice(old.indexOf(END) + END.length).replace(/^[\r\n]+/, '');
  } else {
    const eol = old.includes('\r\n') ? '\r\n' : '\n';  // separate with the file's own line ending
    next = (created ? (front || '') : '') + (old.trim() ? old.replace(/\s+$/, '') + eol + eol : '') + block;
  }
  run.ensureDir(path.dirname(file));
  fs.writeFileSync(file, next, 'utf8');
  return created;
}

function loadManifest(mpath) {
  let m;
  try { m = JSON.parse(fs.readFileSync(mpath, 'utf8')); } catch (e) {
    throw new Error(`${mpath} is not valid JSON (${e.message}); fix or delete it`);
  }
  if (!m || typeof m !== 'object' || Array.isArray(m)) throw new Error(`${mpath} is not a Trust Kitchen manifest`);
  return m;
}

function install(project, agents) {
  const unknown = agents.filter((a) => !TARGETS.agents[a]);
  if (!agents.length || unknown.length) {
    throw new Error(`unknown or no agent(s): ${unknown.join(', ') || '(none)'}; choose from ${Object.keys(TARGETS.agents).join(', ')}`);
  }
  fs.mkdirSync(project, { recursive: true });
  const always = TARGETS.always;
  const mpath = path.join(project, always.manifest);
  const prev = fs.existsSync(mpath) ? loadManifest(mpath) : {};
  const run = newRun(project, prev);
  const blocks = []; const createdBlocks = []; const skillsDirs = [];
  for (const a of agents) {
    const spec = TARGETS.agents[a];
    if (spec.skills_dir && !skillsDirs.includes(spec.skills_dir)) {
      skillsDirs.push(spec.skills_dir);
      run.copyTree(path.join(SRC, 'skills'), path.join(project, spec.skills_dir));
    }
    if (spec.agents_dir) run.copyTree(path.join(SRC, 'agents'), path.join(project, spec.agents_dir));
  }
  if (agents.some((a) => !TARGETS.agents[a].skills_dir)) {
    skillsDirs.push(always.fallback_skills_dir);
    run.copyTree(path.join(SRC, 'skills'), path.join(project, always.fallback_skills_dir));
  }
  run.copyTree(path.join(SRC, 'scripts'), path.join(project, always.scripts_dir));
  run.copyTree(path.join(SRC, always.evals.from), path.join(project, always.evals.to), always.evals.skip || []);
  const policy = path.join(project, always.policy);
  if (!fs.existsSync(policy)) run.copyFile(path.join(SRC, 'schema', 'policy.example.json'), policy);
  const body = fs.readFileSync(path.join(SRC, 'installer', 'block.md'), 'utf8')
    .replace('{skills_dirs}', skillsDirs.map((d) => `\`${d}/\``).join(', '));
  const targets = [[always.agents_md, '']];
  for (const a of agents) for (const r of TARGETS.agents[a].rules || []) targets.push([r.path, r.front || '']);
  for (const [p, front] of targets) {
    if (blocks.includes(p)) continue;
    if (putBlock(run, path.join(project, p), body, front)) createdBlocks.push(p);
    blocks.push(p);
  }
  putCommands(run, agents);
  const order = Object.keys(TARGETS.agents);
  const uniq = (xs) => [...new Set(xs)].sort(cmp);
  const hashes = { ...(prev.hashes || {}) };
  for (const r of run.files) hashes[r] = sha(path.join(project, r));
  run.ensureDir(path.dirname(mpath));
  const manifest = {
    version: TARGETS.version,
    agents: [...new Set([...(prev.agents || []), ...agents])].sort((x, y) => order.indexOf(x) - order.indexOf(y)),
    files: uniq([...(prev.files || []), ...run.files]),
    hashes: Object.fromEntries(Object.keys(hashes).sort(cmp).map((k) => [k, hashes[k]])),
    blocks: uniq([...(prev.blocks || []), ...blocks]),
    created_blocks: uniq([...(prev.created_blocks || []), ...createdBlocks]),
    created_dirs: uniq([...(prev.created_dirs || []), ...run.createdDirs]),
  };
  fs.writeFileSync(mpath, JSON.stringify(manifest, null, 2) + '\n', 'utf8');
  return { written: new Set(run.files).size, agents: manifest.agents, skillsDirs, skipped: uniq(run.skipped) };
}

/*
 * WHAT:       Write each chosen agent's `/tk` command file (targets.json "commands"), with {skills_dir} filled in.
 * WHY:        v0.3 — one "/tk" command in every agent; Gemini CLI and OpenCode need a one-file command.
 * RUNS WHEN:  install() / update, after the skills are copied.
 * AFFECTS:    Adds the paths to run.files (uninstall removes them); a user's own file is skipped.
 * CAUTION:    Mirrors _put_commands in installer/install.py.
 * CHANGED:    2026-11-20 · v0.3 · new
 */
function putCommands(run, agents) {
  for (const a of agents) {
    const spec = TARGETS.agents[a];
    const sd = spec.skills_dir || TARGETS.always.fallback_skills_dir;
    for (const cmd of spec.commands || []) run.writeText(path.join(run.project, cmd.path), cmd.text.split('{skills_dir}').join(sd));
  }
}

function uninstall(project) {
  const mpath = path.join(project, '.trust-kitchen', 'install.json');
  if (!fs.existsSync(mpath)) return { removed: 0, kept: [], note: 'nothing installed' };
  const m = loadManifest(mpath);
  const hashes = m.hashes || {};
  let removed = 0; const kept = [];
  for (const r of m.files || []) {
    const p = path.join(project, r);
    if (!isFile(p)) continue;
    if (hashes[r] && sha(p) !== hashes[r]) { kept.push(r); continue; }  // changed by the user after install
    fs.unlinkSync(p); removed++;
    if (p.endsWith('.py')) {  // bytecode Python wrote when the script ran (found in a clean Linux container)
      const cache = path.join(path.dirname(p), '__pycache__');
      const stem = path.basename(p, '.py');
      if (isDir(cache)) {
        for (const f of fs.readdirSync(cache)) if (f.startsWith(`${stem}.`) && f.endsWith('.pyc')) fs.unlinkSync(path.join(cache, f));
        if (fs.readdirSync(cache).length === 0) fs.rmdirSync(cache);
      }
    }
  }
  for (const r of m.blocks || []) {
    const p = path.join(project, r);
    if (!isFile(p)) continue;
    let t = fs.readFileSync(p, 'utf8');
    if (t.includes(START) && t.includes(END)) {
      const eol = t.slice(0, t.indexOf(START)).includes('\r\n') ? '\r\n' : '\n';
      t = t.slice(0, t.indexOf(START)).replace(/\s+$/, '') + eol + t.slice(t.indexOf(END) + END.length).replace(/^[\r\n]+/, '');
      fs.writeFileSync(p, t.trim() ? t : '', 'utf8');
    }
    const rest = fs.readFileSync(p, 'utf8').replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');
    if ((m.created_blocks || []).includes(r) && !rest.trim()) fs.unlinkSync(p);
  }
  fs.unlinkSync(mpath);
  const dirs = 'created_dirs' in m
    ? m.created_dirs.map((d) => path.join(project, d))
    : [...new Set([...(m.files || []), ...(m.blocks || [])].map((r) => path.dirname(path.join(project, r))))]
      .concat([path.dirname(mpath)]);
  dirs.sort((a, b) => b.split(path.sep).length - a.split(path.sep).length);
  for (const d of dirs) if (d !== project && isDir(d) && fs.readdirSync(d).length === 0) fs.rmdirSync(d);
  return { removed, kept };
}

function status(project) {
  const mpath = path.join(project, '.trust-kitchen', 'install.json');
  if (!fs.existsSync(mpath)) return { installed: false };
  const m = loadManifest(mpath);
  const files = m.files || [];
  const skills = new Set(files.filter((f) => f.endsWith('/SKILL.md')).map((f) => f.split('/').slice(-2)[0]));
  return { installed: true, version: m.version, agents: m.agents || [], skills: skills.size, files: files.length };
}

// "1,3" or "claude-code, codex" → agent ids, exactly like _parse_agents in installer/install.py
function parseAgents(raw) {
  const names = Object.keys(TARGETS.agents);
  return raw.split(',').map((s) => s.trim()).filter(Boolean).map((s) => {
    if (!/^\d+$/.test(s)) return s;
    const i = Number(s);
    if (i < 1 || i > names.length) throw new Error(`no agent number ${i}; choose 1-${names.length}`);
    return names[i - 1];
  });
}

async function askAgents() {
  const names = Object.keys(TARGETS.agents);
  if (!process.stdin.isTTY) throw new Error('no terminal to ask in: use --agents claude-code,codex (see: list)');
  console.log(bold('  Which coding agents do you use in this project?'));
  names.forEach((n, i) => console.log(`   ${teal(String(i + 1).padStart(2))}  ${TARGETS.agents[n].label.padEnd(20)} ${dim(n)}`));
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const answer = await new Promise((res) => rl.question(`  ${teal('>')} numbers or names, comma-separated [1]: `, res));
  rl.close();
  return parseAgents(answer.trim() || '1');
}

async function main() {
  const cmd = args[0];
  const project = path.resolve(opt('dir') || process.cwd());
  if (!['install', 'update', 'uninstall', 'status', 'list'].includes(cmd)) {
    banner();
    console.log('  Usage: npx github:LilCheesy/Trust-Kitchen <install|update|uninstall|status|list> [--agents a,b] [--dir PATH] [--yes]');
    return cmd ? 2 : 0;
  }
  if (cmd === 'list') {
    Object.entries(TARGETS.agents).forEach(([n, s], i) => console.log(`${String(i + 1).padStart(2)}. ${n.padEnd(12)} ${s.label}`));
    return 0;
  }
  if (cmd === 'status') { console.log(JSON.stringify(status(project), null, 2)); return 0; }
  if (cmd === 'uninstall') { console.log(JSON.stringify(uninstall(project), null, 2)); return 0; }
  if (!flag('yes')) banner();
  let agents;
  if (opt('agents')) agents = parseAgents(opt('agents'));
  else if (cmd === 'update') {
    const st = status(project);
    if (!st.installed) { console.error('  Nothing installed here. Run: install'); return 1; }
    agents = st.agents;
  } else if (flag('yes')) throw new Error('no agents given: use --agents claude-code,codex (see: list)');
  else agents = await askAgents();
  const r = install(project, agents);
  console.log(`  ${teal('done')}  Trust Kitchen ${TARGETS.version} for ${bold(r.agents.join(', '))}`);
  console.log(`        ${r.written} files  ${dim('·')}  skills in ${r.skillsDirs.join(', ')}`);
  for (const s of r.skipped) console.log(`  ${dim('skip')}  ${s}: yours (or changed by you), not overwritten`);
  console.log(`  ${teal('next')}  open your agent here and type ${bold('/tk')}  ${dim('(first time: /tk setup)')}`);
  return 0;
}

main().then((code) => process.exit(code)).catch((e) => { console.error(`  error: ${e.message}`); process.exit(2); });
