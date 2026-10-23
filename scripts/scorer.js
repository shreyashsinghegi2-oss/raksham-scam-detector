/* Browser version of deploy/api/_lite.py: TF-IDF features and logistic regression for the Raksham scam detector.
   It must give the same answers as the Python scorer; scripts/check_standalone.js compares them. */
(function (root) {
  "use strict";
  const WORD_CHAR = /[\p{L}\p{N}_]/u; // Python's \w for text: letters, digits and underscore (not combining vowel signs)
  const TYPE_MIN_CONFIDENCE = 0.5;

  function wordGrams(text, lo, hi) {
    const tokens = [];
    let run = [];
    const flush = () => { if (run.length >= 2) tokens.push(run.join("")); run = []; };
    for (const ch of Array.from(text.toLowerCase())) { if (WORD_CHAR.test(ch)) run.push(ch); else flush(); }
    flush();
    const grams = [];
    for (let n = lo; n <= hi; n++) for (let i = 0; i + n <= tokens.length; i++) grams.push(tokens.slice(i, i + n).join(" "));
    return grams;
  }

  function charWbGrams(text, lo, hi) {
    const grams = [];
    for (const raw of text.toLowerCase().split(/\s+/)) {
      if (!raw) continue;
      const word = Array.from(" " + raw + " ");
      for (let n = lo; n <= hi; n++) {
        let offset = 0;
        grams.push(word.slice(offset, offset + n).join(""));
        while (offset + n < word.length) { offset += 1; grams.push(word.slice(offset, offset + n).join("")); }
        if (offset === 0) break; // a word shorter than n counts once
      }
    }
    return grams;
  }

  function floats(b64, Type) {
    const bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new Type(bytes.buffer);
  }

  function makeSpace(spec, vocabs, arrays, prefix) {
    const parts = [["word", wordGrams], ["char", charWbGrams]].map(([name, analyzer]) => ({
      analyzer, ngram: spec[name].ngram, offset: spec[name].offset,
      vocab: new Map(Object.entries(vocabs[prefix + "_" + name])), idf: arrays[prefix + "_" + name + "_idf"],
    }));
    const wordTerms = new Array(spec.word.size).fill("");
    for (const [term, i] of parts[0].vocab) wordTerms[i] = term;
    return { parts, features: spec.features, wordTerms };
  }

  function vector(space, text) {
    const idx = [], val = [];
    for (const part of space.parts) {
      const counts = new Map();
      for (const gram of part.analyzer(text, part.ngram[0], part.ngram[1])) {
        const j = part.vocab.get(gram);
        if (j !== undefined) counts.set(j, (counts.get(j) || 0) + 1);
      }
      let norm = 0;
      const local = [];
      for (const [j, c] of counts) { const v = (1 + Math.log(c)) * part.idf[j]; local.push([j + part.offset, v]); norm += v * v; }
      norm = Math.sqrt(norm);
      for (const [j, v] of local) { idx.push(j); val.push(norm ? v / norm : v); }
    }
    return { idx, val };
  }

  function createScorer(data) {
    const meta = data.meta;
    const arrays = {};
    for (const [k, v] of Object.entries(data.arrays)) arrays[k] = floats(v, k === "type_coef" ? Float32Array : Float64Array);
    const det = makeSpace(meta.det_space, data.vocabs, arrays, "det");
    const kind = makeSpace(meta.type_space, data.vocabs, arrays, "type");
    const stop = new Set(meta.stop_words);
    const classes = meta.type_classes, K = classes.length, F = kind.features;

    function probability(idx, val) {
      let z = meta.det_intercept;
      for (let i = 0; i < idx.length; i++) z += val[i] * arrays.det_coef[idx[i]];
      return z >= 0 ? 1 / (1 + Math.exp(-z)) : Math.exp(z) / (1 + Math.exp(z));
    }

    function typeProbabilities(text) {
      const { idx, val } = vector(kind, text);
      const z = new Array(K);
      for (let k = 0; k < K; k++) {
        let s = arrays.type_intercept[k];
        for (let i = 0; i < idx.length; i++) s += val[i] * arrays.type_coef[k * F + idx[i]];
        z[k] = s;
      }
      const m = Math.max(...z), e = z.map((s) => Math.exp(s - m)), total = e.reduce((a, b) => a + b, 0);
      return e.map((s) => s / total);
    }

    function signals(idx, val, k = 3) {
      const charStart = det.parts[1].offset, found = [];
      const order = idx.map((_, i) => i).sort((a, b) => idx[a] - idx[b]); // feature order, so ties resolve as in scikit-learn
      for (const i of order) {
        const j = idx[i];
        if (j >= charStart) continue; // character features are not words
        const contribution = val[i] * arrays.det_coef[j], term = det.wordTerms[j];
        if (contribution > 0 && !term.split(" ").every((w) => stop.has(w) || /^\d+$/.test(w))) found.push([contribution, term]);
      }
      found.sort((a, b) => b[0] - a[0]); // stable
      return found.slice(0, k).map((pair) => pair[1]);
    }

    function predict(texts, strict) {
      const threshold = meta.thresholds[strict ? "strict" : "balanced"];
      return texts.map((text) => {
        const { idx, val } = vector(det, text);
        const p = probability(idx, val);
        const item = { verdict: p >= threshold ? "scam" : "genuine", scam_probability: Math.round(p * 1000) / 1000, threshold };
        if (p >= threshold) {
          const kinds = typeProbabilities(text);
          let top = 0;
          for (let k = 1; k < K; k++) if (kinds[k] > kinds[top]) top = k;
          const confidence = Math.round(kinds[top] * 1000) / 1000;
          item.scam_type = confidence >= TYPE_MIN_CONFIDENCE ? classes[top] : "uncertain";
          item.scam_type_guess = classes[top];
          item.scam_type_confidence = confidence;
          item.signals = signals(idx, val);
        }
        return item;
      });
    }

    return { predict, meta, rawProbability: (text) => { const v = vector(det, text); return probability(v.idx, v.val); } };
  }

  const api = { createScorer };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.RakshamScorer = api;
})(typeof self !== "undefined" ? self : this);
