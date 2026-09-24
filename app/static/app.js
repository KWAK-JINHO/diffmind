// app/static/app.js

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const projectSelect = document.getElementById("project-select");
  const btnOpenCreateProject = document.getElementById("btn-open-create-project");
  const btnOpenImport = document.getElementById("btn-open-import");

  const tocContainer = document.getElementById("toc-container");
  const btnRefreshToc = document.getElementById("btn-refresh-toc");
  const tabBtns = document.querySelectorAll(".tab-btn[data-tab]");
  const tabContents = document.querySelectorAll(".tab-content");

  // Inputs
  const inputText = document.getElementById("input-text");
  const fileDropzone = document.getElementById("file-dropzone");
  const fileInput = document.getElementById("file-input");
  const filePreviewName = document.getElementById("file-preview-name");
  const imageDropzone = document.getElementById("image-dropzone");
  const imageInput = document.getElementById("image-input");
  const imagePreviewBox = document.getElementById("image-preview-box");
  const imagePreview = document.getElementById("image-preview");

  // Buttons
  const btnPropose = document.getElementById("btn-propose");
  const btnAccept = document.getElementById("btn-accept");
  const btnRecentDiff = document.getElementById("btn-recent-diff");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const recentDiffModal = document.getElementById("recent-diff-modal");
  const modalDiffContent = document.getElementById("modal-diff-content");

  // Project Modal Elements
  const createProjectModal = document.getElementById("create-project-modal");
  const btnCloseProjectModal = document.getElementById("btn-close-project-modal");
  const btnCancelCreateProject = document.getElementById("btn-cancel-create-project");
  const btnSubmitCreateProject = document.getElementById("btn-submit-create-project");
  const inputNewProjectName = document.getElementById("input-new-project-name");
  const inputNewProjectDesc = document.getElementById("input-new-project-desc");

  // Import Modal Elements
  const importModal = document.getElementById("import-modal");
  const btnCloseImportModal = document.getElementById("btn-close-import-modal");
  const btnCancelImport = document.getElementById("btn-cancel-import");
  const btnSubmitImport = document.getElementById("btn-submit-import");
  const importTargetProjectLabel = document.getElementById("import-target-project-label");
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
  const dirBrowserCurrentPath = document.getElementById("dir-browser-current-path");
  const btnDirGoUp = document.getElementById("btn-dir-go-up");
  const btnSelectCurrentDir = document.getElementById("btn-select-current-dir");
  const dirBrowserList = document.getElementById("dir-browser-list");

  // Proposal Section
  const proposalSection = document.getElementById("proposal-section");
  const metaTargetPath = document.getElementById("meta-target-path");
  const metaFileBadge = document.getElementById("meta-file-badge");
  const metaTargetHeading = document.getElementById("meta-target-heading");
  const metaReason = document.getElementById("meta-reason");
  const diffFileHeader = document.getElementById("diff-file-header");
  const diffContent = document.getElementById("diff-content");
  const inputCommitMsg = document.getElementById("input-commit-msg");

  // Sources & Search Elements
  const sourcesSearchInput = document.getElementById("sources-search-input");
  const btnQuickNewNote = document.getElementById("btn-quick-new-note");
  const statsFileCount = document.getElementById("stats-file-count");
  const statsHeadingCount = document.getElementById("stats-heading-count");

  // Reader Elements
  const bcProjectName = document.getElementById("bc-project-name");
  const bcFileName = document.getElementById("bc-file-name");
  const btnReaderToggleMode = document.getElementById("btn-reader-toggle-mode");
  const btnReaderCopy = document.getElementById("btn-reader-copy");
  const outlineDropdown = document.getElementById("outline-dropdown");
  const btnToggleOutline = document.getElementById("btn-toggle-outline");
  const outlineMenu = document.getElementById("outline-menu");
  const btnToggleStudio = document.getElementById("btn-toggle-studio");
  const studioToggleArrow = document.getElementById("studio-toggle-arrow");
  const readerEmptyState = document.getElementById("reader-empty-state");
  const readerActiveContent = document.getElementById("reader-active-content");
  const readerDocPath = document.getElementById("reader-doc-path");
  const readerDocSize = document.getElementById("reader-doc-size");
  const readerDocHeadingsCount = document.getElementById("reader-doc-headings-count");
  const readerMarkdownRender = document.getElementById("reader-markdown-render");
  const readerRawBox = document.getElementById("reader-raw-box");
  const readerRawCode = document.getElementById("reader-raw-code");
  const quickActionSelectDoc = document.getElementById("quick-action-select-doc");
  const quickActionAddNote = document.getElementById("quick-action-add-note");
  const quickActionImport = document.getElementById("quick-action-import");

  // Studio Sidebar Elements
  const studioSidebar = document.getElementById("studio-sidebar");
  const btnCollapseStudio = document.getElementById("btn-collapse-studio");

  // State
  let currentProject = "default";
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
  let expandedFileHeadings = new Set();
  let isStudioOpen = true;

  // 1. Projects Management
  async function loadProjects() {
    try {
      const res = await fetch("/api/v1/projects");
      if (!res.ok) throw new Error("프로젝트 목록을 불러오지 못했습니다.");
      const projects = await res.json();

      projectSelect.innerHTML = "";
      projects.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.name;
        opt.textContent = `${p.name} (${p.file_count} docs)`;
        if (p.name === currentProject) {
          opt.selected = true;
        }
        projectSelect.appendChild(opt);
      });

      // If currentProject not in list, fallback to first
      if (projects.length > 0 && !projects.some((p) => p.name === currentProject)) {
        currentProject = projects[0].name;
        projectSelect.value = currentProject;
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  projectSelect.addEventListener("change", (e) => {
    currentProject = e.target.value;
    bcProjectName.textContent = currentProject;
    proposalSection.style.display = "none";
    activeProposal = null;
    currentLoadedFile = null;
    readerActiveContent.style.display = "none";
    readerEmptyState.style.display = "block";
    bcFileName.textContent = "문서를 선택하세요";
    btnReaderToggleMode.style.display = "none";
    btnReaderCopy.style.display = "none";
    outlineDropdown.style.display = "none";
    loadTOC();
    showToast(`프로젝트를 '${currentProject}'(으)로 전환했습니다.`, "success");
  });

  // Create Project Modal Handlers
  btnOpenCreateProject.addEventListener("click", () => {
    inputNewProjectName.value = "";
    inputNewProjectDesc.value = "";
    createProjectModal.style.display = "flex";
    inputNewProjectName.focus();
  });

  function closeProjectModal() {
    createProjectModal.style.display = "none";
  }

  btnCloseProjectModal.addEventListener("click", closeProjectModal);
  btnCancelCreateProject.addEventListener("click", closeProjectModal);

  btnSubmitCreateProject.addEventListener("click", async () => {
    const name = inputNewProjectName.value.trim();
    const desc = inputNewProjectDesc.value.trim();

    if (!name) {
      showToast("프로젝트 이름을 입력해 주세요.", "error");
      return;
    }

    setLoading(btnSubmitCreateProject, true, "생성 중...");
    try {
      const res = await fetch("/api/v1/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description: desc || undefined }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || errData.message || "프로젝트 생성에 실패했습니다.");
      }

      const created = await res.json();
      showToast(`✅ 새 프로젝트 '${created.name}'이(가) 생성되었습니다!`, "success");
      currentProject = created.name;
      closeProjectModal();
      await loadProjects();
      loadTOC();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btnSubmitCreateProject, false, "생성하기");
    }
  });

  // 2. Knowledge Import Modal Handlers
  btnOpenImport.addEventListener("click", () => {
    importTargetProjectLabel.textContent = currentProject;
    inputGithubUrl.value = "";
    inputGithubBranch.value = "";
    inputLocalPath.value = "";
    importModal.style.display = "flex";
  });

  function closeImportModal() {
    importModal.style.display = "none";
  }

  btnCloseImportModal.addEventListener("click", closeImportModal);
  btnCancelImport.addEventListener("click", closeImportModal);

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

  // Directory Browser Modal Handlers
  btnOpenDirBrowser.addEventListener("click", () => {
    dirBrowserModal.style.display = "flex";
    loadDirectory(inputLocalPath.value.trim() || null);
  });

  function closeDirBrowser() {
    dirBrowserModal.style.display = "none";
  }

  btnCloseDirBrowser.addEventListener("click", closeDirBrowser);

  btnDirGoUp.addEventListener("click", () => {
    if (parentBrowserDir) {
      loadDirectory(parentBrowserDir);
    }
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
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        <span>${dir.name}</span>
      `;

      nameSpan.addEventListener("click", () => {
        loadDirectory(dir.path);
      });

      const actions = document.createElement("div");
      actions.className = "dir-item-actions";

      if (dir.md_count > 0) {
        const badge = document.createElement("span");
        badge.className = "dir-md-badge";
        badge.textContent = `📄 ${dir.md_count} .md`;
        actions.appendChild(badge);
      }

      const pickBtn = document.createElement("button");
      pickBtn.className = "btn btn-sm btn-secondary";
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

  // Finder Folder Picker Setup
  btnPickFolderFinder.addEventListener("click", () => {
    browserFolderPicker.click();
  });

  browserFolderPicker.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const allFiles = Array.from(e.target.files);
      const mdFiles = allFiles.filter(f => f.name.toLowerCase().endsWith(".md"));

      if (mdFiles.length === 0) {
        showToast("선택된 폴더 내에 마크다운(.md) 파일이 없습니다.", "error");
        browserSelectedFolderFiles = null;
        finderFolderLabel.textContent = "";
        return;
      }

      browserSelectedFolderFiles = mdFiles;
      const folderName = mdFiles[0].webkitRelativePath ? mdFiles[0].webkitRelativePath.split("/")[0] : "선택된 폴더";
      finderFolderLabel.textContent = `✓ '${folderName}' 폴더 선택됨 (총 ${mdFiles.length}개 .md 문서)`;
      inputLocalPath.value = `[Finder 업로드: ${folderName}]`;
      showToast(`Finder에서 '${folderName}' 폴더가 선택되었습니다 (${mdFiles.length}개 문서).`, "success");
    }
  });

  btnSubmitImport.addEventListener("click", async () => {
    setLoading(btnSubmitImport, true, "임포트 및 Git 커밋 중...");

    try {
      // 1. Direct browser folder upload
      if (currentImportTab === "local" && browserSelectedFolderFiles && browserSelectedFolderFiles.length > 0) {
        const formData = new FormData();
        browserSelectedFolderFiles.forEach((file) => {
          formData.append("files", file);
          formData.append("paths", file.webkitRelativePath || file.name);
        });

        const res = await fetch(`/api/v1/projects/${encodeURIComponent(currentProject)}/import/files`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || errData.message || "폴더 업로드 임포트에 실패했습니다.");
        }

        const result = await res.json();
        showToast(`🎉 Finder 폴더 임포트 완료: ${result.imported_files}개 문서가 적재되었습니다. [커밋: ${result.commit_hash}]`, "success");
        browserSelectedFolderFiles = null;
        finderFolderLabel.textContent = "";
        closeImportModal();
        await loadProjects();
        loadTOC();
        return;
      }

      // 2. Standard URL or path import
      let endpoint = "";
      let payload = {};

      if (currentImportTab === "github") {
        const url = inputGithubUrl.value.trim();
        const branch = inputGithubBranch.value.trim();
        if (!url) {
          showToast("GitHub HTTPS URL을 입력해 주세요.", "error");
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
      showToast(`🎉 임포트 완료: ${result.imported_files}개 마크다운 문서가 적재되었습니다. [커밋: ${result.commit_hash}]`, "success");
      closeImportModal();
      await loadProjects();
      loadTOC();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btnSubmitImport, false, "임포트 시작");
    }
  });

  // 3. Main Input Tabs
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      currentTab = btn.dataset.tab;
      document.getElementById(`tab-${currentTab}`).classList.add("active");
    });
  });

  function switchTab(tabKey) {
    tabBtns.forEach((b) => b.classList.remove("active"));
    tabContents.forEach((c) => c.classList.remove("active"));

    const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabKey}"]`);
    if (targetBtn) targetBtn.classList.add("active");
    currentTab = tabKey;
    const targetContent = document.getElementById(`tab-${tabKey}`);
    if (targetContent) targetContent.classList.add("active");
  }

  // File & Image Dropzone Setups
  setupDropzone(fileDropzone, fileInput, (file) => {
    selectedFile = file;
    filePreviewName.innerHTML = `
      <span style="color:var(--success); font-weight:600;">✓ ${file.name}</span>
      <span style="color:var(--text-muted);">(${formatBytes(file.size)})</span>
      <span style="color:var(--accent); margin-left:0.5rem;">선택 완료! 아래 버튼을 클릭하세요.</span>
    `;
    btnPropose.classList.add("pulse");
  });

  setupDropzone(imageDropzone, imageInput, (file) => {
    selectedImage = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imagePreviewBox.style.display = "block";
    };
    reader.readAsDataURL(file);
    btnPropose.classList.add("pulse");
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

      const items = e.dataTransfer.items;
      if (items && items.length > 0) {
        const entry = items[0].webkitGetAsEntry ? items[0].webkitGetAsEntry() : null;
        if (entry && entry.isDirectory) {
          showToast("폴더(디렉터리)가 감지되었습니다. 상단의 [📥 지식 임포트] 기능을 사용하거나 개별 .md 파일을 선택해 주세요.", "error");
          return;
        }
      }

      if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.name.endsWith(".md") || file.name.endsWith(".txt") || file.name.endsWith(".markdown")) {
          switchTab("file");
          onFileSelected(file);
        } else if (file.type.startsWith("image/")) {
          switchTab("image");
          onFileSelected(file);
        } else {
          onFileSelected(file);
        }
      }
    });

    inputElement.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        onFileSelected(e.target.files[0]);
      }
    });
  }

  // 4. File Tree & Hierarchy Construction
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
    tocContainer.innerHTML = "";
    const filterQuery = sourcesSearchInput ? sourcesSearchInput.value.trim().toLowerCase() : "";
    const tree = buildFileTree(currentTOC);

    const totalFiles = Object.keys(currentTOC).length;
    const totalHeadings = Object.values(currentTOC).reduce((acc, h) => acc + h.length, 0);
    if (statsFileCount) statsFileCount.textContent = `${totalFiles} docs`;
    if (statsHeadingCount) statsHeadingCount.textContent = `${totalHeadings} headings`;

    if (totalFiles === 0) {
      tocContainer.innerHTML = `
        <div style="padding:1.5rem 1rem; color:var(--text-muted); font-size:0.85rem; text-align:center;">
          현재 프로젝트에 문서가 없습니다.<br>
          <strong>[+ 새 지식 노트]</strong>를 작성하거나<br>
          상단의 <strong>[📥 지식 임포트]</strong>를 이용해 보세요!
        </div>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    renderTreeChildren(tree, fragment, filterQuery);

    if (fragment.children.length === 0 && filterQuery) {
      tocContainer.innerHTML = `
        <div style="padding:1.5rem 1rem; color:var(--text-muted); font-size:0.85rem; text-align:center;">
          '${filterQuery}'에 일치하는 문서가 없습니다.
        </div>`;
      return;
    }

    tocContainer.appendChild(fragment);
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

  // 5. Document Study Reader
  async function openDocument(relPath, targetHeading = null) {
    try {
      const res = await fetch(`/api/v1/files?project=${encodeURIComponent(currentProject)}&path=${encodeURIComponent(relPath)}`);
      if (!res.ok) {
        throw new Error("문서를 불러오지 못했습니다.");
      }
      const data = await res.json();
      currentLoadedFile = data;

      // Update Header Breadcrumb
      bcProjectName.textContent = currentProject;
      bcFileName.textContent = relPath;

      // Update Reader Meta
      readerDocPath.textContent = relPath;
      readerDocSize.textContent = formatBytes(data.size_bytes);
      readerDocHeadingsCount.textContent = `${data.headings.length}개 목차(헤딩)`;

      // Render Markdown
      renderMarkdownContent(data.content);

      // Render Outline Dropdown
      renderOutlineMenu(data.headings);

      // Toggle views
      readerEmptyState.style.display = "none";
      readerActiveContent.style.display = "block";
      btnReaderToggleMode.style.display = "inline-flex";
      btnReaderCopy.style.display = "inline-flex";
      outlineDropdown.style.display = "inline-block";

      // Re-render tree to update active class
      renderFileTree();

      // Scroll to heading if specified
      if (targetHeading) {
        scrollToHeading(targetHeading);
      } else {
        const readerBody = document.getElementById("reader-body");
        if (readerBody) readerBody.scrollTop = 0;
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function renderMarkdownContent(content) {
    if (typeof marked !== "undefined" && marked.parse) {
      try {
        marked.setOptions({
          gfm: true,
          breaks: true,
        });
      } catch (e) {}

      let html = marked.parse(content);
      readerMarkdownRender.innerHTML = html;
    } else {
      readerMarkdownRender.innerHTML = renderBasicMarkdownFallback(content);
    }

    // Attach anchor IDs to headings for jump links
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
      outlineMenu.innerHTML = '<div style="padding:0.75rem; color:var(--text-muted); font-size:0.8rem; text-align:center;">헤딩이 없습니다.</div>';
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
        setTimeout(() => {
          h.style.background = origBg;
        }, 1500);
        break;
      }
    }
  }

  function renderBasicMarkdownFallback(text) {
    if (!text) return "";
    let escaped = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

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

  function toggleStudio(forceOpen) {
    if (typeof forceOpen === "boolean") {
      isStudioOpen = forceOpen;
    } else {
      isStudioOpen = !isStudioOpen;
    }

    if (isStudioOpen) {
      studioSidebar.classList.remove("collapsed");
      if (studioToggleArrow) studioToggleArrow.textContent = "⇥";
    } else {
      studioSidebar.classList.add("collapsed");
      if (studioToggleArrow) studioToggleArrow.textContent = "⇤";
    }
  }

  // Sources & Reader Events
  if (sourcesSearchInput) {
    sourcesSearchInput.addEventListener("input", () => {
      renderFileTree();
    });
  }

  if (btnQuickNewNote) {
    btnQuickNewNote.addEventListener("click", () => {
      toggleStudio(true);
      inputText.focus();
    });
  }

  btnRefreshToc.addEventListener("click", () => {
    loadTOC();
    showToast("지식 소스 트리를 새로고침했습니다.", "success");
  });

  if (btnToggleStudio) {
    btnToggleStudio.addEventListener("click", () => {
      toggleStudio();
    });
  }

  if (btnCollapseStudio) {
    btnCollapseStudio.addEventListener("click", () => {
      toggleStudio(false);
    });
  }

  if (btnReaderToggleMode) {
    btnReaderToggleMode.addEventListener("click", () => {
      rawModeActive = !rawModeActive;
      if (rawModeActive) {
        readerMarkdownRender.style.display = "none";
        readerRawBox.style.display = "block";
        btnReaderToggleMode.textContent = "📖 렌더링 보기";
      } else {
        readerMarkdownRender.style.display = "block";
        readerRawBox.style.display = "none";
        btnReaderToggleMode.textContent = "👁 원문 보기";
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

  // Quick action cards
  if (quickActionSelectDoc) {
    quickActionSelectDoc.addEventListener("click", () => {
      if (sourcesSearchInput) sourcesSearchInput.focus();
    });
  }

  if (quickActionAddNote) {
    quickActionAddNote.addEventListener("click", () => {
      toggleStudio(true);
      inputText.focus();
    });
  }

  if (quickActionImport) {
    quickActionImport.addEventListener("click", () => {
      btnOpenImport.click();
    });
  }

  // 5. Submit Proposal
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

    btnPropose.classList.remove("pulse");
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
    diffFileHeader.textContent = `Unified Diff: ${proposal.target_file_path} (Project: ${currentProject})`;

    renderDiff(diffContent, proposal.unified_diff);

    const action = proposal.is_new_file ? "create" : "update";
    inputCommitMsg.value = `docs: ${action} ${proposal.target_file_path} under '${proposal.target_heading}'`;

    proposalSection.style.display = "flex";
    toggleStudio(true);
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

  // 6. Accept Proposal & Git Commit
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

      await loadProjects();
      await loadTOC();

      // Automatically display the merged document in the Center Reader!
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

  // 7. Recent Git Diff Modal
  btnRecentDiff.addEventListener("click", async () => {
    try {
      const res = await fetch(`/api/v1/recent-diff?project=${encodeURIComponent(currentProject)}`);
      if (!res.ok) throw new Error("최근 diff 정보를 불러오지 못했습니다.");
      const data = await res.json();
      renderDiff(modalDiffContent, data.diff);
      recentDiffModal.style.display = "flex";
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  btnCloseModal.addEventListener("click", () => {
    recentDiffModal.style.display = "none";
  });

  recentDiffModal.addEventListener("click", (e) => {
    if (e.target === recentDiffModal) {
      recentDiffModal.style.display = "none";
    }
  });

  // Helpers
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
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${type === "success" ? "✓" : "⚠"}</span>
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // Initial Boot
  loadProjects();
  loadTOC();
});
