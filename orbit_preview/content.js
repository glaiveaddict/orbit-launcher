(() => {
  const SECTION_ID = "orbit-pv-section";

  function myUserId() {
    const meta = document.querySelector('meta[name="user-data"]');
    return meta ? meta.dataset.userid : null;
  }

  function pageInfo() {
    const m = location.pathname.match(/\/users\/(\d+)\/(profile|inventory)/i);
    return m ? { userId: m[1], page: m[2].toLowerCase() } : null;
  }

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function priceText(item) {
    if (typeof item.rap === "number") return "RAP R$ " + item.rap.toLocaleString();
    if (typeof item.price === "number") return "R$ " + item.price.toLocaleString();
    return "Off sale";
  }

  function card(item) {
    const a = el("a", "orbit-pv-card");
    a.href = "https://www.roblox.com/catalog/" + encodeURIComponent(item.id);
    a.title = item.name + " (preview - not owned)";

    const thumb = el("div", "orbit-pv-thumb");
    if (item.thumb) {
      const img = el("img");
      img.src = item.thumb;
      img.alt = "";
      img.loading = "lazy";
      thumb.appendChild(img);
    }
    thumb.appendChild(el("div", "orbit-pv-band", "PREVIEW · NOT OWNED"));
    a.appendChild(thumb);

    a.appendChild(el("div", "orbit-pv-name", item.name));
    a.appendChild(el("div", "orbit-pv-price", priceText(item)));
    a.appendChild(el("div", "orbit-pv-foot", "Orbit preview"));
    return a;
  }

  function buildSection(items) {
    const section = el("section", "orbit-pv-section");
    section.id = SECTION_ID;

    const head = el("div", "orbit-pv-head");
    head.appendChild(el("h2", "orbit-pv-title", "Preview items"));
    head.appendChild(el("span", "orbit-pv-pill", "NOT OWNED · only visible to you"));
    section.appendChild(head);

    const grid = el("div", "orbit-pv-grid");
    items.forEach((item) => grid.appendChild(card(item)));
    section.appendChild(grid);
    return section;
  }

  let rendering = false;
  async function render(force) {
    if (rendering) return;
    rendering = true;
    try {
      const existing = document.getElementById(SECTION_ID);
      const info = pageInfo();
      const me = myUserId();

      if (!info || (me && me !== info.userId)) {
        if (existing) existing.remove();
        return;
      }
      const { items = [], enabled = true } = await chrome.storage.local.get(["items", "enabled"]);
      if (!enabled || !items.length) {
        if (existing) existing.remove();
        return;
      }
      const key = items.map((i) => i.id).join(",");
      if (existing && existing.dataset.key === key && !force) return;

      const section = buildSection(items);
      section.dataset.key = key;
      const host = document.querySelector("#content") || document.querySelector("main") || document.body;
      if (existing) existing.replaceWith(section);
      else host.prepend(section);
    } catch (e) {

    } finally {
      rendering = false;
    }
  }

  chrome.storage.onChanged.addListener(() => render(true));

  setInterval(() => render(false), 1500);
  render(true);
})();
