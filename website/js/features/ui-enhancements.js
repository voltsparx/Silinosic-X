/* Shared UX enhancements: scroll progress, back-to-top, scrollspy, copy buttons,
   reveal-on-scroll, keyboard shortcuts, accessibility wiring. */
function initUiEnhancements() {
  const body = document.body;
  const topbar = document.getElementById("topbar");
  const main = document.getElementById("main");

  /* Skip link + main landmark */
  if (main) {
    main.setAttribute("tabindex", "-1");
    if (!document.querySelector(".skip-link")) {
      const skip = document.createElement("a");
      skip.className = "skip-link";
      skip.href = "#main";
      skip.textContent = "Skip to content";
      body.prepend(skip);
    }
  }

  /* Progress bar + back to top */
  const progress = document.createElement("div");
  progress.id = "scroll-progress";
  progress.setAttribute("aria-hidden", "true");
  body.appendChild(progress);

  const topBtn = document.createElement("button");
  topBtn.id = "back-to-top";
  topBtn.type = "button";
  topBtn.setAttribute("aria-label", "Back to top");
  topBtn.innerHTML = "&#8593;";
  topBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  body.appendChild(topBtn);

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(() => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = max > 0 ? Math.min(window.scrollY / max, 1) : 0;
      progress.style.transform = `scaleX(${ratio})`;
      topBtn.classList.toggle("is-visible", window.scrollY > 700);
      topbar?.classList.toggle("is-scrolled", window.scrollY > 8);
      ticking = false;
    });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* Scrollspy: highlight the sidebar entry for the section in view */
  const sections = Array.from(main?.querySelectorAll("section[id]") || []);
  if (sections.length && "IntersectionObserver" in window) {
    const spy = new IntersectionObserver((items) => {
      const visible = items.filter((i) => i.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (!visible.length) return;
      const id = visible[0].target.id;
      if (DocsState.currentSection === id) return;
      DocsState.currentSection = id;
      if (window.location.hash && window.location.hash.slice(1) !== id) {
        window.history.replaceState(null, "", `${DocsState.currentPage}#${id}`);
      }
      updateSidebar();
      document.querySelector(".sidebar-link.is-current")?.scrollIntoView({ block: "nearest" });
    }, { rootMargin: "-20% 0px -65% 0px", threshold: 0 });
    sections.forEach((s) => spy.observe(s));
  }

  /* Copy buttons on code blocks and command snippets */
  const copy = async (text, btn) => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      btn.textContent = "Copied";
      btn.classList.add("is-copied");
    } catch (e) {
      btn.textContent = "Failed";
    }
    window.setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("is-copied"); }, 1600);
  };
  document.querySelectorAll(".code-block").forEach((block) => {
    const head = block.querySelector(".code-head");
    const pre = block.querySelector(".code-body");
    if (!head || !pre) return;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.setAttribute("aria-label", "Copy code to clipboard");
    btn.addEventListener("click", () => {
      const lines = pre.innerText.split("\n").filter((l) => !l.trim().startsWith("#"));
      copy(lines.join("\n").trim(), btn);
    });
    head.appendChild(btn);
  });

  /* Reveal on scroll (graceful: content visible without JS / observer) */
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const targets = Array.from(document.querySelectorAll(".page-section, .page-intro"));
    body.classList.add("js-reveal");
    const reveal = new IntersectionObserver((items) => {
      items.forEach((item) => {
        if (item.isIntersecting) {
          item.target.classList.add("is-visible");
          reveal.unobserve(item.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.04 });
    targets.forEach((t) => reveal.observe(t));
    /* Safety net so nothing stays hidden (e.g. printing, anchor jumps) */
    window.setTimeout(() => targets.forEach((t) => t.classList.add("is-visible")), 2500);
    window.addEventListener("beforeprint", () => targets.forEach((t) => t.classList.add("is-visible")));
  }

  /* Global keys: "/" or Ctrl/Cmd+K focuses search, Escape closes panels */
  document.addEventListener("keydown", (event) => {
    const tag = (event.target.tagName || "").toLowerCase();
    const typing = tag === "input" || tag === "textarea" || event.target.isContentEditable;
    if ((event.key === "/" && !typing) || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k")) {
      event.preventDefault();
      DocsElements.searchInput?.focus();
      DocsElements.searchInput?.select();
    }
    if (event.key === "Escape") {
      if (DocsState.navOpen) setNavOpen(false);
      if (DocsElements.contactPopover && !DocsElements.contactPopover.hidden) {
        DocsElements.contactPopover.hidden = true;
        DocsElements.contactToggle?.setAttribute("aria-expanded", "false");
        DocsElements.contactToggle?.focus();
      }
    }
  });

  /* Close mobile nav when the viewport grows past the breakpoint */
  window.matchMedia("(min-width: 1081px)").addEventListener?.("change", (e) => { if (e.matches) setNavOpen(false); });

  /* External links: safe rel */
  document.querySelectorAll('a[target="_blank"]').forEach((a) => {
    const rel = new Set((a.getAttribute("rel") || "").split(/\s+/).filter(Boolean));
    rel.add("noopener"); rel.add("noreferrer");
    a.setAttribute("rel", Array.from(rel).join(" "));
  });
}
