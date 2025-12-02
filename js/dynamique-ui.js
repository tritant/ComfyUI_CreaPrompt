import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ============================================================================
// 🛠️ FONCTIONS UTILITAIRES (Helpers)
// ============================================================================

function updateNodeSize(node) {
    const [minWidth, minHeight] = node.computeSize();
    const currentWidth = (node.size && node.size[0] > 10) ? node.size[0] : 220;
    node.setSize([currentWidth, minHeight]);
    node.graph?.setDirtyCanvas(true, true);
}

async function getCsvMapping() {
    try {
        const res = await fetch("/custom_nodes/creaprompt/csv_list");
        if (!res.ok) throw new Error("Erreur liste CSV");
        const files = await res.json();
        const fileMap = {};
        for (const f of files) {
            const base = f.replace(/^\d+_\d*/, "").replace(/\.csv$/, "");
            fileMap[base] = f;
        }
        return { fileMap, allFiles: files };
    } catch (e) {
        return { fileMap: {}, allFiles: [] };
    }
}

async function fetchCsvValues(filename) {
    try {
        const res = await fetch(`/custom_nodes/creaprompt/csv/${filename}`);
        if (!res.ok) return ["disabled", "🎲random"];
        const text = await res.text();
        const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
        return ["disabled", "🎲random", ...lines];
    } catch (e) {
        return ["disabled", "🎲random"];
    }
}

async function syncComboWidget(node, label, selectedValue, csvFilename) {
    const values = await fetchCsvValues(csvFilename);
    
    if (!values.includes(selectedValue) && selectedValue !== "disabled" && selectedValue !== "🎲random") {
        values.push(selectedValue);
    }

    const existingWidget = node.widgets ? node.widgets.find(w => w.name === label) : null;

    if (existingWidget) {
        existingWidget.options.values = values;
        existingWidget.value = selectedValue;
        node._crea_dynamicValues[label] = selectedValue;
    } else {
        const widget = node.addWidget("combo", label, selectedValue, (val) => {
            node._crea_dynamicValues[label] = val;
            node._crea_updateCsvJson();
        }, { values: values, serialize: false });
    }
    
    node._crea_dynamicValues[label] = selectedValue;
}

function cleanupWidgets(node, targetConfigKeys) {
    if (!node.widgets) return;

    const protectedWidgets = [
        "__csv_json",               
        "control_after_generate",   
        "preview_method",           
        "seed",                     
        "Prompt_count",             
        "CreaPrompt_Collection",
        "separator_top",
        "separator_bottom"
    ];

    for (let i = node.widgets.length - 1; i >= 0; i--) {
        const w = node.widgets[i];
        if (w.type === "CUSTOM_SPACER") continue;
        if (protectedWidgets.includes(w.name)) continue;

        if (w.type === "combo") {
            if (!targetConfigKeys.includes(w.name)) {
                node.widgets.splice(i, 1);
            }
        }
    }
}

async function loadDefaultConfig(node) {
    if (node._crea_is_restored || Object.keys(node._crea_dynamicValues).length > 0) return;

    try {
        const res = await fetch("/custom_nodes/creaprompt/presets/default_combos.txt");
        if (!res.ok) return;
        
        const text = await res.text();
        const labels = text.split("\n").map(l => l.trim()).filter(Boolean);
        const { fileMap } = await getCsvMapping();
        
        cleanupWidgets(node, labels);

        for (const label of labels) {
            if (node._crea_is_restored) break;
            const csvFile = fileMap[label];
            if (csvFile) {
                await syncComboWidget(node, label, "disabled", csvFile);
            }
        }
        node._crea_updateCsvJson();
        updateNodeSize(node);
    } catch (e) { console.warn(e); }
}

