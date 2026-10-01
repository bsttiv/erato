/* @ds-bundle: {"format":4,"namespace":"Erato","components":[{"name":"Button"},{"name":"Tag"},{"name":"Segmented"},{"name":"SideNav"},{"name":"ChordEditor"},{"name":"TabEditor"},{"name":"LyricsViewer"},{"name":"DemoPlayer"},{"name":"TodoList"}]} */
(function () {
  "use strict";
  /* React se resuelve al renderizar, no al cargar: el bundle puede cargarse antes que React. */
  function h() { return window.React.createElement.apply(null, arguments); }
  function useState(v) { return window.React.useState(v); }
  function useRef(v) { return window.React.useRef(v); }
  function useEffect(f, d) { return window.React.useEffect(f, d); }
  function useMemo(f, d) { return window.React.useMemo(f, d); }
  function cx() { return Array.prototype.filter.call(arguments, Boolean).join(" "); }

  /* ── Íconos: trazo 1.5, 16px, currentColor ───────────────────────── */
  var PATHS = {
    play: "M5 3.5v9l7.5-4.5z",
    pause: "M5 3.5v9M11 3.5v9",
    plus: "M8 3v10M3 8h10",
    x: "M4 4l8 8M12 4l-8 8",
    check: "M3.5 8.5l3 3 6-7",
    max: "M3 6V3h3M13 6V3h-3M3 10v3h3M13 10v3h-3",
    min: "M6 3v3H3M10 3v3h3M6 13v-3H3M10 13v-3h3",
    left: "M10 3.5L5.5 8 10 12.5",
    right: "M6 3.5L10.5 8 6 12.5",
    bar: "M8 3v10",
    guitar: "M10.5 2.5l3 3M12 4L7.5 8.5M7 7.5c-1.5-1-3.5-.5-4 1s-.5 3 1 4.5 3.5 1.5 4.5 1 2-2.5 1-4",
    piano: "M2.5 3.5h11v9h-11zM6 3.5v5M10 3.5v5M8 8.5v4"
  };
  function Icon(p) {
    var fill = p.name === "play";
    return h("svg", { className: cx("er-ico", p.className), viewBox: "0 0 16 16", "aria-hidden": "true",
      fill: fill ? "currentColor" : "none", stroke: "currentColor", strokeWidth: p.name === "pause" ? 2.25 : 1.5,
      strokeLinecap: "round", strokeLinejoin: "round" }, h("path", { d: PATHS[p.name] }));
  }

  /* ── Teoría: nombres de notas y detección de acordes ─────────────── */
  var NOTE = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"];
  var QUAL = [
    ["", [0, 4, 7]], ["m", [0, 3, 7]], ["7", [0, 4, 7, 10]], ["maj7", [0, 4, 7, 11]], ["m7", [0, 3, 7, 10]],
    ["sus4", [0, 5, 7]], ["sus2", [0, 2, 7]], ["dim", [0, 3, 6]], ["aug", [0, 4, 8]], ["5", [0, 7]],
    ["6", [0, 4, 7, 9]], ["m6", [0, 3, 7, 9]], ["m7b5", [0, 3, 6, 10]], ["dim7", [0, 3, 6, 9]], ["mMaj7", [0, 3, 7, 11]],
    ["7sus4", [0, 5, 7, 10]], ["add9", [0, 2, 4, 7]], ["madd9", [0, 2, 3, 7]], ["9", [0, 2, 4, 7, 10]],
    ["maj9", [0, 2, 4, 7, 11]], ["m9", [0, 2, 3, 7, 10]], ["6/9", [0, 2, 4, 7, 9]], ["7b9", [0, 1, 4, 7, 10]],
    ["7#9", [0, 3, 4, 7, 10]], ["13", [0, 2, 4, 7, 9, 10]], ["maj7#11", [0, 4, 6, 7, 11]], ["aug7", [0, 4, 8, 10]]
  ];
  function key(arr) { return arr.slice().sort(function (a, b) { return a - b; }).join(","); }
  /** detectChord(notes) — notes: MIDI numbers (the lowest is the bass) or pitch classes 0–11.
   *  Returns {name, root, quality, bass, notes} or null. Handles slash chords and 7th/9th chords without a 5th. */
  function detectChord(notes) {
    if (!notes || !notes.length) return null;
    var bass = Math.min.apply(null, notes) % 12;
    var pcs = []; notes.forEach(function (n) { var p = ((n % 12) + 12) % 12; if (pcs.indexOf(p) < 0) pcs.push(p); });
    if (pcs.length === 1) return { name: NOTE[pcs[0]], root: pcs[0], quality: "nota", bass: bass, notes: [NOTE[pcs[0]]] };
    var best = null;
    pcs.forEach(function (r) {
      var iv = key(pcs.map(function (p) { return (p - r + 12) % 12; }));
      QUAL.forEach(function (q, qi) {
        var full = key(q[1]), no5 = q[1].length >= 4 ? key(q[1].filter(function (x) { return x !== 7; })) : null;
        var s = iv === full ? 0 : (iv === no5 ? 1 : -1);
        if (s < 0) return;
        var score = s * 3 + (r === bass ? 0 : 2) + qi * 0.01;
        if (!best || score < best.score) best = { score: score, root: r, q: q[0] };
      });
    });
    var names = pcs.map(function (p) { return NOTE[p]; });
    if (!best) return { name: null, root: bass, quality: null, bass: bass, notes: names };
    var nm = NOTE[best.root] + best.q + (best.root !== bass ? "/" + NOTE[bass] : "");
    return { name: nm, root: best.root, quality: best.q, bass: bass, notes: names };
  }

  /* ── Button ──────────────────────────────────────────────────────── */
  function Button(p) {
    var variant = p.variant || "quiet", size = p.size || "md";
    var rest = Object.assign({}, p); delete rest.variant; delete rest.size; delete rest.icon; delete rest.className;
    return h("button", Object.assign({ type: "button" }, rest, {
      className: cx("er-btn", "er-btn--" + variant, size === "sm" && "er-btn--sm", p.className)
    }), p.icon ? h(Icon, { name: p.icon }) : null, p.children);
  }

  /* ── Tag ─────────────────────────────────────────────────────────── */
  function Tag(p) {
    var tone = p.tone || "neutral";
    return h("span", { className: cx("er-tag", tone !== "neutral" && "er-tag--" + tone, p.className) },
      p.dot ? h("span", { className: "er-tag-dot", "aria-hidden": "true" }) : null, p.children);
  }

  /* ── Segmented ───────────────────────────────────────────────────── */
  function Segmented(p) {
    return h("div", { className: "er-seg", role: "group", "aria-label": p.label },
      (p.options || []).map(function (o) {
        return h("button", { key: o.value, type: "button", className: "er-seg-opt", "aria-pressed": o.value === p.value ? "true" : "false",
          onClick: function () { p.onChange && p.onChange(o.value); } }, o.label);
      }));
  }

  /* ── SideNav ─────────────────────────────────────────────────────── */
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function SideNav(p) {
    var ctl = p.activeId !== undefined;
    var st = useState(p.defaultActiveId || (p.items && p.items[0] && p.items[0].id));
    var active = ctl ? p.activeId : st[0];
    return h("nav", { className: "er-nav", "aria-label": p.heading || "Navegación" },
      h("div", { className: "er-nav-brand" },
        h("span", { className: "er-nav-lamp", "aria-hidden": "true" }),
        h("div", null, h("div", { className: "er-nav-name" }, p.brand || "Erato"),
          p.subtitle ? h("div", { className: "er-nav-sub" }, p.subtitle) : null)),
      h("div", { className: "er-label er-nav-heading" }, "// " + (p.heading || "composiciones")),
      h("ul", { className: "er-nav-list" }, (p.items || []).map(function (it, i) {
        return h("li", { key: it.id }, h("button", { type: "button", className: "er-nav-item", "aria-current": it.id === active ? "true" : undefined,
          onClick: function () { if (!ctl) st[1](it.id); p.onSelect && p.onSelect(it.id); } },
          h("span", { className: "er-nav-num" }, pad2(i)), h("span", null, it.label),
          it.meta ? h("span", { className: "er-nav-meta" }, it.meta) : null));
      })));
  }

  /* ── ChordEditor ─────────────────────────────────────────────────── */
  var TUNING = [40, 45, 50, 55, 59, 64], STR = ["E", "A", "D", "G", "B", "e"];
  function fretsToMidi(fr) { var out = []; fr.forEach(function (f, i) { if (f >= 0) out.push(TUNING[i] + f); }); return out; }
  function autoBase(fr) { var pos = fr.filter(function (f) { return f > 0; }); if (!pos.length) return 1; var mx = Math.max.apply(null, pos), mn = Math.min.apply(null, pos); return mx <= 5 ? 1 : mn; }

  function Fretboard(p) {
    var fr = p.frets, base = p.base, root = p.root, ed = p.editable;
    var X0 = 30, DX = 22, Y0 = 34, DY = 32, ROWS = 5, W = X0 + DX * 5 + 16, H = Y0 + DY * ROWS + 24;
    var els = [];
    for (var s = 0; s < 6; s++) els.push(h("line", { key: "s" + s, className: "er-fb-string", x1: X0 + s * DX, x2: X0 + s * DX, y1: Y0, y2: Y0 + DY * ROWS }));
    for (var r = 0; r <= ROWS; r++) {
      if (r === 0 && base === 1) els.push(h("line", { key: "nut", className: "er-fb-nut", x1: X0 - 1, x2: X0 + 5 * DX + 1, y1: Y0, y2: Y0 }));
      else els.push(h("line", { key: "f" + r, className: "er-fb-fret", x1: X0, x2: X0 + 5 * DX, y1: Y0 + r * DY, y2: Y0 + r * DY }));
    }
    if (base > 1) els.push(h("text", { key: "base", className: "er-fb-base", x: X0 - 10, y: Y0 + DY / 2 }, base + "fr"));
    fr.forEach(function (f, s) {
      var x = X0 + s * DX, midi = TUNING[s] + f, isRoot = f >= 0 && root !== undefined && midi % 12 === root;
      if (f === -1) els.push(h("path", { key: "m" + s, className: "er-fb-mute", d: "M" + (x - 5) + " 11l10 10M" + (x + 5) + " 11l-10 10" }));
      else if (f === 0) els.push(h("circle", { key: "m" + s, className: "er-fb-mark", cx: x, cy: 16, r: 5.5, style: isRoot ? { stroke: "var(--wine)" } : null }));
      else if (f >= base && f < base + ROWS) {
        var cy = Y0 + (f - base) * DY + DY / 2;
        els.push(h("circle", { key: "d" + s, className: cx("er-fb-dot", isRoot && "er-fb-dot--root"), cx: x, cy: cy, r: 8.5 }));
        els.push(h("text", { key: "dl" + s, className: "er-fb-dotlabel", x: x, y: cy }, NOTE[midi % 12]));
      }
      els.push(h("text", { key: "n" + s, className: "er-fb-txt", x: x, y: H - 4 }, f >= 0 ? NOTE[midi % 12] : STR[s]));
      if (ed) {
        els.push(h("rect", { key: "hm" + s, className: "er-fb-hit", x: x - DX / 2, y: 4, width: DX, height: Y0 - 8, rx: 4,
          onClick: function () { p.onSet(s, f === -1 ? 0 : (f === 0 ? -1 : 0)); } }, h("title", null, STR[s] + ": al aire / apagada")));
        for (var rr = 0; rr < ROWS; rr++) (function (row) {
          var target = base + row;
          els.push(h("rect", { key: "h" + s + "-" + row, className: "er-fb-hit", x: x - DX / 2, y: Y0 + row * DY + 1, width: DX, height: DY - 2, rx: 4,
            onClick: function () { p.onSet(s, f === target ? 0 : target); } }, h("title", null, STR[s] + ", traste " + target)));
        })(rr);
      }
    });
    return h("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img", "aria-label": "Diagrama de guitarra" }, els);
  }

  var WHITE = [0, 2, 4, 5, 7, 9, 11], BLACK_AFTER = { 0: 1, 2: 3, 5: 6, 7: 8, 9: 10 };
  function Piano(p) {
    var start = p.start || 48, oct = p.octaves || 2, on = p.notes, root = p.root, WW = 24, WH = 112, BW = 15, BH = 70;
    var whites = [], blacks = [], wi = 0;
    for (var o = 0; o < oct; o++) WHITE.forEach(function (pc) {
      var m = start + o * 12 + pc, x = wi * WW, act = on.indexOf(m) >= 0;
      whites.push(h("g", { key: "w" + m },
        h("rect", { className: cx("er-pk-white", act && "is-on", act && m % 12 === root && "is-root"), x: x + 1, y: 1, width: WW - 2, height: WH, rx: 4,
          onClick: function () { p.onToggle(m); } }, h("title", null, NOTE[pc])),
        act ? h("text", { className: "er-pk-lbl", x: x + WW / 2, y: WH - 10 }, NOTE[pc]) : (pc === 0 ? h("text", { className: "er-pk-c", x: x + WW / 2, y: WH - 10 }, "C" + (Math.floor(m / 12) - 1)) : null)));
      if (BLACK_AFTER[pc] !== undefined) {
        var bm = start + o * 12 + BLACK_AFTER[pc], bact = on.indexOf(bm) >= 0, bx = x + WW - BW / 2;
        blacks.push(h("g", { key: "b" + bm },
          h("rect", { className: cx("er-pk-black", bact && "is-on", bact && bm % 12 === root && "is-root"), x: bx, y: 1, width: BW, height: BH, rx: 3,
            onClick: function () { p.onToggle(bm); } }, h("title", null, NOTE[bm % 12])),
          bact ? h("text", { className: "er-pk-lbl", x: bx + BW / 2, y: BH - 8 }, NOTE[bm % 12].charAt(0)) : null));
      }
      wi++;
    });
    var W = wi * WW + 2;
    return h("svg", { width: W, height: WH + 2, viewBox: "0 0 " + W + " " + (WH + 2), role: "img", "aria-label": "Teclado de piano" }, whites, blacks);
  }

  function ChordName(p) {
    var info = p.info;
    if (!info || !info.name) return h("div", { className: "er-chord-name er-chord-empty" }, info ? "¿?" : "—");
    var base = NOTE[info.root], rest = info.name.slice(base.length), slash = rest.indexOf("/") >= 0 ? rest.slice(rest.indexOf("/")) : "", q = slash ? rest.slice(0, rest.indexOf("/")) : rest;
    return h("div", { className: "er-chord-name", "aria-live": "polite" }, base, q ? h("sup", null, q) : null, slash ? h("small", null, slash) : null);
  }

  function ChordEditor(p) {
    var editable = p.editable !== false;
    var initFr = p.defaultFrets || [-1, 3, 2, 0, 1, 0];
    var inst = useState(p.defaultInstrument || "guitar"), fr = useState(initFr), base = useState(p.defaultBaseFret || autoBase(initFr));
    var keys = useState(p.defaultNotes || fretsToMidi(initFr));
    var midi = inst[0] === "guitar" ? fretsToMidi(fr[0]) : keys[0];
    var info = detectChord(midi);
    var first = useRef(true);
    useEffect(function () {
      if (first.current) { first.current = false; return; }
      p.onChange && p.onChange({ instrument: inst[0], frets: fr[0], notes: midi, name: info && info.name });
    }, [inst[0], fr[0], keys[0]]);
    function setInst(v) {
      if (v === "piano" && inst[0] === "guitar") {
        var folded = [];
        fretsToMidi(fr[0]).forEach(function (m) { while (m < 48) m += 12; while (m > 71) m -= 12; if (folded.indexOf(m) < 0) folded.push(m); });
        keys[1](folded.sort(function (a, b) { return a - b; }));
      }
      inst[1](v);
    }
    function setString(s, f) { var n = fr[0].slice(); n[s] = f; fr[1](n); }
    function toggle(m) { var n = keys[0].slice(), i = n.indexOf(m); if (i >= 0) n.splice(i, 1); else n.push(m); keys[1](n.sort(function (a, b) { return a - b; })); }
    return h("div", { className: cx("er-chord er-panel", p.className) },
      h("div", { className: "er-chord-head" },
        h("div", null, h(ChordName, { info: info }),
          h("div", { className: "er-chord-notes" }, info ? info.notes.join(" · ") : "sin notas")),
        p.hideSwitch ? null : h(Segmented, { label: "Instrumento", value: inst[0], onChange: setInst,
          options: [{ value: "guitar", label: "guitarra" }, { value: "piano", label: "piano" }] })),
      h("div", { className: "er-chord-body" },
        inst[0] === "guitar" && editable ? h("button", { type: "button", className: "er-iconbtn", "aria-label": "Bajar traste", disabled: base[0] <= 1, onClick: function () { base[1](Math.max(1, base[0] - 1)); } }, h(Icon, { name: "left" })) : null,
        inst[0] === "guitar"
          ? h(Fretboard, { frets: fr[0], base: base[0], root: info ? info.root : undefined, editable: editable, onSet: setString })
          : h(Piano, { notes: keys[0], root: info ? info.root : undefined, onToggle: editable ? toggle : function () {} }),
        inst[0] === "guitar" && editable ? h("button", { type: "button", className: "er-iconbtn", "aria-label": "Subir traste", disabled: base[0] >= 15, onClick: function () { base[1](Math.min(15, base[0] + 1)); } }, h(Icon, { name: "right" })) : null));
  }

  /* ── TabEditor ───────────────────────────────────────────────────── */
  var EMPTY = function () { return ["", "", "", "", "", ""]; };
  function blankTab(n) { var a = []; for (var i = 0; i < n; i++) a.push(EMPTY()); return a; }
  /** tabToText(columns, names) → plain ASCII tab. Columns: arrays of 6 strings (high e first) or "|" for a bar line. */
  function tabToText(cols, names) {
    names = names || ["e", "B", "G", "D", "A", "E"];
    return names.map(function (n, s) {
      return n + "|" + cols.map(function (c) {
        if (c === "|") return "|";
        var w = Math.max.apply(null, c.map(function (v) { return v.length; }).concat([1]));
        var v = c[s] || ""; while (v.length < w) v += "-"; return v + "-";
      }).join("") + "|";
    }).join("\n");
  }
  var TECH = "hpbrs/\\~xv";
  function TabEditor(p) {
    var names = p.strings || ["e", "B", "G", "D", "A", "E"];
    var cols = useState(p.defaultValue || blankTab(p.columns || 16));
    var sel = useState({ c: 0, s: 0 });
    var grid = useRef(null);
    var first = useRef(true);
    useEffect(function () { if (first.current) { first.current = false; return; } p.onChange && p.onChange(cols[0]); }, [cols[0]]);
    function set(n) { cols[1](n); }
    function move(dc, ds) {
      var c = Math.max(0, Math.min(cols[0].length - 1, sel[0].c + dc)), s = Math.max(0, Math.min(names.length - 1, sel[0].s + ds));
      sel[1]({ c: c, s: s });
    }
    function insert(val) { var n = cols[0].slice(); n.splice(sel[0].c + 1, 0, val); set(n); sel[1]({ c: sel[0].c + 1, s: sel[0].s }); }
    function onKey(e) {
      var c = sel[0].c, s = sel[0].s, col = cols[0][c], k = e.key;
      if (k === "ArrowRight" || k === " ") { e.preventDefault(); if (c === cols[0].length - 1) { set(cols[0].concat([EMPTY()])); } sel[1]({ c: c + 1, s: s }); return; }
      if (k === "ArrowLeft") { e.preventDefault(); move(-1, 0); return; }
      if (k === "ArrowUp") { e.preventDefault(); move(0, -1); return; }
      if (k === "ArrowDown") { e.preventDefault(); move(0, 1); return; }
      if (k === "Enter") { e.preventDefault(); insert(EMPTY()); return; }
      if (k === "|") { e.preventDefault(); insert("|"); return; }
      if (col === "|") { if (k === "Backspace" || k === "Delete") { e.preventDefault(); var n0 = cols[0].slice(); n0.splice(c, 1); set(n0); sel[1]({ c: Math.max(0, c - 1), s: s }); } return; }
      var n = cols[0].slice(), cell = col[s];
      if (/^[0-9]$/.test(k)) {
        e.preventDefault();
        var run = (/[0-9]+$/.exec(cell) || [""])[0], nv;
        if (run.length === 1 && Number(run + k) <= 24) nv = cell + k;      // 1 → 12
        else if (cell && !run) nv = cell + k;                                // 5h → 5h7
        else nv = k;                                                         // reemplaza
        n[c] = col.slice(); n[c][s] = nv.slice(0, 6); set(n); return;
      }
      if (k.length === 1 && TECH.indexOf(k.toLowerCase()) >= 0) { e.preventDefault(); if (!cell && k.toLowerCase() !== "x") return; n[c] = col.slice(); n[c][s] = (k.toLowerCase() === "x" ? "x" : (cell + k.toLowerCase())).slice(0, 6); set(n); return; }
      if (k === "Backspace") { e.preventDefault(); if (cell) { n[c] = col.slice(); n[c][s] = cell.slice(0, -1); set(n); } else move(-1, 0); return; }
      if (k === "Delete") { e.preventDefault(); n[c] = col.slice(); n[c][s] = ""; set(n); return; }
    }
    function pick(c, s) { sel[1]({ c: c, s: s }); grid.current && grid.current.focus(); }
    var cur = sel[0];
    return h("div", { className: cx("er-tab er-panel", p.className) },
      h("div", { className: "er-tab-bar" },
        p.title ? h("div", { className: "er-label", style: { marginRight: "auto" } }, "// " + p.title) : h("span", { style: { marginRight: "auto" } }),
        h(Button, { size: "sm", variant: "ghost", icon: "bar", onClick: function () { insert("|"); grid.current.focus(); } }, "compás"),
        h(Button, { size: "sm", variant: "quiet", icon: "plus", onClick: function () { set(cols[0].concat(blankTab(8))); grid.current.focus(); } }, "8 tiempos")),
      h("div", { className: "er-tab-grid", tabIndex: 0, ref: grid, onKeyDown: onKey, role: "grid", "aria-label": "Tablatura: usa las flechas y escribe números de traste" },
        h("div", { className: "er-tab-names", "aria-hidden": "true" }, names.map(function (n, i) { return h("span", { key: i }, n); })),
        cols[0].map(function (col, c) {
          if (col === "|") return h("div", { key: c, className: cx("er-tab-barline", cur.c === c && "is-sel"), onClick: function () { pick(c, cur.s); } }, h("i"));
          return h("div", { key: c, className: cx("er-tab-col", cur.c === c && "er-tab-colsel") }, col.map(function (v, s) {
            return h("div", { key: s, role: "gridcell", "aria-selected": cur.c === c && cur.s === s, className: cx("er-tab-cell", cur.c === c && cur.s === s && "is-sel"), onMouseDown: function (e) { e.preventDefault(); pick(c, s); } }, v ? h("b", null, v) : null);
          }));
        })),
      p.hideHint ? null : h("div", { className: "er-tab-hint" },
        h("span", { className: "er-kbd" }, "0–24"), " traste · ", h("span", { className: "er-kbd" }, "h p b / ~ x"), " técnica · ",
        h("span", { className: "er-kbd" }, "← → ↑ ↓"), " moverse · ", h("span", { className: "er-kbd" }, "espacio"), " avanzar · ",
        h("span", { className: "er-kbd" }, "enter"), " insertar tiempo · ", h("span", { className: "er-kbd" }, "|"), " compás"));
  }

  /* ── LyricsViewer ────────────────────────────────────────────────── */
  function parseLine(line) {
    var segs = [], re = /\[([^\]]+)\]/g, last = 0, chord = null, m;
    while ((m = re.exec(line))) { if (m.index > last || chord !== null) segs.push({ chord: chord, text: line.slice(last, m.index) }); chord = m[1]; last = re.lastIndex; }
    segs.push({ chord: chord, text: line.slice(last) });
    return segs.filter(function (s) { return s.chord || s.text; });
  }
  function LyricsViewer(p) {
    var playing = useState(false), speed = useState(p.defaultSpeed || 24), max = useState(false);
    var box = useRef(null), raf = useRef(0), acc = useRef(0);
    var text = p.lyrics || "";
    var hasChords = /\[[^\]]+\]/.test(text) && p.showChords !== false;
    useEffect(function () {
      if (!playing[0]) return;
      var last = performance.now();
      function tick(t) {
        var el = box.current; if (!el) return;
        acc.current += (t - last) / 1000 * speed[0]; last = t;
        if (acc.current >= 1) { var step = Math.floor(acc.current); acc.current -= step; el.scrollTop += step; }
        if (el.scrollTop + el.clientHeight >= el.scrollHeight - 1) { playing[1](false); return; }
        raf.current = requestAnimationFrame(tick);
      }
      raf.current = requestAnimationFrame(tick);
      return function () { cancelAnimationFrame(raf.current); };
    }, [playing[0], speed[0]]);
    useEffect(function () {
      if (!max[0]) return;
      function esc(e) { if (e.key === "Escape") max[1](false); }
      window.addEventListener("keydown", esc); return function () { window.removeEventListener("keydown", esc); };
    }, [max[0]]);
    var body = [];
    text.split("\n").forEach(function (raw, i) {
      var line = raw.replace(/\s+$/, "");
      if (/^#\s*/.test(line)) { body.push(h("div", { key: i, className: "er-lyrics-section" }, line.replace(/^#\s*/, ""))); return; }
      if (!line) { body.push(h("div", { key: i, className: "er-lyric--gap" })); return; }
      if (!hasChords) { body.push(h("p", { key: i, className: "er-lyric" }, line.replace(/\[[^\]]+\]/g, ""))); return; }
      body.push(h("p", { key: i, className: "er-lyric" }, parseLine(line).map(function (s, j) {
        return h("span", { key: j, className: "er-seg-lyr" }, h("span", { className: "er-seg-chord" }, s.chord || ""), s.text || " ");
      })));
    });
    var mult = (speed[0] / 24).toFixed(1) + "×";
    return h("section", { className: cx("er-lyrics", max[0] && "er-lyrics--max", p.className), style: max[0] ? null : { height: p.height || 360 } },
      h("div", { className: "er-lyrics-top" },
        h("button", { type: "button", className: "er-iconbtn", "aria-label": playing[0] ? "Pausar desplazamiento" : "Desplazar automáticamente", onClick: function () { var el = box.current; if (!playing[0] && el && el.scrollTop + el.clientHeight >= el.scrollHeight - 1) el.scrollTop = 0; playing[1](!playing[0]); }, style: playing[0] ? { color: "var(--amber)" } : null }, h(Icon, { name: playing[0] ? "pause" : "play" })),
        h("div", { className: "er-lyrics-title" }, p.title || "Letra"),
        h("label", { className: "er-lyrics-speed" }, "velocidad",
          h("input", { type: "range", className: "er-range", min: 6, max: 120, step: 2, value: speed[0], onChange: function (e) { speed[1](Number(e.target.value)); }, "aria-label": "Velocidad de desplazamiento" }),
          h("output", null, mult)),
        h("button", { type: "button", className: "er-iconbtn", "aria-label": max[0] ? "Salir de pantalla completa" : "Maximizar", onClick: function () { max[1](!max[0]); } }, h(Icon, { name: max[0] ? "min" : "max" }))),
      h("div", { className: "er-lyrics-scroll", ref: box, style: { flex: 1 } }, body));
  }

  /* ── DemoPlayer ──────────────────────────────────────────────────── */
  function fmt(t) { t = Math.max(0, Math.floor(t)); return pad2(Math.floor(t / 60)) + ":" + pad2(t % 60); }
  function peaks(seed, n) {
    var x = 0; for (var i = 0; i < seed.length; i++) x = (x * 31 + seed.charCodeAt(i)) >>> 0;
    var out = []; for (var j = 0; j < n; j++) { x = (x * 1664525 + 1013904223) >>> 0; var r = x / 4294967296; var env = 0.45 + 0.55 * Math.sin(Math.PI * (j + 1) / (n + 1)); out.push(Math.max(0.12, env * (0.35 + 0.65 * r))); }
    return out;
  }
  function DemoPlayer(p) {
    var takes = useState(p.takes || []), curId = useState(p.defaultTakeId || (p.takes && p.takes[0] && p.takes[0].id));
    var t = useState(0), playing = useState(false), draft = useState(""), dur = useState(null);
    var audio = useRef(null), waveRef = useRef(null);
    var take = takes[0].filter(function (x) { return x.id === curId[0]; })[0] || takes[0][0];
    var D = dur[0] || (take && take.duration) || 1;
    var N = 72, pk = useMemo(function () { return peaks(take ? take.id : "x", N); }, [take && take.id]);
    useEffect(function () { t[1](0); playing[1](false); dur[1](null); }, [curId[0]]);
    useEffect(function () {
      if (!take) return;
      if (take.src && audio.current) { if (playing[0]) audio.current.play().catch(function () { playing[1](false); }); else audio.current.pause(); return; }
      if (!playing[0]) return;
      var last = performance.now(), id = setInterval(function () {
        var now = performance.now(); var nt = null;
        t[1](function (v) { nt = v + (now - last) / 1000; return nt >= D ? D : nt; }); last = now;
      }, 100);
      return function () { clearInterval(id); };
    }, [playing[0], take && take.id]);
    useEffect(function () { if (t[0] >= D && playing[0] && !(take && take.src)) playing[1](false); }, [t[0]]);
    function seek(v) { v = Math.max(0, Math.min(D, v)); t[1](v); if (audio.current && take.src) audio.current.currentTime = v; }
    function onWave(e) { var r = waveRef.current.getBoundingClientRect(); seek((e.clientX - r.left) / r.width * D); }
    function addComment() {
      var txt = draft[0].trim(); if (!txt) return;
      var c = { t: t[0], author: p.author || "Tú", text: txt };
      var next = takes[0].map(function (x) { return x.id === take.id ? Object.assign({}, x, { comments: (x.comments || []).concat([c]).sort(function (a, b) { return a.t - b.t; }) }) : x; });
      takes[1](next); draft[1](""); p.onComment && p.onComment(take.id, c);
    }
    if (!take) return h("div", { className: "er-player er-panel" }, "Aún no hay demos.");
    var comments = take.comments || [];
    return h("div", { className: cx("er-player", p.className) },
      h("div", { className: "er-takes" },
        h("div", { className: "er-label" }, "// demos"),
        takes[0].map(function (x, i) {
          return h("button", { key: x.id, type: "button", className: "er-take", "aria-current": x.id === take.id ? "true" : undefined, onClick: function () { curId[1](x.id); } },
            h("span", { className: "er-take-idx" }, pad2(i + 1)), h("span", { className: "er-take-title" }, x.title), h("span", { className: "er-take-dur" }, fmt(x.duration || 0)),
            h("span", { className: "er-take-meta" }, (x.date ? x.date + " · " : "") + (x.comments ? x.comments.length : 0) + " coment."));
        })),
      h("div", { className: "er-now" },
        take.src ? h("audio", { ref: audio, src: take.src, preload: "metadata", onTimeUpdate: function (e) { t[1](e.target.currentTime); }, onLoadedMetadata: function (e) { if (isFinite(e.target.duration)) dur[1](e.target.duration); }, onEnded: function () { playing[1](false); } }) : null,
        h("div", { className: "er-now-head" },
          h("button", { type: "button", className: "er-play", "aria-label": playing[0] ? "Pausar" : "Reproducir", onClick: function () { if (!playing[0] && t[0] >= D) seek(0); playing[1](!playing[0]); } }, h(Icon, { name: playing[0] ? "pause" : "play" })),
          h("div", { style: { minWidth: 0 } }, h("div", { className: "er-now-title" }, take.title), h("div", { className: "er-now-sub" }, (take.date || "") + (take.note ? " · " + take.note : "")))),
        h("div", { className: "er-wave", ref: waveRef, onClick: onWave },
          comments.map(function (c, i) {
            return h("button", { key: i, type: "button", className: "er-pin", style: { left: (c.t / D * 100) + "%" }, "aria-label": fmt(c.t) + " — " + c.author + ": " + c.text, title: fmt(c.t) + " — " + c.text, onClick: function (e) { e.stopPropagation(); seek(c.t); } });
          }),
          h("svg", { viewBox: "0 0 " + (N * 6) + " 64", preserveAspectRatio: "none", "aria-hidden": "true" },
            pk.map(function (v, i) { var bh = v * 60; return h("rect", { key: i, className: cx("er-wave-bar", (i + 0.5) / N <= t[0] / D && "is-past"), x: i * 6 + 1, y: (64 - bh) / 2, width: 3.5, height: bh, rx: 1.75 }); })),
          h("div", { className: "er-wave-head", style: { left: (t[0] / D * 100) + "%" } })),
        h("div", { className: "er-times" }, h("b", null, fmt(t[0])), h("span", null, fmt(D))),
        comments.length ? h("ul", { className: "er-comments" }, comments.map(function (c, i) {
          return h("li", { key: i, className: cx("er-comment", Math.abs(c.t - t[0]) < 2.5 && "is-near"), onClick: function () { seek(c.t); } },
            h("span", { className: "er-comment-t" }, fmt(c.t)),
            h("span", null, h("span", { className: "er-comment-who" }, c.author), h("span", { className: "er-comment-txt" }, c.text)));
        })) : null,
        h("div", { className: "er-compose" },
          h("input", { className: "er-input", value: draft[0], placeholder: "Comentar en " + fmt(t[0]) + "…", onChange: function (e) { draft[1](e.target.value); }, onKeyDown: function (e) { if (e.key === "Enter") addComment(); } }),
          h(Button, { onClick: addComment, disabled: !draft[0].trim() }, "Comentar"))));
  }

  /* ── TodoList ────────────────────────────────────────────────────── */
  var uid = 0;
  function TodoList(p) {
    var items = useState(p.defaultItems || []), draft = useState("");
    var first = useRef(true);
    useEffect(function () { if (first.current) { first.current = false; return; } p.onChange && p.onChange(items[0]); }, [items[0]]);
    function add() { var v = draft[0].trim(); if (!v) return; items[1](items[0].concat([{ id: "t" + Date.now() + (uid++), text: v, done: false }])); draft[1](""); }
    function upd(id, f) { items[1](items[0].map(function (x) { return x.id === id ? f(x) : x; })); }
    var left = items[0].filter(function (x) { return !x.done; }).length, done = items[0].length - left;
    return h("div", { className: cx("er-todo er-panel", p.className) },
      p.title ? h("div", { className: "er-label" }, "// " + p.title) : null,
      h("div", { className: "er-compose" },
        h("input", { className: "er-input", value: draft[0], placeholder: p.placeholder || "Nueva tarea…", onChange: function (e) { draft[1](e.target.value); }, onKeyDown: function (e) { if (e.key === "Enter") add(); } }),
        h(Button, { variant: "primary", icon: "plus", onClick: add, disabled: !draft[0].trim() }, "Agregar")),
      items[0].length ? h("ul", { className: "er-todo-list" }, items[0].map(function (x) {
        return h("li", { key: x.id, className: cx("er-todo-item", x.done && "is-done") },
          h("button", { type: "button", role: "checkbox", className: "er-check", "aria-checked": x.done ? "true" : "false", "aria-label": x.text, onClick: function () { upd(x.id, function (y) { return Object.assign({}, y, { done: !y.done }); }); } }, x.done ? h(Icon, { name: "check" }) : null),
          h("span", { className: "er-todo-text" }, x.text),
          h("button", { type: "button", className: "er-iconbtn", "aria-label": "Borrar " + x.text, onClick: function () { items[1](items[0].filter(function (y) { return y.id !== x.id; })); } }, h(Icon, { name: "x" })));
      })) : h("div", { className: "er-todo-empty" }, "Nada pendiente. Toca otra vez desde el coro."),
      h("div", { className: "er-todo-foot" },
        h("span", null, left + (left === 1 ? " pendiente" : " pendientes") + " · " + done + (done === 1 ? " hecha" : " hechas")),
        done ? h(Button, { size: "sm", variant: "ghost", onClick: function () { items[1](items[0].filter(function (x) { return !x.done; })); } }, "Limpiar hechas") : null));
  }

  window.Erato = Object.assign(window.Erato || {}, {
    Button: Button, Tag: Tag, Segmented: Segmented, SideNav: SideNav, ChordEditor: ChordEditor, TabEditor: TabEditor,
    LyricsViewer: LyricsViewer, DemoPlayer: DemoPlayer, TodoList: TodoList, Icon: Icon, detectChord: detectChord, tabToText: tabToText
  });
})();
