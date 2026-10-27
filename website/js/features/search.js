function initSearch() {
  const input = DocsElements.searchInput;
  const box = DocsElements.searchResults;
  if (!input || !box) {
    return;
  }

  let items = [];
  let active = -1;

  const hideResults = () => {
    box.hidden = true;
    box.innerHTML = "";
    items = [];
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const highlight = (text, terms) => {
    let out = escapeHtml(text);
    for (const term of terms) {
      if (!term) continue;
      const safe = escapeHtml(term).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      out = out.replace(new RegExp(`(${safe})`, "ig"), "<mark>$1</mark>");
    }
    return out;
  };

  const setActive = (index) => {
    const nodes = box.querySelectorAll(".search-result");
    if (!nodes.length) return;
    active = (index + nodes.length) % nodes.length;
    nodes.forEach((node, i) => {
      node.classList.toggle("is-active", i === active);
      node.setAttribute("aria-selected", i === active ? "true" : "false");
    });
    nodes[active].scrollIntoView({ block: "nearest" });
    input.setAttribute("aria-activedescendant", nodes[active].id);
  };

  const score = (entry, terms) => {
    const title = entry.title.toLowerCase();
    const hint = entry.hint.toLowerCase();
    const group = entry.group.toLowerCase();
    const page = entry.page.toLowerCase();
    let total = 0;
    for (const term of terms) {
      if (title.startsWith(term)) total += 6;
      else if (title.includes(term)) total += 4;
      else if (group.includes(term) || page.includes(term)) total += 2;
      else if (hint.includes(term)) total += 1;
      else return 0; // every word must match somewhere
    }
    return total;
  };

  const showResults = (results, terms) => {
    input.setAttribute("aria-expanded", "true");
    box.hidden = false;
    if (!results.length) {
      box.innerHTML = '<div class="empty-state">No matching section or page.</div>';
      return;
    }
    box.innerHTML = results
      .map((item, i) => `
        <a class="search-result" id="search-opt-${i}" role="option" href="${pageLink(item.page, item.id)}">
          <span class="search-result-title">${highlight(item.title, terms)}</span>
          <span class="search-result-meta">${escapeHtml(item.group)} &middot; ${escapeHtml(DocsData.pages[item.page]?.title || item.page)} &middot; ${highlight(item.hint, terms)}</span>
        </a>`)
      .join("");
  };

  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    if (!query) {
      hideResults();
      return;
    }
    const terms = query.split(/\s+/).filter(Boolean);
    items = DocsData.entries
      .map((entry) => ({ entry, s: score(entry, terms) }))
      .filter((r) => r.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 8)
      .map((r) => r.entry);
    active = -1;
    showResults(items, terms);
  });

  input.addEventListener("focus", () => {
    if (input.value.trim()) input.dispatchEvent(new Event("input"));
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideResults();
      input.blur();
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      if (box.hidden && input.value.trim()) input.dispatchEvent(new Event("input"));
      setActive(active + 1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(active - 1);
    } else if (event.key === "Enter") {
      const target = items[active >= 0 ? active : 0];
      if (target && !box.hidden) {
        event.preventDefault();
        hideResults();
        input.blur();
        navigateToEntry(target);
      }
    }
  });

  box.addEventListener("click", (event) => {
    if (event.target.closest(".search-result")) {
      window.setTimeout(hideResults, 0);
    }
  });

  document.addEventListener("click", (event) => {
    if (!box.contains(event.target) && !input.contains(event.target)) {
      hideResults();
    }
  });
}
