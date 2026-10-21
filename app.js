const demoItems = [
  { id: "m-001", imageUrl: "https://picsum.photos/seed/module-001/900/1120", largeImageUrl: "https://picsum.photos/seed/module-001/1600/2000", tags: ["标签栏", "二级 Tab"], curated: true, recent: true },
  { id: "m-002", imageUrl: "https://picsum.photos/seed/module-002/900/700", largeImageUrl: "https://picsum.photos/seed/module-002/1600/1200", tags: ["导航栏"], curated: true, recent: true },
  { id: "m-003", imageUrl: "https://picsum.photos/seed/module-003/900/1260", largeImageUrl: "https://picsum.photos/seed/module-003/1600/2240", tags: ["弹窗", "表单"], curated: true, recent: false },
  { id: "m-004", imageUrl: "https://picsum.photos/seed/module-004/900/860", largeImageUrl: "https://picsum.photos/seed/module-004/1600/1528", tags: ["卡片", "列表"], curated: false, recent: true },
  { id: "m-005", imageUrl: "https://picsum.photos/seed/module-005/900/1180", largeImageUrl: "https://picsum.photos/seed/module-005/1600/2100", tags: ["搜索", "筛选器"], curated: true, recent: true },
  { id: "m-006", imageUrl: "https://picsum.photos/seed/module-006/900/670", largeImageUrl: "https://picsum.photos/seed/module-006/1600/1191", tags: ["数据看板", "卡片"], curated: false, recent: true },
  { id: "m-007", imageUrl: "https://picsum.photos/seed/module-007/900/1340", largeImageUrl: "https://picsum.photos/seed/module-007/1600/2382", tags: ["状态页", "空状态"], curated: true, recent: false },
  { id: "m-008", imageUrl: "https://picsum.photos/seed/module-008/900/920", largeImageUrl: "https://picsum.photos/seed/module-008/1600/1636", tags: ["表单", "下拉菜单"], curated: false, recent: true },
  { id: "m-009", imageUrl: "https://picsum.photos/seed/module-009/900/1080", largeImageUrl: "https://picsum.photos/seed/module-009/1600/1920", tags: ["二级 Tab", "标签栏"], curated: true, recent: true },
  { id: "m-010", imageUrl: "https://picsum.photos/seed/module-010/900/760", largeImageUrl: "https://picsum.photos/seed/module-010/1600/1351", tags: ["Toast", "状态页"], curated: false, recent: false },
  { id: "m-011", imageUrl: "https://picsum.photos/seed/module-011/900/1160", largeImageUrl: "https://picsum.photos/seed/module-011/1600/2062", tags: ["侧边栏", "导航栏"], curated: true, recent: true },
  { id: "m-012", imageUrl: "https://picsum.photos/seed/module-012/900/690", largeImageUrl: "https://picsum.photos/seed/module-012/1600/1227", tags: ["加载状态", "列表"], curated: false, recent: true },
  { id: "m-013", imageUrl: "https://picsum.photos/seed/module-013/900/1240", largeImageUrl: "https://picsum.photos/seed/module-013/1600/2204", tags: ["弹窗", "抽屉"], curated: true, recent: true },
  { id: "m-014", imageUrl: "https://picsum.photos/seed/module-014/900/820", largeImageUrl: "https://picsum.photos/seed/module-014/1600/1458", tags: ["卡片", "数据看板"], curated: false, recent: false },
  { id: "m-015", imageUrl: "https://picsum.photos/seed/module-015/900/1020", largeImageUrl: "https://picsum.photos/seed/module-015/1600/1813", tags: ["搜索", "表单"], curated: true, recent: true },
  { id: "m-016", imageUrl: "https://picsum.photos/seed/module-016/900/1380", largeImageUrl: "https://picsum.photos/seed/module-016/1600/2453", tags: ["导航栏", "二级 Tab"], curated: false, recent: true },
  { id: "m-017", imageUrl: "https://picsum.photos/seed/module-017/900/740", largeImageUrl: "https://picsum.photos/seed/module-017/1600/1315", tags: ["标签栏", "筛选器"], curated: true, recent: false },
  { id: "m-018", imageUrl: "https://picsum.photos/seed/module-018/900/1140", largeImageUrl: "https://picsum.photos/seed/module-018/1600/2026", tags: ["个人中心", "列表"], curated: false, recent: true }
];