function showFloatingMenu(items, onClickItem, clickX, clickY, title = "Menu") {
    const oldMenu = document.getElementById("crea_prompt_floating_menu");
    if (oldMenu) oldMenu.remove();

    const menu = document.createElement("div");
    menu.id = "crea_prompt_floating_menu";
    Object.assign(menu.style, {
        position: "fixed", left: `${clickX}px`, top: `${clickY}px`,
        background: "#222", color: "#fff", border: "1px solid #666",
        padding: "0", zIndex: 9999, borderRadius: "4px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
        maxHeight: "60vh", overflowY: "auto", minWidth: "200px",
        fontFamily: "sans-serif", fontSize: "13px"
    });

    const header = document.createElement("div");
    header.innerHTML = `<b>${title}</b> <span style="float:right; cursor:pointer">❌</span>`;
    Object.assign(header.style, {
        padding: "6px 10px", borderBottom: "1px solid #444", background: "#333",
        position: "sticky", top: "0"
    });
    header.querySelector("span").onclick = () => menu.remove();
    menu.appendChild(header);

    if (items.length === 0) {
        menu.appendChild(Object.assign(document.createElement("div"), {textContent: "Vide", style:"padding:10px"}));
    } else {
        items.forEach(item => {
            const div = document.createElement("div");
            div.textContent = item.label || item;
            Object.assign(div.style, { padding: "5px 10px", cursor: "pointer" });
            div.onmouseover = () => div.style.background = "#444";
            div.onmouseout = () => div.style.background = "transparent";
            div.onclick = () => { onClickItem(item); menu.remove(); };
            menu.appendChild(div);
        });
    }
    document.body.appendChild(menu);
}

function addCustomSpacer(node, name, title) {
    node.widgets.push({
        name: name,
        type: "CUSTOM_SPACER",
        serialize: false, 
        draw: (ctx, node, width, y) => {
            const rectHeight = 20, marginY = 5, x_padding = 10;
            ctx.fillStyle = "#272"; 
            ctx.fillRect(x_padding, y + marginY, width - (x_padding * 2), rectHeight);
            ctx.fillStyle = "#CCC"; 
            ctx.font = "bold 12px Arial";
            ctx.textAlign = "center";
            const textY = y + marginY + rectHeight / 2 + 4;
            ctx.fillText(title, width / 2, textY);
        },
        computeSize: () => [0, 30] 
    });
}


// ============================================================================
// 🧩 EXTENSION PRINCIPALE
// ============================================================================

