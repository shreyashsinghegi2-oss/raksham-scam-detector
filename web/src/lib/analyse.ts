/** Plain pattern checks on the text. They describe the message and never change the score. */
const TLD = "com|in|org|net|co|xyz|top|club|online|site|link|click|icu|cc|vip|work|live|shop|buzz|info|app|me|ly|cfd|sbs";
const urlRe = () => new RegExp('(?:https?:\\/\\/|www\\.)[^\\s<>"\')]+|\\b[a-z0-9][a-z0-9-]*(?:\\.[a-z0-9-]+)*\\.(?:' + TLD + ')\\b(?:\\/[^\\s<>"\')]*)?', "gi");

export const FACTS: [string, RegExp][] = [
  ["Link", urlRe()],
  ["Phone number", /(?:\+?91[\s-]?)?[6-9]\d{9}\b|\b[6-9]\d[x*]{4,}\d{2}\b|\b1800[\s-]?\d{3}[\s-]?\d{3,4}\b/i],
  ["Money amount", /(?:₹|\brs\.?|\binr)\s?[\d,]+|\b[\d,]+\s?(?:rupees|lakh|lac|crore)\b|रुपये|लाख/i],
  ["OTP, PIN or password", /\b(?:otp|pin|cvv|mpin|password|passcode)\b|ओटीपी|पिन/i],
  ["Urgent wording", /\b(?:immediately|urgent(?:ly)?|right now|tonight|today|within \d+\s?(?:hours?|hrs?|minutes?|mins?)|last chance|turant|abhi|jaldi)\b|तुरंत|अभी/i],
  ["Threat wording", /\b(?:blocked?|suspended?|disconnect(?:ed)?|arrest(?:ed)?|legal action|frozen|freeze|penalty|fir)\b|\bband ho\b|\bkat jayega\b/i],
  ["Authority or brand", /\b(?:police|cbi|ncb|rbi|trai|income tax|customs|court|cyber ?crime|bank|sbi|hdfc|icici|paytm|amazon|customer care|officer)\b/i],
];

export const presentFacts = (text: string) =>
  new Set(FACTS.filter(([, re]) => { re.lastIndex = 0; return re.test(text); }).map(([name]) => name));

const SHORTENERS = new Set(["bit.ly", "tinyurl.com", "t.co", "goo.gl", "cutt.ly", "rb.gy", "is.gd", "tiny.cc", "shorturl.at", "ow.ly", "buff.ly"]);
const ODD_TLDS = new Set(["xyz", "top", "club", "online", "site", "link", "click", "icu", "cc", "vip", "work", "live", "shop", "buzz", "cfd", "sbs"]);

export type LinkReport = { raw: string; host: string; notes: string[] };

export function analyseLinks(text: string): LinkReport[] {
  const seen = new Set<string>();
  const out: LinkReport[] = [];
  for (const match of text.matchAll(urlRe())) {
    const raw = match[0].replace(/[.,;:!?]+$/, "");
    if (seen.has(raw.toLowerCase())) continue;
    seen.add(raw.toLowerCase());
    const host = raw.replace(/^https?:\/\//i, "").split(/[/?#]/)[0].replace(/:\d+$/, "").toLowerCase();
    const notes: string[] = [];
    if (/^http:\/\//i.test(raw)) notes.push("Uses http, not https");
    if (SHORTENERS.has(host)) notes.push("A link shortener hides the real destination");
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) notes.push("The address is a raw IP number");
    if (host.includes("xn--")) notes.push("Contains look-alike characters (punycode)");
    const tld = host.split(".").pop() ?? "";
    if (ODD_TLDS.has(tld)) notes.push("Ends in ." + tld + ", a cheap ending common on throwaway sites");
    if ((host.match(/-/g) ?? []).length >= 3 || host.length > 30 || host.split(".").length > 4) notes.push("Long or hyphen-heavy address");
    out.push({ raw, host, notes });
  }
  return out;
}
