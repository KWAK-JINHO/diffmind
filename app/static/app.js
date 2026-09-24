// app/static/app.js - Modern macOS Glassmorphism & Gemini Notebook Architecture

document.addEventListener("DOMContentLoaded", () => {
  // Single Repository Workspace
  const currentProject = "default";

  // Layout Container & Panel Toggles
  const notebookContainer = document.querySelector(".notebook-container");
  const sourcesPanel = document.getElementById("sources-panel");
  const studioPanel = document.getElementById("studio-panel");
  const btnToggleSources = document.getElementById("btn-toggle-sources");
  const btnToggleStudio = document.getElementById("btn-toggle-studio");
  const btnToggleSourcesHeader = document.getElementById("btn-toggle-sources-header");
  const btnToggleStudioHeader = document.getElementById("btn-toggle-studio-header");

  // Top Navigation Buttons
  const btnOpenImport = document.getElementById("btn-open-import");
  const btnRecentDiff = document.getElementById("btn-recent-diff");

  // Left Panel: Sources Elements
  const btnAddSources = document.getElementById("btn-add-sources");
  const sourcesSearchInput = document.getElementById("sources-search-input");
  const sourcesEmptyState = document.getElementById("sources-empty-state");
  const sourcesTreeList = document.getElementById("sources-tree-list");
  const linkAddSourcesAction = document.getElementById("link-add-sources-action");
  const statsFileCount = document.getElementById("stats-file-count");
  const statsHeadingCount = document.getElementById("stats-heading-count");
  const btnRefreshSources = document.getElementById("btn-refresh-sources");

  // Center Panel: Blank Canvas vs Reader Elements
  const canvasBlankState = document.getElementById("canvas-blank-state");
  const canvasReaderState = document.getElementById("canvas-reader-state");
  const btnBackCanvas = document.getElementById("btn-back-canvas");
  const bcFileName = document.getElementById("bc-file-name");
  const btnReaderToggleMode = document.getElementById("btn-reader-toggle-mode");
  const btnReaderCopy = document.getElementById("btn-reader-copy");
  const outlineDropdown = document.getElementById("outline-dropdown");
  const btnToggleOutline = document.getElementById("btn-toggle-outline");
  const outlineMenu = document.getElementById("outline-menu");
  const readerDocPath = document.getElementById("reader-doc-path");
  const readerDocSize = document.getElementById("reader-doc-size");
  const readerDocHeadingsCount = document.getElementById("reader-doc-headings-count");
  const readerMarkdownRender = document.getElementById("reader-markdown-render");
  const readerRawBox = document.getElementById("reader-raw-box");
  const readerRawCode = document.getElementById("reader-raw-code");

  // Canvas Floating Bottom Bar & Chips
  const canvasQueryInput = document.getElementById("canvas-query-input");
  const btnQuerySubmit = document.getElementById("btn-query-submit");
  const canvasSourcesCounter = document.getElementById("canvas-sources-counter");
  const chipLearnTopic = document.getElementById("chip-learn-topic");
  const chipCreateNew = document.getElementById("chip-create-new");
  const chipMakeProgress = document.getElementById("chip-make-progress");

  // Right Panel: Studio Elements
  const studioBanner = document.getElementById("studio-banner");
  const btnCloseBanner = document.getElementById("btn-close-banner");
  const btnStudioAddNote = document.getElementById("btn-studio-add-note");
  const btnStudioOpenDiff = document.getElementById("btn-studio-open-diff");
  const studioToolPills = document.querySelectorAll(".studio-tool-pill");

  // Modals
  const addSourcesModal = document.getElementById("add-sources-modal");
  const btnCloseSourcesModal = document.getElementById("btn-close-sources-modal");
  const btnCloseSourcesDot = document.getElementById("btn-close-sources-dot");
  const recentDiffModal = document.getElementById("recent-diff-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnCloseDiffDot = document.getElementById("btn-close-diff-dot");
  const modalDiffContent = document.getElementById("modal-diff-content");

  // Knowledge Input & Proposal Section
  const tabBtns = document.querySelectorAll(".tab-btn[data-tab]");
  const tabContents = document.querySelectorAll(".tab-content");
  const inputText = document.getElementById("input-text");
  const fileDropzone = document.getElementById("file-dropzone");
  const fileInput = document.getElementById("file-input");
  const filePreviewName = document.getElementById("file-preview-name");
  const imageDropzone = document.getElementById("image-dropzone");
  const imageInput = document.getElementById("image-input");
  const imagePreviewBox = document.getElementById("image-preview-box");
  const imagePreview = document.getElementById("image-preview");
  const btnPropose = document.getElementById("btn-propose");
  const proposalSection = document.getElementById("proposal-section");
  const metaTargetPath = document.getElementById("meta-target-path");
  const metaFileBadge = document.getElementById("meta-file-badge");
  const metaTargetHeading = document.getElementById("meta-target-heading");
  const metaReason = document.getElementById("meta-reason");
  const diffFileHeader = document.getElementById("diff-file-header");
  const diffContent = document.getElementById("diff-content");
  const inputCommitMsg = document.getElementById("input-commit-msg");
  const btnAccept = document.getElementById("btn-accept");

  // Import Modal Elements
  const importModal = document.getElementById("import-modal");
  const btnCloseImportModal = document.getElementById("btn-close-import-modal");
  const btnCloseImportDot = document.getElementById("btn-close-import-dot");
  const btnCancelImport = document.getElementById("btn-cancel-import");
  const btnSubmitImport = document.getElementById("btn-submit-import");
  const importTabBtns = document.querySelectorAll("[data-import-tab]");
  const importTabGithub = document.getElementById("import-tab-github");
  const importTabLocal = document.getElementById("import-tab-local");
  const inputGithubUrl = document.getElementById("input-github-url");
  const inputGithubBranch = document.getElementById("input-github-branch");
  const inputLocalPath = document.getElementById("input-local-path");
  const btnOpenDirBrowser = document.getElementById("btn-open-dir-browser");
  const browserFolderPicker = document.getElementById("browser-folder-picker");
  const btnPickFolderFinder = document.getElementById("btn-pick-folder-finder");
  const finderFolderLabel = document.getElementById("finder-folder-label");

  // Directory Browser Modal Elements
  const dirBrowserModal = document.getElementById("dir-browser-modal");
  const btnCloseDirBrowser = document.getElementById("btn-close-dir-browser");
  const btnCloseDirDot = document.getElementById("btn-close-dir-dot");
  const dirBrowserCurrentPath = document.getElementById("dir-browser-current-path");
  const btnDirGoUp = document.getElementById("btn-dir-go-up");
  const btnSelectCurrentDir = document.getElementById("btn-select-current-dir");
  const dirBrowserList = document.getElementById("dir-browser-list");

  // State
  let currentTab = "text";
  let currentImportTab = "github";
  let selectedFile = null;
  let selectedImage = null;
  let activeProposal = null;
  let activeBrowserDir = "";
  let parentBrowserDir = null;
  let browserSelectedFolderFiles = null;

  let currentLoadedFile = null;
  let rawModeActive = false;
  let currentTOC = {};
  let expandedFolders = new Set();

  // ==========================================================================
  // 1. Panel Collapse & Expand Handlers
  // ==========================================================================
  if (btnToggleSources) {
    btnToggleSources.addEventListener("click", () => {
      notebookContainer.classList.toggle("sources-collapsed");
    });
  }

  if (btnToggleSourcesHeader) {
    btnToggleSourcesHeader.addEventListener("click", () => {
      notebookContainer.classList.toggle("sources-collapsed");
    });
  }

  if (btnToggleStudio) {
    btnToggleStudio.addEventListener("click", () => {
      notebookContainer.classList.toggle("studio-collapsed");
    });
  }

  if (btnToggleStudioHeader) {
    btnToggleStudioHeader.addEventListener("click", () => {
      notebookContainer.classList.toggle("studio-collapsed");
    });
  }

  if (btnCloseBanner) {
    btnCloseBanner.addEventListener("click", () => {
      studioBanner.style.display = "none";
    });
  }

  // ==========================================================================
  // 2. Modals: Add Sources, Recent Diff, Import
  // ==========================================================================
  function openAddSourcesModal(prefillTopic = "") {
    if (prefillTopic) {
      inputText.value = prefillTopic;
    }
    addSourcesModal.style.display = "flex";
    inputText.focus();
  }

  function closeAddSourcesModal() {
    addSourcesModal.style.display = "none";
  }

  if (btnAddSources) btnAddSources.addEventListener("click", () => openAddSourcesModal());
  if (linkAddSourcesAction) linkAddSourcesAction.addEventListener("click", (e) => { e.preventDefault(); openAddSourcesModal(); });
  if (btnCloseSourcesModal) btnCloseSourcesModal.addEventListener("click", closeAddSourcesModal);
  if (btnCloseSourcesDot) btnCloseSourcesDot.addEventListener("click", closeAddSourcesModal);

  if (addSourcesModal) {
    addSourcesModal.addEventListener("click", (e) => {
      if (e.target === addSourcesModal) closeAddSourcesModal();
    });
  }

  // Recent Diff Modal
  if (btnRecentDiff) {
    btnRecentDiff.addEventListener("click", async () => {
      try {
        const res = await fetch(`/api/v1/recent-diff?project=${encodeURIComponent(currentProject)}`);
        if (!res.ok) throw new Error("최근 diff 정보를 불러오지 못했습니다.");
        const data = await res.json();
        renderDiff(modalDiffContent, data.diff);
        if (recentDiffModal) recentDiffModal.style.display = "flex";
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  }

  if (btnCloseModal && recentDiffModal) btnCloseModal.addEventListener("click", () => { recentDiffModal.style.display = "none"; });
  if (btnCloseDiffDot && recentDiffModal) btnCloseDiffDot.addEventListener("click", () => { recentDiffModal.style.display = "none"; });
  if (recentDiffModal) {
    recentDiffModal.addEventListener("click", (e) => {
      if (e.target === recentDiffModal) recentDiffModal.style.display = "none";
    });
  }

  // Import Modal
  if (btnOpenImport) {
    btnOpenImport.addEventListener("click", () => {
      if (inputGithubUrl) inputGithubUrl.value = "";
      if (inputGithubBranch) inputGithubBranch.value = "";
      if (inputLocalPath) inputLocalPath.value = "";
      if (importModal) importModal.style.display = "flex";
    });
  }

  function closeImportModal() {
    if (importModal) importModal.style.display = "none";
  }

  if (btnCloseImportModal) btnCloseImportModal.addEventListener("click", closeImportModal);
  if (btnCloseImportDot) btnCloseImportDot.addEventListener("click", closeImportModal);
  if (btnCancelImport) btnCancelImport.addEventListener("click", closeImportModal);
  if (importModal) {
    importModal.addEventListener("click", (e) => {
      if (e.target === importModal) closeImportModal();
    });
  }

  // ==========================================================================
  // 3. Knowledge Base File Tree & Hierarchy Construction
  // ==========================================================================
  function buildFileTree(toc) {
    const root = { name: "", type: "dir", path: "", children: {} };

    Object.keys(toc).forEach((filePath) => {
      const parts = filePath.split("/");
      let curr = root;

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        const isFile = i === parts.length - 1;
        const subPath = parts.slice(0, i + 1).join("/");

        if (isFile) {
          curr.children[part] = {
            name: part,
            path: filePath,
            type: "file",
            headings: toc[filePath] || [],
          };
        } else {
          if (!curr.children[part]) {
            curr.children[part] = {
              name: part,
              path: subPath,
              type: "dir",
              children: {},
            };
          }
          curr = curr.children[part];
        }
      }
    });

    return root;
  }

  function countFilesInDir(dirNode) {
    let count = 0;
    Object.values(dirNode.children).forEach((child) => {
      if (child.type === "file") count += 1;
      else if (child.type === "dir") count += countFilesInDir(child);
    });
    return count;
  }

  async function loadTOC() {
    try {
      const res = await fetch(`/api/v1/toc?project=${encodeURIComponent(currentProject)}`);
      if (!res.ok) throw new Error("목차 정보를 가져오지 못했습니다.");
      const data = await res.json();
      currentTOC = data.toc || {};
      renderFileTree();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderFileTree() {
    sourcesTreeList.innerHTML = "";
    const filterQuery = sourcesSearchInput ? sourcesSearchInput.value.trim().toLowerCase() : "";
    const tree = buildFileTree(currentTOC);

    const totalFiles = Object.keys(currentTOC).length;
    const totalHeadings = Object.values(currentTOC).reduce((acc, h) => acc + h.length, 0);

    if (statsFileCount) statsFileCount.textContent = `${totalFiles} sources`;
    if (statsHeadingCount) statsHeadingCount.textContent = `${totalHeadings} sections`;
    if (canvasSourcesCounter) canvasSourcesCounter.textContent = `${totalFiles} sources`;

    if (totalFiles === 0) {
      sourcesEmptyState.style.display = "flex";
      sourcesTreeList.style.display = "none";
      return;
    }

    sourcesEmptyState.style.display = "none";
    sourcesTreeList.style.display = "block";

    const fragment = document.createDocumentFragment();
    renderTreeChildren(tree, fragment, filterQuery);

    if (fragment.children.length === 0 && filterQuery) {
      sourcesTreeList.innerHTML = `
        <div style="padding:1.5rem 1rem; color:var(--text-muted); font-size:0.8rem; text-align:center;">
          '${filterQuery}'에 일치하는 지식 소스가 없습니다.
        </div>`;
      return;
    }

    sourcesTreeList.appendChild(fragment);
  }

  function renderTreeChildren(dirNode, container, filterQuery) {
    const keys = Object.keys(dirNode.children).sort((a, b) => {
      const nodeA = dirNode.children[a];
      const nodeB = dirNode.children[b];
      if (nodeA.type !== nodeB.type) {
        return nodeA.type === "dir" ? -1 : 1;
      }
      return a.localeCompare(b);
    });

    keys.forEach((key) => {
      const node = dirNode.children[key];

      if (node.type === "dir") {
        const fileCount = countFilesInDir(node);
        const isExpanded = filterQuery ? true : expandedFolders.has(node.path);

        const nodeWrapper = document.createElement("div");
        nodeWrapper.className = "tree-node";

        const folderRow = document.createElement("div");
        folderRow.className = "tree-folder-row";
        folderRow.innerHTML = `
          <div class="tree-folder-left">
            <span class="tree-caret ${isExpanded ? 'expanded' : ''}">▶</span>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            <span>${node.name}</span>
          </div>
          <span class="tree-folder-count">${fileCount}</span>
        `;

        const childrenContainer = document.createElement("div");
        childrenContainer.className = "tree-folder-children";
        childrenContainer.style.display = isExpanded ? "block" : "none";

        folderRow.addEventListener("click", () => {
          if (expandedFolders.has(node.path)) {
            expandedFolders.delete(node.path);
            childrenContainer.style.display = "none";
            folderRow.querySelector(".tree-caret").classList.remove("expanded");
          } else {
            expandedFolders.add(node.path);
            childrenContainer.style.display = "block";
            folderRow.querySelector(".tree-caret").classList.add("expanded");
          }
        });

        renderTreeChildren(node, childrenContainer, filterQuery);

        if (filterQuery && childrenContainer.children.length === 0) {
          return;
        }

        nodeWrapper.appendChild(folderRow);
        nodeWrapper.appendChild(childrenContainer);
        container.appendChild(nodeWrapper);

      } else if (node.type === "file") {
        const matchesName = node.path.toLowerCase().includes(filterQuery);
        const matchesHeading = node.headings.some((h) => h.toLowerCase().includes(filterQuery));
        if (filterQuery && !matchesName && !matchesHeading) {
          return;
        }

        const fileWrapper = document.createElement("div");
        fileWrapper.className = "tree-node";

        const isCurrent = currentLoadedFile && currentLoadedFile.path === node.path;
        const fileRow = document.createElement("div");
        fileRow.className = `tree-file-row ${isCurrent ? 'active' : ''}`;
        fileRow.innerHTML = `
          <div class="tree-file-left">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <span>${node.name}</span>
          </div>
          <span class="tree-file-badge">${node.headings.length} H</span>
        `;

        fileRow.addEventListener("click", () => {
          openDocument(node.path);
        });

        fileWrapper.appendChild(fileRow);

        if (node.headings.length > 0 && (isCurrent || filterQuery)) {
          const headingsList = document.createElement("ul");
          headingsList.className = "tree-file-headings";
          node.headings.forEach((h) => {
            const li = document.createElement("li");
            const link = document.createElement("a");
            link.className = "tree-heading-link";
            link.textContent = h;
            link.title = h;
            link.addEventListener("click", (e) => {
              e.stopPropagation();
              openDocument(node.path, h);
            });
            li.appendChild(link);
            headingsList.appendChild(li);
          });
          fileWrapper.appendChild(headingsList);
        }

        container.appendChild(fileWrapper);
      }
    });
  }

  // ==========================================================================
  // 4. Center Canvas: Document Study Reader & Blank Canvas Toggle
  // ==========================================================================
  async function openDocument(relPath, targetHeading = null) {
    try {
      const res = await fetch(`/api/v1/files?project=${encodeURIComponent(currentProject)}&path=${encodeURIComponent(relPath)}`);
      if (!res.ok) throw new Error("문서를 불러오지 못했습니다.");
      const data = await res.json();
      currentLoadedFile = data;

      bcFileName.textContent = relPath;
      readerDocPath.textContent = relPath;
      readerDocSize.textContent = formatBytes(data.size_bytes);
      readerDocHeadingsCount.textContent = `${data.headings.length}개 목차(헤딩)`;

      renderMarkdownContent(data.content);
      renderOutlineMenu(data.headings);

      canvasBlankState.style.display = "none";
      canvasReaderState.style.display = "flex";

      renderFileTree();

      if (targetHeading) {
        scrollToHeading(targetHeading);
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  if (btnBackCanvas) {
    btnBackCanvas.addEventListener("click", () => {
      canvasReaderState.style.display = "none";
      canvasBlankState.style.display = "flex";
      currentLoadedFile = null;
      renderFileTree();
    });
  }

  function renderMarkdownContent(content) {
    if (typeof marked !== "undefined" && marked.parse) {
      try {
        marked.setOptions({ gfm: true, breaks: true });
      } catch (e) {}
      readerMarkdownRender.innerHTML = marked.parse(content);
    } else {
      readerMarkdownRender.innerHTML = renderBasicMarkdownFallback(content);
    }

    const headingEls = readerMarkdownRender.querySelectorAll("h1, h2, h3, h4");
    headingEls.forEach((el) => {
      const cleanText = el.textContent.trim();
      const id = "sec-" + cleanText.toLowerCase().replace(/[^a-z0-9_\-\uac00-\ud7a3]+/g, "-").replace(/^-+|-+$/g, "");
      el.id = id;
    });

    readerRawCode.textContent = content;
  }

  function renderOutlineMenu(headings) {
    outlineMenu.innerHTML = "";
    if (!headings || headings.length === 0) {
      outlineMenu.innerHTML = '<div style="padding:0.75rem; color:var(--text-muted); font-size:0.75rem; text-align:center;">헤딩이 없습니다.</div>';
      return;
    }

    headings.forEach((h) => {
      const match = h.match(/^(#{1,3})\s+(.+)$/);
      const level = match ? match[1].length : 1;
      const title = match ? match[2].trim() : h;

      const item = document.createElement("div");
      item.className = `outline-item h${level}`;
      item.textContent = title;
      item.addEventListener("click", () => {
        scrollToHeading(h);
        outlineMenu.style.display = "none";
      });
      outlineMenu.appendChild(item);
    });
  }

  function scrollToHeading(headingText) {
    const cleanText = headingText.replace(/^#+\s*/, "").trim();
    const headings = readerMarkdownRender.querySelectorAll("h1, h2, h3, h4");
    for (const h of headings) {
      if (h.textContent.trim().toLowerCase() === cleanText.toLowerCase()) {
        h.scrollIntoView({ behavior: "smooth", block: "start" });
        h.style.transition = "background 0.3s ease";
        const origBg = h.style.background;
        h.style.background = "rgba(56, 189, 248, 0.25)";
        setTimeout(() => { h.style.background = origBg; }, 1500);
        break;
      }
    }
  }

  function renderBasicMarkdownFallback(text) {
    if (!text) return "";
    let escaped = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    escaped = escaped.replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>");
    escaped = escaped.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    escaped = escaped.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    escaped = escaped.replace(/^# (.*$)/gim, "<h1>$1</h1>");
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    escaped = escaped.replace(/\*(.*?)\*/g, "<em>$1</em>");
    escaped = escaped.replace(/^\> (.*$)/gim, "<blockquote>$1</blockquote>");
    escaped = escaped.replace(/\n\n/g, "</p><p>");
    return `<p>${escaped}</p>`;
  }

  // Reader Actions
  if (btnReaderToggleMode) {
    btnReaderToggleMode.addEventListener("click", () => {
      rawModeActive = !rawModeActive;
      if (rawModeActive) {
        readerMarkdownRender.style.display = "none";
        readerRawBox.style.display = "block";
        btnReaderToggleMode.textContent = "📖 Rendered";
      } else {
        readerMarkdownRender.style.display = "block";
        readerRawBox.style.display = "none";
        btnReaderToggleMode.textContent = "👁 Raw";
      }
    });
  }

  if (btnReaderCopy) {
    btnReaderCopy.addEventListener("click", async () => {
      if (currentLoadedFile && currentLoadedFile.content) {
        try {
          await navigator.clipboard.writeText(currentLoadedFile.content);
          showToast("마크다운 원문이 클립보드에 복사되었습니다.", "success");
        } catch (err) {
          showToast("복사에 실패했습니다.", "error");
        }
      }
    });
  }

  if (btnToggleOutline) {
    btnToggleOutline.addEventListener("click", (e) => {
      e.stopPropagation();
      const isVisible = outlineMenu.style.display === "block";
      outlineMenu.style.display = isVisible ? "none" : "block";
    });
  }

  document.addEventListener("click", (e) => {
    if (outlineDropdown && !outlineDropdown.contains(e.target)) {
      outlineMenu.style.display = "none";
    }
  });

  // Search filter
  if (sourcesSearchInput) {
    sourcesSearchInput.addEventListener("input", () => {
      renderFileTree();
    });
  }

  if (btnRefreshSources) {
    btnRefreshSources.addEventListener("click", () => {
      loadTOC();
      showToast("지식 소스를 새로고침했습니다.", "success");
    });
  }



  // ==========================================================================
  // 5. Ingestion Tabs & File/Image Dropzone
  // ==========================================================================
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      currentTab = btn.dataset.tab;
      document.getElementById(`tab-${currentTab}`).classList.add("active");
    });
  });

  function setupDropzone(dropzone, inputElement, onFileSelected) {
    dropzone.addEventListener("click", () => inputElement.click());
    inputElement.addEventListener("click", (e) => e.stopPropagation());

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        onFileSelected(e.dataTransfer.files[0]);
      }
    });

    inputElement.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        onFileSelected(e.target.files[0]);
      }
    });
  }

  setupDropzone(fileDropzone, fileInput, (file) => {
    selectedFile = file;
    filePreviewName.innerHTML = `
      <span style="color:var(--success); font-weight:600;">✓ ${file.name}</span>
      <span style="color:var(--text-muted);">(${formatBytes(file.size)})</span>
    `;
  });

  setupDropzone(imageDropzone, imageInput, (file) => {
    selectedImage = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imagePreviewBox.style.display = "block";
    };
    reader.readAsDataURL(file);
  });

  // ==========================================================================
  // 6. AI Diff Proposal & Git Accept Pipeline
  // ==========================================================================
  btnPropose.addEventListener("click", async () => {
    const formData = new FormData();
    formData.append("project", currentProject);
    let hasPayload = false;

    if (currentTab === "text") {
      const textVal = inputText.value.trim();
      if (!textVal) {
        showToast("마크다운 텍스트를 입력해 주세요.", "error");
        return;
      }
      formData.append("content", textVal);
      hasPayload = true;
    } else if (currentTab === "file") {
      if (!selectedFile) {
        showToast("업로드할 마크다운 파일을 선택해 주세요.", "error");
        return;
      }
      formData.append("file", selectedFile);
      hasPayload = true;
    } else if (currentTab === "image") {
      if (!selectedImage) {
        showToast("분석할 스크린샷 이미지를 선택해 주세요.", "error");
        return;
      }
      formData.append("image", selectedImage);
      hasPayload = true;
    }

    if (!hasPayload) return;

    setLoading(btnPropose, true, "지식 위치 분석 중...");

    try {
      const res = await fetch("/api/v1/propose", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.message || "제안 생성에 실패했습니다.");
      }

      const proposal = await res.json();
      activeProposal = proposal;
      displayProposal(proposal);
      showToast("새로운 지식 병합 제안이 생성되었습니다.", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btnPropose, false, "지식 위치 분석 및 Diff 제안 생성");
    }
  });

  function displayProposal(proposal) {
    metaTargetPath.textContent = proposal.target_file_path;
    metaTargetHeading.textContent = proposal.target_heading || "(루트 문서 생성)";

    if (proposal.is_new_file) {
      metaFileBadge.textContent = "신규 파일 생성";
      metaFileBadge.className = "badge badge-new";
    } else {
      metaFileBadge.textContent = "기존 파일 업데이트";
      metaFileBadge.className = "badge badge-update";
    }

    metaReason.textContent = proposal.reason;
    diffFileHeader.textContent = `Unified Diff: ${proposal.target_file_path}`;

    renderDiff(diffContent, proposal.unified_diff);

    const action = proposal.is_new_file ? "create" : "update";
    inputCommitMsg.value = `docs: ${action} ${proposal.target_file_path} under '${proposal.target_heading}'`;

    proposalSection.style.display = "block";
    proposalSection.scrollIntoView({ behavior: "smooth" });
  }

  function renderDiff(targetContainer, diffText) {
    targetContainer.innerHTML = "";
    if (!diffText || !diffText.trim()) {
      targetContainer.innerHTML = '<div class="diff-line normal">변경 사항이 없거나 동일합니다.</div>';
      return;
    }

    const lines = diffText.split("\n");
    lines.forEach((line) => {
      const el = document.createElement("div");
      if (line.startsWith("+++") || line.startsWith("---")) {
        el.className = "diff-line normal";
        el.style.fontWeight = "bold";
      } else if (line.startsWith("@@")) {
        el.className = "diff-line hunk";
      } else if (line.startsWith("+")) {
        el.className = "diff-line add";
      } else if (line.startsWith("-")) {
        el.className = "diff-line del";
      } else {
        el.className = "diff-line normal";
      }
      el.textContent = line;
      targetContainer.appendChild(el);
    });
  }

  btnAccept.addEventListener("click", async () => {
    if (!activeProposal) {
      showToast("승인할 활성 제안이 없습니다.", "error");
      return;
    }

    const commitMsg = inputCommitMsg.value.trim() || undefined;
    const targetFile = activeProposal.target_file_path;
    const targetHeading = activeProposal.target_heading;

    setLoading(btnAccept, true, "원자적 패치 & Git 커밋 중...");

    try {
      const res = await fetch(`/api/v1/accept?project=${encodeURIComponent(currentProject)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          proposal: activeProposal,
          commit_message: commitMsg,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.message || "패치 승인 및 커밋에 실패했습니다.");
      }

      const result = await res.json();
      showToast(`✅ Git 커밋 완료 [${result.commit_hash}]: ${result.message}`, "success");

      proposalSection.style.display = "none";
      activeProposal = null;
      inputText.value = "";
      selectedFile = null;
      selectedImage = null;
      filePreviewName.textContent = "";
      imagePreviewBox.style.display = "none";
      imagePreview.src = "";
      closeAddSourcesModal();

      await loadTOC();

      const fileToOpen = result.file_path || targetFile;
      if (fileToOpen) {
        openDocument(fileToOpen, targetHeading);
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btnAccept, false, "변경 사항 승인 및 Git 커밋");
    }
  });

  // ==========================================================================
  // 7. Bulk Knowledge Import & Directory Explorer
  // ==========================================================================
  importTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      importTabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentImportTab = btn.dataset.importTab;
      if (currentImportTab === "github") {
        importTabGithub.style.display = "block";
        importTabLocal.style.display = "none";
      } else {
        importTabGithub.style.display = "none";
        importTabLocal.style.display = "block";
      }
    });
  });

  btnOpenDirBrowser.addEventListener("click", () => {
    dirBrowserModal.style.display = "flex";
    loadDirectory(inputLocalPath.value.trim() || null);
  });

  function closeDirBrowser() {
    dirBrowserModal.style.display = "none";
  }

  btnCloseDirBrowser.addEventListener("click", closeDirBrowser);
  if (btnCloseDirDot) btnCloseDirDot.addEventListener("click", closeDirBrowser);

  btnDirGoUp.addEventListener("click", () => {
    if (parentBrowserDir) loadDirectory(parentBrowserDir);
  });

  btnSelectCurrentDir.addEventListener("click", () => {
    if (activeBrowserDir) {
      inputLocalPath.value = activeBrowserDir;
      browserSelectedFolderFiles = null;
      finderFolderLabel.textContent = "";
      closeDirBrowser();
      showToast(`로컬 경로 선택 완료: ${activeBrowserDir}`, "success");
    }
  });

  async function loadDirectory(path) {
    dirBrowserList.innerHTML = '<p style="padding:1rem; color:var(--text-muted); font-size:0.85rem; text-align:center;">디렉터리 탐색 중...</p>';
    try {
      const query = path ? `?path=${encodeURIComponent(path)}` : "";
      const res = await fetch(`/api/v1/projects/browse/local-dirs${query}`);
      if (!res.ok) throw new Error("디렉터리 정보를 가져오지 못했습니다.");
      const data = await res.json();

      activeBrowserDir = data.current_path;
      parentBrowserDir = data.parent_path;
      dirBrowserCurrentPath.textContent = activeBrowserDir;
      btnDirGoUp.disabled = !parentBrowserDir;

      renderDirectoryList(data.directories);
    } catch (err) {
      dirBrowserList.innerHTML = `<p style="padding:1rem; color:var(--danger); font-size:0.85rem; text-align:center;">${err.message}</p>`;
    }
  }

  function renderDirectoryList(directories) {
    dirBrowserList.innerHTML = "";
    if (!directories || directories.length === 0) {
      dirBrowserList.innerHTML = '<p style="padding:1rem; color:var(--text-muted); font-size:0.85rem; text-align:center;">하위 디렉터리가 없습니다.</p>';
      return;
    }

    directories.forEach((dir) => {
      const row = document.createElement("div");
      row.className = "dir-item";

      const nameSpan = document.createElement("div");
      nameSpan.className = "dir-item-name";
      nameSpan.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        <span>${dir.name}</span>
      `;
      nameSpan.addEventListener("click", () => loadDirectory(dir.path));

      const actions = document.createElement("div");
      actions.style.display = "flex";
      actions.style.alignItems = "center";
      actions.style.gap = "0.5rem";

      if (dir.md_count > 0) {
        const badge = document.createElement("span");
        badge.className = "dir-md-badge";
        badge.textContent = `📄 ${dir.md_count} .md`;
        actions.appendChild(badge);
      }

      const pickBtn = document.createElement("button");
      pickBtn.className = "nav-pill-btn";
      pickBtn.style.padding = "0.2rem 0.6rem";
      pickBtn.style.fontSize = "0.75rem";
      pickBtn.textContent = "선택";
      pickBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        inputLocalPath.value = dir.path;
        browserSelectedFolderFiles = null;
        finderFolderLabel.textContent = "";
        closeDirBrowser();
        showToast(`로컬 경로 선택 완료: ${dir.path}`, "success");
      });
      actions.appendChild(pickBtn);

      row.appendChild(nameSpan);
      row.appendChild(actions);
      dirBrowserList.appendChild(row);
    });
  }

  // Finder Directory Picker
  btnPickFolderFinder.addEventListener("click", () => {
    browserFolderPicker.click();
  });

  browserFolderPicker.addEventListener("change", (e) => {
    const files = Array.from(e.target.files);
    const mdFiles = files.filter((f) => f.name.toLowerCase().endsWith(".md"));

    if (mdFiles.length === 0) {
      showToast("선택한 폴더 내에 마크다운(.md) 파일이 없습니다.", "error");
      return;
    }

    browserSelectedFolderFiles = mdFiles;
    inputLocalPath.value = "";
    finderFolderLabel.textContent = `✓ Finder에서 선택됨: ${mdFiles.length}개 마크다운 문서`;
    showToast(`Finder 폴더 선택 완료 (${mdFiles.length}개 마크다운 감지)`, "success");
  });

  // Submit Import
  btnSubmitImport.addEventListener("click", async () => {
    setLoading(btnSubmitImport, true, "임포트 중...");
    try {
      if (currentImportTab === "local" && browserSelectedFolderFiles && browserSelectedFolderFiles.length > 0) {
        const formData = new FormData();
        browserSelectedFolderFiles.forEach((file) => {
          const relPath = file.webkitRelativePath || file.name;
          formData.append("files", file, relPath);
        });

        const res = await fetch(`/api/v1/projects/${encodeURIComponent(currentProject)}/import/files`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || "폴더 업로드 임포트에 실패했습니다.");
        }

        const result = await res.json();
        showToast(`🎉 임포트 완료: ${result.imported_files}개 마크다운 문서가 적재되었습니다.`, "success");
        closeImportModal();
        await loadTOC();
        return;
      }

      let endpoint = "";
      let payload = {};

      if (currentImportTab === "github") {
        const url = inputGithubUrl.value.trim();
        const branch = inputGithubBranch.value.trim();
        if (!url) {
          showToast("GitHub URL을 입력해 주세요.", "error");
          setLoading(btnSubmitImport, false, "임포트 시작");
          return;
        }
        endpoint = `/api/v1/projects/${encodeURIComponent(currentProject)}/import/github`;
        payload = { repo_url: url, branch: branch || undefined };
      } else {
        const pathVal = inputLocalPath.value.trim();
        if (!pathVal) {
          showToast("로컬 디렉터리 경로를 입력해 주세요.", "error");
          setLoading(btnSubmitImport, false, "임포트 시작");
          return;
        }
        endpoint = `/api/v1/projects/${encodeURIComponent(currentProject)}/import/local`;
        payload = { source_path: pathVal };
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.message || "지식 임포트에 실패했습니다.");
      }

      const result = await res.json();
      showToast(`🎉 임포트 완료: ${result.imported_files}개 마크다운 문서 적재 완료`, "success");
      closeImportModal();
      await loadTOC();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btnSubmitImport, false, "임포트 시작");
    }
  });

  // ==========================================================================
  // 8. Utility Functions
  // ==========================================================================
  function setLoading(btn, isLoading, text) {
    const textSpan = btn.querySelector(".btn-text");
    const spinner = btn.querySelector(".spinner");
    btn.disabled = isLoading;
    if (isLoading) {
      if (textSpan) textSpan.textContent = text;
      if (spinner) spinner.style.display = "inline-block";
    } else {
      if (textSpan) textSpan.textContent = text;
      if (spinner) spinner.style.display = "none";
    }
  }

  function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${type === "success" ? "✓" : "⚠"}</span>
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(12px)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // ==========================================================================
  // 9. AI & .env Settings Modal Controller
  // ==========================================================================
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const settingsModal = document.getElementById("settings-modal");
  const btnCloseSettingsModal = document.getElementById("btn-close-settings-modal");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const sourceModalAiPill = document.getElementById("source-modal-ai-pill");
  const sourceModalAiName = document.getElementById("source-modal-ai-name");
  const sourceModalStatusDot = document.getElementById("source-modal-status-dot");

  const settingsProviderTabs = document.querySelectorAll("[data-settings-provider]");
  const geminiKeyStatus = document.getElementById("gemini-key-status");
  const inputGeminiKey = document.getElementById("input-gemini-key");
  const selectGeminiModel = document.getElementById("select-gemini-model");
  const btnToggleGeminiVis = document.getElementById("btn-toggle-gemini-key-vis");

  const openaiKeyStatus = document.getElementById("openai-key-status");
  const inputOpenaiKey = document.getElementById("input-openai-key");
  const inputOpenaiModel = document.getElementById("input-openai-model");
  const btnToggleOpenaiVis = document.getElementById("btn-toggle-openai-key-vis");

  const inputOllamaUrl = document.getElementById("input-ollama-url");
  const inputOllamaModel = document.getElementById("input-ollama-model");

  const inputCustomUrl = document.getElementById("input-custom-url");
  const inputCustomKey = document.getElementById("input-custom-key");
  const inputCustomModel = document.getElementById("input-custom-model");

  let currentActiveProvider = "google";

  // Tab switching for settings provider
  settingsProviderTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      settingsProviderTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentActiveProvider = tab.dataset.settingsProvider;

      document.querySelectorAll(".settings-provider-pane").forEach(pane => {
        pane.style.display = "none";
      });
      const targetPane = document.getElementById(`settings-pane-${currentActiveProvider}`);
      if (targetPane) targetPane.style.display = "block";
    });
  });

  // Password visibility toggle helper
  function setupKeyVisToggle(btn, input) {
    if (!btn || !input) return;
    btn.addEventListener("click", () => {
      if (input.type === "password") {
        input.type = "text";
        btn.textContent = "🔒";
      } else {
        input.type = "password";
        btn.textContent = "👁";
      }
    });
  }
  setupKeyVisToggle(btnToggleGeminiVis, inputGeminiKey);
  setupKeyVisToggle(btnToggleOpenaiVis, inputOpenaiKey);

  async function loadSettings() {
    try {
      const res = await fetch("/api/v1/settings");
      if (!res.ok) return;
      const data = await res.json();

      currentActiveProvider = data.llm_provider || "google";

      // Select active tab
      settingsProviderTabs.forEach(tab => {
        const isMatch = tab.dataset.settingsProvider === currentActiveProvider;
        tab.classList.toggle("active", isMatch);
      });
      document.querySelectorAll(".settings-provider-pane").forEach(pane => {
        pane.style.display = "none";
      });
      const activePane = document.getElementById(`settings-pane-${currentActiveProvider}`);
      if (activePane) activePane.style.display = "block";

      // Gemini
      if (data.gemini_api_key_set) {
        geminiKeyStatus.textContent = `설정됨 (${data.gemini_api_key_masked})`;
        geminiKeyStatus.className = "key-status-badge set";
      } else {
        geminiKeyStatus.textContent = "미설정";
        geminiKeyStatus.className = "key-status-badge unset";
      }
      if (data.gemini_model && selectGeminiModel) {
        selectGeminiModel.value = data.gemini_model;
      }

      // OpenAI
      if (data.openai_api_key_set) {
        openaiKeyStatus.textContent = `설정됨 (${data.openai_api_key_masked})`;
        openaiKeyStatus.className = "key-status-badge set";
      } else {
        openaiKeyStatus.textContent = "미설정";
        openaiKeyStatus.className = "key-status-badge unset";
      }
      if (data.openai_model && inputOpenaiModel) {
        inputOpenaiModel.value = data.openai_model;
      }

      // Ollama
      if (data.ollama_base_url && inputOllamaUrl) inputOllamaUrl.value = data.ollama_base_url;
      if (data.ollama_model && inputOllamaModel) inputOllamaModel.value = data.ollama_model;

      // Custom
      if (data.openai_base_url && inputCustomUrl) inputCustomUrl.value = data.openai_base_url;

      // Update AI status badge in modal
      if (sourceModalAiName) {
        let name = "Gemini 3.8 Flash";
        let isConfigured = true;
        if (currentActiveProvider === "google") {
          name = data.gemini_model || "Gemini";
          isConfigured = data.gemini_api_key_set;
        } else if (currentActiveProvider === "openai") {
          name = data.openai_model || "OpenAI";
          isConfigured = data.openai_api_key_set;
        } else if (currentActiveProvider === "ollama") {
          name = `Ollama (${data.ollama_model || "Local"})`;
          isConfigured = true;
        } else if (currentActiveProvider === "custom") {
          name = "Custom LLM";
          isConfigured = Boolean(data.openai_base_url);
        }
        sourceModalAiName.textContent = name;
        if (sourceModalStatusDot) {
          sourceModalStatusDot.className = `status-dot ${isConfigured ? "" : "warning"}`;
        }
      }
    } catch (e) {
      console.warn("Failed to load settings:", e);
    }
  }

  async function saveSettings() {
    setLoading(btnSaveSettings, true, "저장 중...");
    try {
      const payload = {
        llm_provider: currentActiveProvider,
      };

      const geminiKeyVal = inputGeminiKey.value.trim();
      if (geminiKeyVal) payload.gemini_api_key = geminiKeyVal;
      if (selectGeminiModel) payload.gemini_model = selectGeminiModel.value;

      const openaiKeyVal = inputOpenaiKey.value.trim();
      if (openaiKeyVal) payload.openai_api_key = openaiKeyVal;
      if (inputOpenaiModel) payload.openai_model = inputOpenaiModel.value.trim();

      if (inputOllamaUrl) payload.ollama_base_url = inputOllamaUrl.value.trim();
      if (inputOllamaModel) payload.ollama_model = inputOllamaModel.value.trim();

      if (currentActiveProvider === "custom") {
        if (inputCustomUrl) payload.openai_base_url = inputCustomUrl.value.trim();
        if (inputCustomKey && inputCustomKey.value.trim()) payload.openai_api_key = inputCustomKey.value.trim();
        if (inputCustomModel && inputCustomModel.value.trim()) payload.openai_model = inputCustomModel.value.trim();
      }

      const res = await fetch("/api/v1/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "설정 저장에 실패했습니다.");
      }

      inputGeminiKey.value = "";
      inputOpenaiKey.value = "";
      if (inputCustomKey) inputCustomKey.value = "";

      await loadSettings();
      closeSettingsModal();
      showToast("API 설정이 .env 파일에 안전하게 저장되었습니다.", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btnSaveSettings, false, "💾 .env에 저장 및 적용");
    }
  }

  function openSettingsModal() {
    loadSettings();
    if (settingsModal) {
      settingsModal.classList.add("active");
      settingsModal.style.display = "flex";
    }
  }

  function closeSettingsModal() {
    if (settingsModal) {
      settingsModal.classList.remove("active");
      settingsModal.style.display = "none";
    }
  }

  if (btnOpenSettings) {
    btnOpenSettings.addEventListener("click", openSettingsModal);
  }
  if (sourceModalAiPill) {
    sourceModalAiPill.addEventListener("click", openSettingsModal);
  }
  if (btnCloseSettingsModal) {
    btnCloseSettingsModal.addEventListener("click", closeSettingsModal);
  }
  if (btnCancelSettings) {
    btnCancelSettings.addEventListener("click", closeSettingsModal);
  }
  if (btnSaveSettings) {
    btnSaveSettings.addEventListener("click", saveSettings);
  }
  if (settingsModal) {
    settingsModal.addEventListener("click", (e) => {
      if (e.target === settingsModal) closeSettingsModal();
    });
  }

  // Initial Load
  loadTOC();
  loadSettings();
});