const state = { items: [], filter: "全部", search: "", activePreviewId: null };
const moduleChips = ["导航栏", "侧边栏", "标签栏", "二级 Tab", "弹窗", "抽屉", "卡片", "列表", "表单", "搜索", "筛选器", "下拉菜单", "Toast", "空状态", "加载状态", "数据看板", "登录注册", "个人中心"];
const MANUAL_TAGS_KEY = "module-inspiration:manual-tags";

const $ = (selector) => document.querySelector(selector);
const gallery = $("#gallery");
const emptyState = $("#emptyState");

function formatDate() {
  return new Intl.DateTimeFormat("zh-CN", { month: "2-digit", day: "2-digit" }).format(new Date()).replace("/", ".");
}

function matches(item) {
  const query = state.search.trim().toLowerCase();
  const filterMatch = state.filter === "全部"
    || (state.filter === "未分类" && item.status === "pending_review")
    || (state.filter === "今日精选" && item.curated)
    || (state.filter === "最近收录" && item.recent)
    || item.tags.some((tag) => tag.includes(state.filter));
  const searchMatch = !query || item.tags.some((tag) => tag.toLowerCase().includes(query));
  return filterMatch && searchMatch;
}

function renderChips() {
  $("#chipList").innerHTML = moduleChips.map((chip) => `<button class="chip ${state.filter === chip ? "active" : ""}" type="button" data-chip="${chip}">${chip}</button>`).join("");
  document.querySelectorAll("[data-chip]").forEach((button) => button.addEventListener("click", () => setFilter(button.dataset.chip)));
}

function readManualTags() {
  try {
    const parsed = JSON.parse(localStorage.getItem(MANUAL_TAGS_KEY) || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function applyManualTags(items) {
  const overrides = readManualTags();
  return items.map((item) => {
    const tags = Array.isArray(overrides[item.id]) ? overrides[item.id].filter((tag) => moduleChips.includes(tag)) : item.tags;
    return tags !== item.tags ? { ...item, tags, status: tags.length ? "published" : "pending_review" } : item;
  });
}

function renderManualTagPicker(item) {
  const picker = $("#manualTagList");
  if (!picker) return;
  picker.innerHTML = moduleChips.map((tag) => `
    <button class="manual-tag ${item.tags.includes(tag) ? "selected" : ""}" type="button" data-manual-tag="${tag}">${tag}</button>
  `).join("");
}

function renderGallery() {
  const visible = state.items.filter(matches);
  gallery.innerHTML = visible.map((item, index) => `
    <article class="tile" tabindex="0" data-item-id="${item.id}">
      <img src="${item.imageUrl}" alt="${item.tags.length ? item.tags.join("、") : "未分类"} 模块灵感" loading="lazy" />
      <span class="tile-index">${String(index + 1).padStart(2, "0")}</span>
      <div class="tile-overlay">
        <div class="tile-tags">${item.tags.length ? item.tags.map((tag) => `<span class="tile-tag">${tag}</span>`).join("") : '<span class="tile-tag pending-tag">未分类</span>'}</div>
        <button class="original-link" type="button" data-preview="${item.id}">查看大图 ↗</button>
      </div>
    </article>
  `).join("");
  $("#resultCount").textContent = visible.length;
  emptyState.hidden = visible.length !== 0;
  gallery.hidden = visible.length === 0;
  document.querySelectorAll("[data-preview]").forEach((button) => button.addEventListener("click", (event) => { event.stopPropagation(); openPreview(button.dataset.preview); }));
  document.querySelectorAll(".tile").forEach((tile) => tile.addEventListener("click", () => openPreview(tile.dataset.itemId)));
}

function renderNavigation() {
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === state.filter);
  });
  $("#currentFilter").textContent = state.filter === "全部" ? "全部模块" : state.filter;
}

