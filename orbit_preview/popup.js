const MAX_ITEMS = 60;
const $ = (id) => document.getElementById(id);

function parseId(text) {
  text = text.trim();
  if (/^\d+$/.test(text)) return text;
  const m = text.match(/\/(?:catalog|library)\/(\d+)/i);
  return m ? m[1] : null;
}

async function getJson(url) {
  const res = await fetch(url, { credentials: "omit" });
  if (!res.ok) throw new Error(url + " -> " + res.status);
  return res.json();
}

async function itemDetails(id) {
  const item = { id, name: "Item " + id, price: null, rap: null, thumb: null };


  try {
    const d = await getJson(`https://catalog.roblox.com/v1/catalog/items/${id}/details?itemType=Asset`);
    item.name = d.name || item.name;
    item.price = typeof d.price === "number" ? d.price : (typeof d.lowestPrice === "number" ? d.lowestPrice : null);
    item.limited = Array.isArray(d.itemRestrictions) && d.itemRestrictions.some((r) => /Limited/i.test(r));
  } catch (e) {
    try {
      const d = await getJson(`https://economy.roblox.com/v2/assets/${id}/details`);
      item.name = d.Name || item.name;
      item.price = typeof d.PriceInRobux === "number" ? d.PriceInRobux : null;
      item.limited = !!(d.IsLimited || d.IsLimitedUnique);
    } catch (e2) {  }
  }

  if (item.limited) {
    try {
      const r = await getJson(`https://economy.roblox.com/v1/assets/${id}/resale-data`);
      if (typeof r.recentAveragePrice === "number") item.rap = r.recentAveragePrice;
    } catch (e) {  }
  }


  for (let attempt = 0; attempt < 2 && !item.thumb; attempt++) {
    try {
      const t = await getJson(`https://thumbnails.roblox.com/v1/assets?assetIds=${id}&returnPolicy=PlaceHolder&size=420x420&format=Png&isCircular=false`);
      const entry = t.data && t.data[0];
      if (entry && entry.imageUrl && entry.state === "Completed") item.thumb = entry.imageUrl;
      else await new Promise((r) => setTimeout(r, 1200));
    } catch (e) { break; }
  }
  return item;
}

async function load() {
  const { items = [], enabled = true } = await chrome.storage.local.get(["items", "enabled"]);
  return { items, enabled };
}

async function renderList() {
  const { items, enabled } = await load();
  $("enabled").checked = enabled;
  const list = $("list");
  list.textContent = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "item";
    const img = document.createElement("img");
    if (item.thumb) img.src = item.thumb;
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = item.name;
    const rm = document.createElement("button");
    rm.textContent = "×";
    rm.title = "Remove";
    rm.onclick = async () => {
      const cur = (await load()).items.filter((i) => i.id !== item.id);
      await chrome.storage.local.set({ items: cur });
      renderList();
    };
    row.append(img, name, rm);
    list.appendChild(row);
  });
}

$("add").onclick = async () => {
  const id = parseId($("item").value);
  const msg = $("msg");
  if (!id) { msg.textContent = "Paste an item ID or a roblox.com/catalog/... link."; return; }
  const { items } = await load();
  if (items.some((i) => i.id === id)) { msg.textContent = "Already added."; return; }
  if (items.length >= MAX_ITEMS) { msg.textContent = `You can preview up to ${MAX_ITEMS} items.`; return; }
  $("add").disabled = true;
  msg.textContent = "Looking up item...";
  try {
    const item = await itemDetails(id);
    await chrome.storage.local.set({ items: [...items, item] });
    msg.textContent = "Added " + item.name;
    $("item").value = "";
    renderList();
  } finally {
    $("add").disabled = false;
  }
};

$("item").addEventListener("keydown", (e) => { if (e.key === "Enter") $("add").click(); });
$("enabled").onchange = (e) => chrome.storage.local.set({ enabled: e.target.checked });

renderList();
