const EasterEgg = (() => {
  let toastTimer = null;
  let overdriveTimer = null;
  let brandTapCount = 0;
  let brandTapTimer = null;
  let heroTapCount = 0;
  let heroTapTimer = null;
  let heroStarActive = false;

  const secretQueries = {
    fusioncore: () => activateOverdrive("Fusion lane synchronized"),
    threatconductor: () => showToast("Threat conductor armed", "Priority signal stack elevated."),
    orbitmatrix: () => showToast("Orbit link matrix", "Outbound link constellation projected."),
    ember: () => toggleBlueprintMode(),
    silinosic_x: () => showToast("Legacy alias detected", "Public naming stays Silinosic-X.")
  };

  function ensureToast() {
    let toast = document.getElementById("egg-toast");
    if (toast) {
      return toast;
    }

    toast = document.createElement("div");
    toast.id = "egg-toast";
    toast.className = "egg-toast";
    toast.setAttribute("aria-live", "polite");
    DocsElements.body.appendChild(toast);
    return toast;
  }

  function showToast(title, copy = "") {
    const toast = ensureToast();
    toast.innerHTML = `<span class="egg-toast-title">${escapeHtml(title)}</span><span class="egg-toast-copy">${escapeHtml(copy)}</span>`;
    toast.classList.add("show");

    if (toastTimer) {
      window.clearTimeout(toastTimer);
    }

    toastTimer = window.setTimeout(() => {
      toast.classList.remove("show");
    }, 2200);
  }

  function pulseLogo(node) {
    if (!node) {
      return;
    }
    node.classList.remove("egg-logo-pulse");
    void node.offsetWidth;
    node.classList.add("egg-logo-pulse");
  }

  function spinHeroLogo(node) {
    if (!node) {
      return;
    }

    node.classList.remove("egg-hero-spin");
    void node.offsetWidth;
    node.classList.add("egg-hero-spin");
  }

  function wait(ms) {
    return new Promise((resolve) => {
      window.setTimeout(resolve, ms);
    });
  }

  function spawnRibbons(count = 18) {
    const layer = document.createElement("div");
    layer.className = "egg-ribbon-layer";
    DocsElements.body.appendChild(layer);

    const palette = ["#ff8a1d", "#ffb259", "#ffd36f", "#73d4ff", "#67d6a8"];
    const total = Math.max(10, Math.min(count, 40));

    for (let index = 0; index < total; index += 1) {
      const ribbon = document.createElement("span");
      ribbon.className = "egg-ribbon";
      ribbon.style.left = `${Math.random() * 100}%`;
      ribbon.style.background = `linear-gradient(180deg, ${palette[index % palette.length]}, rgba(255,255,255,0.12))`;
      ribbon.style.setProperty("--egg-drift", `${(Math.random() * 220) - 110}px`);
      ribbon.style.animationDuration = `${2.8 + (Math.random() * 1.8)}s`;
      ribbon.style.animationDelay = `${Math.random() * 0.25}s`;
      layer.appendChild(ribbon);
    }

    window.setTimeout(() => {
      layer.remove();
    }, 4200);
  }

  function activateOverdrive(message) {
    DocsElements.body.classList.add("egg-overdrive");
    pulseLogo(DocsElements.topbarLogo);
    pulseLogo(DocsElements.homeHeroLogo);
    showToast(message, "Signal intensity boosted for a short burst.");

    if (overdriveTimer) {
      window.clearTimeout(overdriveTimer);
    }

    overdriveTimer = window.setTimeout(() => {
      DocsElements.body.classList.remove("egg-overdrive");
    }, 7000);
  }

  function toggleBlueprintMode() {
    const enabled = DocsElements.body.classList.toggle("egg-blueprint");
    showToast(
      enabled ? "Blueprint grid enabled" : "Blueprint grid disabled",
      enabled ? "Architecture view switched to wireframe emphasis." : "Back to standard operator view."
    );
  }

  function toggleCleanScreen() {
    const enabled = DocsElements.body.classList.toggle("egg-clean-screen");
    showToast(
      enabled ? "Clean screen mode" : "Full signal mode",
      enabled ? "Background circuitry softened." : "Ambient circuitry restored."
    );
  }

  function bindBrandCombo() {
    if (!DocsElements.topbarBrand || !DocsElements.topbarLogo) {
      return;
    }

    DocsElements.topbarBrand.addEventListener("click", (event) => {
      event.preventDefault();
      brandTapCount += 1;
      pulseLogo(DocsElements.topbarLogo);

      if (brandTapTimer) {
        window.clearTimeout(brandTapTimer);
      }

      brandTapTimer = window.setTimeout(() => {
        brandTapCount = 0;
      }, 1900);

      if (brandTapCount >= 7) {
        brandTapCount = 0;
        spawnRibbons(24);
        showToast("Ribbon fall unlocked", "Brand console accepted seven taps.");
      }
    });
  }

  function bindHeroCombo() {
    if (!DocsElements.homeHeroLogo) {
      return;
    }

    DocsElements.homeHeroLogo.addEventListener("click", () => {
      if (heroStarActive) {
        return;
      }

      heroTapCount += 1;
      spinHeroLogo(DocsElements.homeHeroLogo);

      if (heroTapTimer) {
        window.clearTimeout(heroTapTimer);
      }

      heroTapTimer = window.setTimeout(() => {
        heroTapCount = 0;
      }, 2200);

      if (heroTapCount >= 7) {
        heroTapCount = 0;
        heroStarActive = true;
        void launchHeroStar(DocsElements.homeHeroLogo);
      }
    });
  }

  async function launchHeroStar(node) {
    const startRect = node.getBoundingClientRect();
    if (!startRect.width || !startRect.height) {
      heroStarActive = false;
      return;
    }

    const shell = document.createElement("div");
    shell.className = "egg-ninja-star-shell";
    shell.style.width = `${startRect.width}px`;
    shell.style.height = `${startRect.height}px`;
    shell.style.left = `${startRect.left}px`;
    shell.style.top = `${startRect.top}px`;

    const clone = node.cloneNode(true);
    clone.className = "egg-ninja-star egg-ninja-charge";
    shell.appendChild(clone);
    DocsElements.body.appendChild(shell);
    node.classList.add("egg-hero-hidden");

    showToast("Achievement unlocked", "Shardstorm Protocol armed. Ricochet spin charging.");
    spawnRibbons(28);
    await wait(3400);
    clone.classList.remove("egg-ninja-charge");
    showToast("Ricochet burst", "Ember shard released into the lattice.");

    const minSpeed = 560;
    const maxSpeed = 980;
    const angle = (Math.random() * Math.PI * 2) || (Math.PI / 3);
    let velocityX = Math.cos(angle) * (minSpeed + (Math.random() * (maxSpeed - minSpeed)));
    let velocityY = Math.sin(angle) * (minSpeed + (Math.random() * (maxSpeed - minSpeed)));
    let positionX = startRect.left;
    let positionY = startRect.top;
    let spin = 18000;
    let lastFrame = performance.now();
    const travelUntil = lastFrame + 4100;

    await new Promise((resolve) => {
      const step = (now) => {
        const delta = Math.min((now - lastFrame) / 1000, 0.032);
        lastFrame = now;

        positionX += velocityX * delta;
        positionY += velocityY * delta;
        spin += delta * 1680;

        const maxX = window.innerWidth - startRect.width;
        const maxY = window.innerHeight - startRect.height;
        let bounced = false;

        if (positionX <= 0 || positionX >= maxX) {
          positionX = Math.min(Math.max(positionX, 0), maxX);
          velocityX *= -1;
          velocityY += ((Math.random() * 180) - 90);
          bounced = true;
        }

        if (positionY <= 0 || positionY >= maxY) {
          positionY = Math.min(Math.max(positionY, 0), maxY);
          velocityY *= -1;
          velocityX += ((Math.random() * 180) - 90);
          bounced = true;
        }

        if (bounced) {
          const speedScale = 0.96 + (Math.random() * 0.12);
          velocityX *= speedScale;
          velocityY *= speedScale;
        }

        shell.style.left = `${positionX}px`;
        shell.style.top = `${positionY}px`;
        clone.style.transform = `rotate(${spin}deg) scale(1.03)`;

        if (now < travelUntil) {
          window.requestAnimationFrame(step);
          return;
        }

        resolve();
      };

      window.requestAnimationFrame(step);
    });

    const endRect = node.getBoundingClientRect();
    const returnAnimation = shell.animate(
      [
        { left: `${positionX}px`, top: `${positionY}px` },
        { left: `${endRect.left}px`, top: `${endRect.top}px` }
      ],
      { duration: 820, easing: "cubic-bezier(0.22, 1, 0.36, 1)", fill: "forwards" }
    );
    const returnSpin = clone.animate(
      [
        { transform: `rotate(${spin}deg) scale(1.03)` },
        { transform: `rotate(${spin + 1440}deg) scale(1)` }
      ],
      { duration: 820, easing: "cubic-bezier(0.22, 1, 0.36, 1)", fill: "forwards" }
    );

    try {
      await Promise.all([returnAnimation.finished, returnSpin.finished]);
    } catch (error) {
      // Ignore interrupted animation and continue restoring the original node.
    }

    shell.remove();
    node.classList.remove("egg-hero-hidden");
    pulseLogo(node);
    showToast("Shardstorm complete", "Ricochet pattern collapsed back into the operator mark.");
    heroStarActive = false;
  }

  function bindLongPress(node, delay, callback) {
    if (!node) {
      return;
    }

    let timer = null;
    const start = (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) {
        return;
      }
      if (timer) {
        window.clearTimeout(timer);
      }
      timer = window.setTimeout(() => {
        timer = null;
        callback();
      }, delay);
    };
    const stop = () => {
      if (timer) {
        window.clearTimeout(timer);
        timer = null;
      }
    };

    node.addEventListener("pointerdown", start);
    node.addEventListener("pointerup", stop);
    node.addEventListener("pointercancel", stop);
    node.addEventListener("pointerleave", stop);
    node.addEventListener("dragstart", stop);
  }

  function bindVersionLongPress() {
    bindLongPress(DocsElements.topbarVersion, 720, toggleBlueprintMode);
  }

  function bindMenuLongPress() {
    bindLongPress(DocsElements.menuToggle, 780, toggleCleanScreen);
  }

  function bindSearchSecrets() {
    if (!DocsElements.searchInput) {
      return;
    }

    DocsElements.searchInput.addEventListener("input", () => {
      const query = DocsElements.searchInput.value.trim().toLowerCase().replace(/\s+/g, "");
      const fn = secretQueries[query];
      if (fn) {
        fn();
      }
    });
  }

  function init() {
    bindBrandCombo();
    bindHeroCombo();
    bindVersionLongPress();
    bindMenuLongPress();
    bindSearchSecrets();
  }

  return { init };
})();