function setFilter(filter) {
  state.filter = filter;
  renderNavigation();
  renderChips();
  renderGallery();
}

function bindEvents() {
  document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {
    setFilter(button.dataset.filter);
    closeSidebar();
  }));
  $("#searchInput").addEventListener("input", (event) => { state.search = event.target.value; renderGallery(); });
  $("#clearFilter").addEventListener("click", () => { state.filter = "全部"; state.search = ""; $("#searchInput").value = ""; renderNavigation(); renderChips(); renderGallery(); });
  $("#refreshButton").addEventListener("click", (event) => { event.currentTarget.classList.add("is-refreshing"); setTimeout(() => event.currentTarget.classList.remove("is-refreshing"), 600); renderGallery(); });
  $("#openSidebar").addEventListener("click", openSidebar);
  $("#closeSidebar").addEventListener("click", closeSidebar);
  $("#scrim").addEventListener("click", closeSidebar);
  $("#previewClose").addEventListener("click", closePreview);
  $("#previewBackdrop").addEventListener("click", closePreview);
  $("#manualTagList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-manual-tag]");
    if (button) button.classList.toggle("selected");
  });
  $("#manualSaveTags").addEventListener("click", saveManualTags);
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); $("#searchInput").focus(); }
    if (event.key === "Escape") { closeSidebar(); closePreview(); }
  });
}

function openSidebar() { $("#sidebar").classList.add("open"); $("#scrim").classList.add("visible"); }
function closeSidebar() { $("#sidebar").classList.remove("open"); $("#scrim").classList.remove("visible"); }

function openPreview(itemId) {
  const item = state.items.find((entry) => entry.id === itemId);
  if (!item) return;
  state.activePreviewId = itemId;
  $("#previewImage").src = item.largeImageUrl || item.imageUrl;
  $("#previewImage").alt = `${item.tags.length ? item.tags.join("、") : "未分类"} 模块大图`;
  $("#previewTags").innerHTML = item.tags.length
    ? item.tags.map((tag) => `<span class="tile-tag">${tag}</span>`).join("")
    : '<span class="tile-tag pending-tag">未分类</span>';
  renderManualTagPicker(item);
  $("#manualHint").textContent = item.tags.length ? "已选择标签，可继续调整。保存后仅保存在当前浏览器。" : "请选择模块标签，保存后仅保存在当前浏览器。";
  $("#previewModal").hidden = false;
  document.body.classList.add("modal-open");
  $("#previewClose").focus();
}

function saveManualTags() {
  const item = state.items.find((entry) => entry.id === state.activePreviewId);
  if (!item) return;
  const tags = [...document.querySelectorAll("[data-manual-tag].selected")].map((button) => button.dataset.manualTag);
  item.tags = tags;
  item.status = tags.length ? "published" : "pending_review";
  const overrides = readManualTags();
  overrides[item.id] = tags;
  try {
    localStorage.setItem(MANUAL_TAGS_KEY, JSON.stringify(overrides));
  } catch {
    $("#manualHint").textContent = "浏览器未允许保存，请检查隐私设置。";
    return;
  }
  $("#manualHint").textContent = "已保存到当前浏览器。";
  openPreview(item.id);
  renderGallery();
}

function closePreview() {
  $("#previewModal").hidden = true;
  document.body.classList.remove("modal-open");
  $("#previewImage").src = "";
}

async function loadItems() {
  try {
    const response = await fetch("./data/items.json", { cache: "no-store" });
    if (!response.ok) throw new Error("items.json unavailable");
    // The old m-* records are UI placeholders, not collected assets.
    state.items = applyManualTags((await response.json()).filter((item) => !String(item.id).startsWith("m-")));
  } catch {
    state.items = [];
  }
  $("#allCount").textContent = state.items.length;
  $("#todayLabel").textContent = formatDate();
  renderChips();
  renderGallery();
  bindEvents();
}

loadItems();
