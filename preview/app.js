/* LauncherRE independent browser preview interactions. No native launcher bridge. */
(() => {
  const pages = [...document.querySelectorAll("[data-page-content]")];
  const nav = [...document.querySelectorAll(".sidebar [data-page]")];
  const tabs = [...document.querySelectorAll("[data-tab]")];
  const panels = [...document.querySelectorAll("[data-panel]")];
  const toast = document.querySelector("#toast");
  let toastTimer = null;

  function message(text) {
    if (!toast) return;
    toast.textContent = text;
    toast.classList.remove("hidden");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.add("hidden"), 4800);
  }

  function openPage(page) {
    if (!pages.some(node => node.dataset.pageContent === page)) return;
    pages.forEach(el => el.classList.toggle("hidden", el.dataset.pageContent !== page));
    nav.forEach(el => {
      const active = el.dataset.page === page;
      el.classList.toggle("active", active);
      if (active) el.setAttribute("aria-current", "page");
      else el.removeAttribute("aria-current");
    });
    if (page === "java") openTab("play");
    document.querySelector("#main").scrollTop = 0;
    try { history.replaceState(null, "", "#" + page); } catch (_) {}
  }

  function openTab(tab) {
    tabs.forEach(el => {
      const selected = el.dataset.tab === tab;
      el.classList.toggle("is-active", selected);
      el.setAttribute("aria-selected", String(selected));
    });
    panels.forEach(el => el.classList.toggle("hidden", el.dataset.panel !== tab));
    document.querySelector("#main").scrollTop = 0;
  }

  document.querySelectorAll("[data-page]").forEach(button => {
    button.addEventListener("click", () => openPage(button.dataset.page));
  });
  tabs.forEach(button => button.addEventListener("click", () => openTab(button.dataset.tab)));
  document.querySelectorAll("[data-tab-target]").forEach(button => {
    button.addEventListener("click", () => openTab(button.dataset.tabTarget));
  });

  const actions = [
    ["play-button", "This is a launcher UI preview. Starting Minecraft requires a native bridge or compatible game runtime."],
    ["quickplay-info", "Quick Play works with local game saves in the official desktop launcher. This is a UI-only preview."],
    ["new-installation", "Installation editing is a frontend prototype. Native Java runtime management is not connected."],
    ["installation-play", "Game launching is not connected to this browser preview."],
    ["add-skin", "Microsoft account and skin upload integration are not connected yet."]
  ];
  for (const [id, text] of actions) {
    document.getElementById(id)?.addEventListener("click", () => message(text));
  }
  document.querySelectorAll(".preview-action").forEach(button => {
    button.addEventListener("click", () => message("Native game launch and installation are not implemented in this web preview."));
  });
  document.getElementById("compact-sidebar")?.addEventListener("change", event => {
    document.body.classList.toggle("compact", event.target.checked);
  });
  document.getElementById("reduce-motion")?.addEventListener("change", event => {
    document.body.classList.toggle("reduce-motion", event.target.checked);
  });

  const initial = decodeURIComponent(location.hash.slice(1) || "java");
  openPage(pages.some(el => el.dataset.pageContent === initial) ? initial : "java");
})();