app.registerExtension({
    name: "CreaPrompt_UI",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CreaPrompt_0") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            const node = this;

            node._crea_dynamicValues = {};
            node._crea_is_restored = false; 
            node._crea_load_timer = null;

            // --- WIDGET JSON ---
            const jsonWidget = node.widgets.find(w => w.name === "__csv_json");
            
            node._crea_updateCsvJson = function() {
                if (jsonWidget) jsonWidget.value = JSON.stringify(node._crea_dynamicValues);
            };

            // ⚡⚡ CORRECTION DU BUG D'AFFICHAGE AU SCROLL ⚡⚡
            // Au lieu de le cacher une seule fois, on force le masquage à chaque redessin du node.
            // Cela résout le problème où ComfyUI recrée le DOM quand le node revient à l'écran.
            if (jsonWidget) {
                jsonWidget.computeSize = () => [0, -4]; // Réduit la taille logique
                
                const origDrawForeground = node.onDrawForeground;
                node.onDrawForeground = function (ctx) {
                    if (origDrawForeground) origDrawForeground.apply(this, arguments);
                    
                    // On vérifie et on cache l'élément DOM s'il est visible
                    if (jsonWidget.inputEl) {
                        if (jsonWidget.inputEl.style.display !== "none") {
                            jsonWidget.inputEl.style.display = "none";
                        }
                        // Parfois ComfyUI met le widget dans un parent qui a des marges/bordures
                        if (jsonWidget.inputEl.parentElement && jsonWidget.inputEl.parentElement.style.display !== "none") {
                            jsonWidget.inputEl.parentElement.style.display = "none";
                        }
                    }
                };
            }

            // 🕒 TIMEOUT
            node._crea_load_timer = setTimeout(() => {
                if (node._crea_is_restored) return;
                const rawJson = jsonWidget ? jsonWidget.value : null;
                if (rawJson && typeof rawJson === "string" && rawJson.trim().startsWith("{") && rawJson.trim() !== "{}") {
                    return; 
                }
                loadDefaultConfig(node);
            }, 100);

            // ================= 1. SPACER HAUT =================
            addCustomSpacer(node, "separator_top", "Preset Actions");

            // ================= BUTTONS =================
            node.addWidget("button", "💾 Save Categories Preset", "", async () => {
                const name = prompt("Name:");
                if (!name || name.length < 2) return;
                try {
                    await fetch("/custom_nodes/creaprompt/save_preset", {
                        method: "POST", headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ name: name.trim(), content: JSON.stringify(node._crea_dynamicValues, null, 2) })
                    });
                } catch (e) { alert("Error " + e.message); }
            });

            node.addWidget("button", "📂 Load Categories Preset", "", async (v, a, n, p, e) => {
                const cx = e?.clientX ?? 100; const cy = e?.clientY ?? 100;
                try {
                    const r = await fetch("/custom_nodes/creaprompt/presets_list");
                    const f = await r.json();
                    
                    const menuItems = f
                        .filter(x => x.endsWith(".txt") && x !== "default_combos.txt")
                        .map(filename => ({
                            label: filename.replace(/\.txt$/, ""), 
                            filename: filename                     
                        }));

                    showFloatingMenu(menuItems, async (item) => {
                        const r2 = await fetch(`/custom_nodes/creaprompt/presets/${item.filename}`);
                        const parsed = JSON.parse(await r2.text());
                        
                        const targetKeys = Object.keys(parsed);
                        node._crea_dynamicValues = {}; 

                        cleanupWidgets(node, targetKeys);

                        const { fileMap } = await getCsvMapping();
                        for (const [k, val] of Object.entries(parsed)) {
                            if(fileMap[k]) await syncComboWidget(node, k, val, fileMap[k]);
                        }
                        node._crea_updateCsvJson();
                        updateNodeSize(node);
                    }, cx, cy, "📂 Load");
                } catch (err) { alert("Error"); }
            });

            node.addWidget("button", "🗑️ Delete Categories Preset", "", async (v, a, n, p, e) => {
                const cx = e?.clientX ?? 100; const cy = e?.clientY ?? 100;
                try {
                    const r = await fetch("/custom_nodes/creaprompt/presets_list");
                    const f = await r.json();

                    const menuItems = f
                        .filter(x => x.endsWith(".txt") && x !== "default_combos.txt")
                        .map(filename => ({
                            label: filename.replace(/\.txt$/, ""), 
                            filename: filename 
                        }));

                    showFloatingMenu(menuItems, async (item) => {
                        if(confirm(`Delete ${item.label}?`)) await fetch(`/custom_nodes/creaprompt/delete_preset/${item.filename}`, {method:"DELETE"});
                    }, cx, cy, "🗑️ Delete");
                } catch (err) {}
            });

            node.addWidget("button", "➖ Remove Category", "", (v, a, n, p, e) => {
                const keys = Object.keys(node._crea_dynamicValues);
                if(!keys.length) return;
                showFloatingMenu(keys, (k) => {
                    const idx = node.widgets.findIndex(w => w.name === k);
                    if(idx>-1) node.widgets.splice(idx, 1);
                    delete node._crea_dynamicValues[k];
                    node._crea_updateCsvJson();
                    updateNodeSize(node);
                }, e?.clientX??100, e?.clientY??100, "➖ Remove");
            });

            node.addWidget("button", "🧹 Remove All", "", () => {
                if(!confirm("Remove all?")) return;
                cleanupWidgets(node, []); 
                node._crea_dynamicValues = {};
                node._crea_updateCsvJson();
                updateNodeSize(node);
            });

            node.addWidget("button", "➕ Add Category", "", async (v, a, n, p, e) => {
                const cx = e?.clientX ?? 100; const cy = e?.clientY ?? 100;
                const { fileMap } = await getCsvMapping();
                const used = Object.keys(node._crea_dynamicValues);
                const items = Object.keys(fileMap).filter(k => !used.includes(k)).map(k => ({label: k, file: fileMap[k]}));
                showFloatingMenu(items, async (i) => {
                    await syncComboWidget(node, i.label, "disabled", i.file);
                    node._crea_updateCsvJson();
                    updateNodeSize(node);
                }, cx, cy, "➕ Add");
            });

            // ================= 2. SPACER BAS =================
            addCustomSpacer(node, "separator_bottom", "Dynamic Categories");
        };
    },

    async loadedGraphNode(node, def) {
        if (node.type !== "CreaPrompt_0") return;

        if (node._crea_load_timer) {
            clearTimeout(node._crea_load_timer);
            node._crea_load_timer = null;
        }
        node._crea_is_restored = true;

        const jsonWidget = node.widgets.find(w => w.name === "__csv_json");
        if (jsonWidget && jsonWidget.value && jsonWidget.value !== "{}") {
            try {
                const savedConfig = JSON.parse(jsonWidget.value);
                const targetKeys = Object.keys(savedConfig);

                cleanupWidgets(node, targetKeys);

                node._crea_dynamicValues = savedConfig;
                const { fileMap } = await getCsvMapping();

                for (const [label, val] of Object.entries(savedConfig)) {
                    if (fileMap[label]) await syncComboWidget(node, label, val, fileMap[label]);
                }
                updateNodeSize(node);
            } catch (e) { console.error("JSON error", e); }
        } else {
            await loadDefaultConfig(node);
        }
    }
});