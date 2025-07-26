import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

window.creaPromptRestores = [];
window._crea_prompt_launch_time = performance.now();

if (!window._crea_prompt_first_boot_done) {
    window._crea_prompt_first_boot_done = true;
    window._crea_prompt_is_refresh = true;

    window.addEventListener("DOMContentLoaded", () => {
        setTimeout(() => {
            window._crea_prompt_is_refresh = false;
        }, 2000);
    });
}

window._crea_prompt_refresh_done = false;

app.registerExtension({
    name: "CreaPrompt_UI",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CreaPrompt_0") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            const node = this;
            let clickX = 100;
            let clickY = 100;
            
            const jsonWidget = node.widgets.find(w => w.name === "__csv_json");

            // --- SOLUTION FINALE : FUSION DES DEUX TECHNIQUES ---
            if (jsonWidget) {
                // 1. On dit au CANVAS de supprimer l'espace alloué au widget.
                jsonWidget.computeSize = () => [0, -4]; // Le -4 est important pour la marge.

                // 2. On dit au navigateur de masquer l'élément HTML pour supprimer les bordures.
                setTimeout(() => {
                    if (jsonWidget.inputEl && jsonWidget.inputEl.parentElement) {
                        jsonWidget.inputEl.parentElement.style.display = "none";
                    }
                }, 0);
            }
            
            function updateCsvJson() {
                const jsonText = JSON.stringify(node._crea_dynamicValues);
                if (jsonWidget) {
                    jsonWidget.value = jsonText;
                }
                node.graph?.setDirtyCanvas(true, true);
            }

            node._crea_updateCsvJson = updateCsvJson;
            node._crea_dynamicValues = {};
            
            // Le reste de votre code est inchangé.
            
            // 💾 Preset Name + Save Preset
            if (!node._crea_savePresetAdded) {
                node._crea_savePresetAdded = true;
                node.addWidget("text", "📁 Enter Preset Name for Saving", "", (val) => {
                    node._crea_presetName = val.trim();
                });
                node.addWidget("button", "💾 Save Categories Preset", "", async () => {
                    const name = node._crea_presetName;
                    const content = JSON.stringify(node._crea_dynamicValues, null, 2);
                    if (!name || name.length < 2) {
                        alert("❗Please enter a preset name.");
                        return;
                    }
                    try {
                        const res = await fetch("/custom_nodes/creaprompt/save_preset", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ name, content })
                        });
                        if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`);
                        alert(`✅ Preset "${name}" saved successfully !`);
                    } catch (e) {
                        alert("❌ Error saving preset : " + e.message);
                    }
                }, { serialize: false });
            }
            
            // 📂 Load Preset
            node.addWidget("button", "📂 Load Categories Preset", "", async () => {
                try {
                    if (node._crea_presetMenu) {
                        node._crea_presetMenu.remove();
                        node._crea_presetMenu = null;
                    }

                    if (window.event) {
                        clickX = window.event.clientX;
                        clickY = window.event.clientY;
                    }

                    const res = await fetch("/custom_nodes/creaprompt/presets_list");
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const files = await res.json();
                    const txtFiles = files.filter(f => f.endsWith(".txt") && f !== "default_combos.txt");
                    if (!txtFiles.length) {
                        alert("No preset found in /presets.");
                        return;
                    }
                    const menu = document.createElement("div");
                    Object.assign(menu.style, {
                        position: "fixed",
                        left: `${clickX}px`,
                        top: `${clickY}px`,
                        background: "#222",
                        color: "#fff",
                        padding: "5px",
                        border: "1px solid #444",
                        zIndex: 9999
                    });

                    const closeItem = document.createElement("div");
                    closeItem.innerText = "❌ Close menu";
                    closeItem.style.padding = "4px";
                    closeItem.style.cursor = "pointer";
                    closeItem.style.fontWeight = "bold";
                    closeItem.style.borderBottom = "1px solid #ccc";
                    closeItem.addEventListener("click", () => {
                        document.body.removeChild(menu);
                        node._crea_presetMenu = null;
                    });
                    menu.appendChild(closeItem);

                    txtFiles.forEach(file => {
                        const label = file.replace(/\.txt$/, "");
                        const item = document.createElement("div");
                        item.textContent = label;
                        item.style.padding = "4px 8px";
                        item.style.cursor = "pointer";
                        item.onclick = async () => {
                            const r = await fetch(`/custom_nodes/creaprompt/presets/${file}`);
                            const content = await r.text();
                            try {
                                const parsed = JSON.parse(content);

                                const existingLabels = Object.keys(node._crea_dynamicValues || {});
                                for (const name of existingLabels) {
                                    const widgetsToRemove = node.widgets.filter(w => w.name === name);
                                    for (const w of widgetsToRemove) {
                                        const i = node.widgets.indexOf(w);
                                        if (i !== -1) {
                                            node.widgets.splice(i, 1);
                                            if (node.widgets_values) node.widgets_values.splice(i, 1);
                                        }
                                    }
                                }

                                node._crea_dynamicValues = parsed;

                                const resList = await fetch("/custom_nodes/creaprompt/csv_list");
                                if (!resList.ok) throw new Error("Error csv_list");
                                const allFiles = await resList.json();
                                const fileMap = {};
                                for (const f of allFiles) {
                                    const base = f.replace(/^\d+_\d*/, "").replace(/\.csv$/, "");
                                    fileMap[base] = f;
                                }

                                for (const [comboLabel, val] of Object.entries(parsed)) {
                                    const file = fileMap[comboLabel];
                                    if (!file) continue;

                                    const res2 = await fetch(`/custom_nodes/creaprompt/csv/${file}`);
                                    if (!res2.ok) continue;

                                    const text = await res2.text();
                                    const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
                                    const values = ["disabled", "🎲random", ...lines];

                                    node.addWidget("combo", comboLabel, val, (newVal) => {
                                        node._crea_dynamicValues[comboLabel] = newVal;
                                        node._crea_updateCsvJson?.();
                                    }, {
                                        values: values,
                                        serialize: false
                                    });
                                }

                                node._crea_updateCsvJson?.();
                                node.widgets_changed = true;
                                node.onResize?.();
                            } catch (e) {
                                alert("❌ Error when loading : " + e.message);
                            }
                            menu.remove();
                            node._crea_presetMenu = null;
                        };
                        item.onmouseover = () => item.style.background = "#555";
                        item.onmouseout = () => item.style.background = "#222";
                        menu.appendChild(item);
                    });

                    document.body.appendChild(menu);
                    node._crea_presetMenu = menu;
                } catch (err) {
                    alert("❌ Error when loading presets : " + err.message);
                }
            });


            // 🗑️ Delete Preset
            node.addWidget("button", "🗑️ Delete Categories Preset", "", async () => {
                let clickX = 100;
                let clickY = 100;
                if (window.event) {
                    clickX = window.event.clientX;
                    clickY = window.event.clientY;
                }

                const existingMenu = document.getElementById("crea_delete_preset_menu");
                if (existingMenu) existingMenu.remove();

                try {
                    const res = await fetch("/custom_nodes/creaprompt/presets_list");
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const files = await res.json();
                    const txtFiles = files.filter(f => f.endsWith(".txt") && f !== "default_combos.txt");

                    if (!txtFiles.length) {
                        alert("No preset found.");
                        return;
                    }

                    const menu = document.createElement("div");
                    menu.id = "crea_delete_preset_menu";
                    Object.assign(menu.style, {
                        position: "fixed",
                        left: `${clickX}px`,
                        top: `${clickY}px`,
                        background: "#2c2c2c",
                        color: "#fff",
                        padding: "5px",
                        border: "1px solid #444",
                        zIndex: 9999,
                        fontFamily: "sans-serif",
                        fontSize: "13px"
                    });

                    const closeItem = document.createElement("div");
                    closeItem.textContent = "❌ Close menu";
                    Object.assign(closeItem.style, {
                        padding: "6px 12px",
                        cursor: "pointer",
                        fontWeight: "bold",
                        borderBottom: "1px solid #555"
                    });
                    closeItem.onclick = () => menu.remove();
                    menu.appendChild(closeItem);

                    txtFiles.forEach(file => {
                        const item = document.createElement("div");
                        const label = file.replace(/\.txt$/, "");
                        item.textContent = label;
                        item.style.padding = "4px 12px";
                        item.style.cursor = "pointer";
                        item.onclick = async () => {
                            if (!confirm(`Do you really want to delete the preset \"${label}\" ?`)) return;
                            try {
                                const resDel = await fetch(`/custom_nodes/creaprompt/delete_preset/${file}`, {
                                    method: "DELETE"
                                });
                                if (!resDel.ok) throw new Error(`HTTP ${resDel.status}`);
                                menu.remove();
                            } catch (e) {
                                alert("❌ Delete error : " + e.message);
                            }
                        };
                        item.onmouseover = () => item.style.background = "#555";
                        item.onmouseout = () => item.style.background = "#2c2c2c";
                        menu.appendChild(item);
                    });

                    document.body.appendChild(menu);
                } catch (e) {
                    alert("❌ Error when loading presets : " + e.message);
                }
            }, { serialize: false });
            
            // 🧹 Remove All Categories
            if (!node._crea_removeAllAdded) {
                node._crea_removeAllAdded = true;
                node.addWidget("button", "🧹 Remove All Categories", "", () => {
                    const names = Object.keys(node._crea_dynamicValues || {});
                    if (!names.length) return alert("Aucun combo à supprimer.");
                    for (const name of names) {
                        const widgetsToRemove = node.widgets.filter(w => w.name === name);
                        for (const w of widgetsToRemove) {
                            const i = node.widgets.indexOf(w);
                            if (i !== -1) {
                                node.widgets.splice(i, 1);
                                if (node.widgets_values) node.widgets_values.splice(i, 1);
                            }
                        }
                        delete node._crea_dynamicValues[name];
                    }
                    node._crea_updateCsvJson?.();
                    node.widgets_changed = true;
                    const newSize = node.computeSize();
		            node.size[1] = newSize[1];
                    node.onResize?.(node.size);
                    node.graph.setDirtyCanvas(true, true);
                }, { serialize: false });
            }

            // ➖ Bouton Remove a Category
            node.addWidget("button", "➖ Remove a Category", "", () => {
                const existing = Object.keys(node._crea_dynamicValues || {});
                if (!existing.length) return alert("No combo to delete.");

                const oldMenu = document.getElementById("crea_remove_combo_menu");
                if (oldMenu) document.body.removeChild(oldMenu);

                let clickX = 100;
                let clickY = 100;
                if (window.event) {
                    clickX = window.event.clientX;
                    clickY = window.event.clientY;
                }

                const menu = document.createElement("div");
                menu.id = "crea_remove_combo_menu";
                const closeItem = document.createElement("div");
                closeItem.innerText = "❌ Close menu";
                closeItem.style.padding = "4px";
                closeItem.style.cursor = "pointer";
                closeItem.style.fontWeight = "bold";
                closeItem.style.borderBottom = "1px solid #ccc";
                closeItem.addEventListener("click", () => {
                    document.body.removeChild(menu);
                });
                menu.appendChild(closeItem);
                Object.assign(menu.style, {
                    position: "fixed",
                    left: `${clickX}px`,
                    top: `${clickY}px`,
                    background: "#222",
                    color: "#fff",
                    padding: "5px",
                    border: "1px solid #444",
                    zIndex: 9999
                });
                existing.forEach(name => {
                    const item = document.createElement("div");
                    item.textContent = name;
                    item.style.padding = "4px 8px";
                    item.style.cursor = "pointer";
                    item.onclick = () => {
                        const toRemove = node.widgets.filter(w => w.name === name);
                        for (const w of toRemove) {
                            const i = node.widgets.indexOf(w);
                            if (i !== -1) {
                                node.widgets.splice(i, 1);
                                if (node.widgets_values) node.widgets_values.splice(i, 1);
                            }
                        }
                        delete node._crea_dynamicValues[name];
                        node._crea_updateCsvJson?.();
                        node.widgets_changed = true;
						const newSize2 = node.computeSize();
		                node.size[1] = newSize2[1];
                        node.onResize?.(node.size);
                        node.graph.setDirtyCanvas(true, true);
                        menu.remove();
                    };
                    item.onmouseover = () => item.style.background = "#555";
                    item.onmouseout = () => item.style.background = "#222";
                    menu.appendChild(item);
                });
                document.body.appendChild(menu);

            }, { serialize: false });

            waitForJsonToBeReady(node);

            setTimeout(() => {
                const now = performance.now();
                const isRefresh = (now - window._crea_prompt_launch_time) < 3000;

                if (!isRefresh) {
                    tryLoadDefaultCombos(node);
                }
            }, 500);

            const button = node.addWidget("button", "📂 Choose CSV file", "", async () => {
                if (window.event) {
                    clickX = window.event.clientX;
                    clickY = window.event.clientY;
                }

                if (node._csvMenu) {
                    node._csvMenu.remove();
                    node._csvMenu = null;
                }

                try {
                    const res = await fetch("/custom_nodes/creaprompt/csv_list");
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const files = await res.json();
                    const csvFiles = files.filter(f => f.endsWith(".csv"));

                    if (!csvFiles.length) {
                        alert("No CSV file found in /csv.");
                        return;
                    }

                    const menu = document.createElement("div");
                    menu.id = "crea_remove_combo_menu";
                    Object.assign(menu.style, {
                        position: "fixed",
                        left: `${clickX}px`,
                        top: `${clickY}px`,
                        background: "#2c2c2c",
                        color: "#eee",
                        border: "1px solid #666",
                        padding: "4px 0",
                        zIndex: 1000,
                        fontFamily: "sans-serif",
                        fontSize: "13px",
                        minWidth: "200px",
                        maxHeight: "40vh",
                        overflowY: "auto",
                        boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
                        borderRadius: "4px"
                    });

                    const closeItem = document.createElement("div");
                    closeItem.textContent = "❌ Close menu";
                    Object.assign(closeItem.style, {
                        padding: "6px 12px",
                        cursor: "pointer",
                        fontWeight: "bold",
                        borderBottom: "1px solid #555",
                        background: "#2c2c2c",
                        position: "sticky",
                        top: "0",
                        zIndex: "1001"
                    });
                    closeItem.onclick = () => {
                        menu.remove();
                        node._csvMenu = null;
                    };
                    menu.appendChild(closeItem);

                    for (const file of csvFiles) {
                        const label = file.slice(3, -4);
                        if (node.widgets.some(w => w.name === label)) continue;

                        const item = document.createElement("div");
                        item.textContent = label;
                        item.style.padding = "4px 12px";
                        item.style.cursor = "pointer";

                        item.onclick = async () => {
                            menu.remove();
                            node._csvMenu = null;

                            const res2 = await fetch(`/custom_nodes/creaprompt/csv/${file}`);
                            const text = await res2.text();
                            const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
                            const values = ["disabled", "🎲random", ...lines];

                            node._crea_dynamicValues[label] = "disabled";

                            node.addWidget("combo", label, "disabled", (val) => {
                                node._crea_dynamicValues[label] = val;
                                updateCsvJson();
                            }, {
                                values: values,
                                serialize: false
                            });

                            updateCsvJson();
                            node.widgets_changed = true;
                            node.onResize?.();
                        };

                        item.onmouseover = () => item.style.background = "#444";
                        item.onmouseout = () => item.style.background = "transparent";

                        menu.appendChild(item);
                    }

                    document.body.appendChild(menu);
                    node._csvMenu = menu;

                } catch (err) {
                    alert("Error when try to find CSV files.");
                }
            }, { serialize: false });

            button.label = "➕ Add a Category";

        };

    }

});

function waitForJsonToBeReady(node) {
    let attempts = 0;
    const check = () => {
        const widget = node.widgets.find(w => w.name === "__csv_json");
        const raw = widget ? widget.value : null;

        if (!raw || typeof raw !== 'string' || raw.trim() === "" || raw.trim() === "{}") {
            attempts++;
            if (attempts < 50) return setTimeout(check, 100);
            return;
        }

        try {
            const parsed = JSON.parse(raw);
            node._crea_dynamicValues = parsed;

            const rawIsJson = typeof raw === "string" && raw.trim().startsWith("{") && raw.includes(":");
            if (rawIsJson && !node._crea_restored) {
                node._crea_restored = true;
                window.creaPromptRestores.push(node);
            }
        } catch (e) {
            console.warn("❌ JSON __csv_json mal formé ou vide :", raw);
        }
    };
    check();
}


let attempt = 0;
const waitAndRestore = async () => {
    attempt++;
    const nodes = window.creaPromptRestores || [];
    if (!nodes.length && attempt < 50) {
        return setTimeout(waitAndRestore, 100);
    }
    if (!nodes.length) return;

    window._crea_prompt_refresh_done = true;

    const resList = await fetch("/custom_nodes/creaprompt/csv_list");
    if (!resList.ok) return;
    const allFiles = await resList.json();

    const fileMap = {};
    for (const f of allFiles) {
        const base = f.replace(/^\d+_\d*/, "").replace(/\.csv$/, "");
        fileMap[base] = f;
    }

    for (const node of nodes) {
        const dynamicValues = node._crea_dynamicValues || {};
        const updateCsvJson = node._crea_updateCsvJson;

        for (const [label, val] of Object.entries(dynamicValues)) {
            if (node.widgets.some(w => w.name === label)) continue;

            const matchingFile = fileMap[label];
            if (!matchingFile) continue;

            const res = await fetch(`/custom_nodes/creaprompt/csv/${matchingFile}`);
            if (!res.ok) continue;

            const text = await res.text();
            const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
            const values = ["disabled", "🎲random", ...lines];

            node.addWidget("combo", label, val, (newVal) => {
                dynamicValues[label] = newVal;
                updateCsvJson();
            }, {
                values: values,
                serialize: false
            });

            node.widgets_changed = true;
            node.onResize?.();
        }
        updateCsvJson?.();
    }
};

async function tryLoadDefaultCombos(node) {
    try {
        if (Object.keys(node._crea_dynamicValues || {}).length > 0) {
            return;
        }

        const res = await fetch("/custom_nodes/creaprompt/presets/default_combos.txt");
        if (!res.ok) {
            return;
        }

        const text = await res.text();
        const labels = text.split("\n").map(l => l.trim()).filter(Boolean);

        const resList = await fetch("/custom_nodes/creaprompt/csv_list");
        if (!resList.ok) {
            return;
        }
        const allFiles = await resList.json();

        const fileMap = {};
        for (const f of allFiles) {
            const base = f.replace(/^\d+_\d*/, "").replace(/\.csv$/, "");
            fileMap[base] = f;
        }

        for (const label of labels) {
            if (node.widgets.some(w => w.name === label)) {
                continue;
            }

            const file = fileMap[label];
            if (!file) {
                continue;
            }

            const res2 = await fetch(`/custom_nodes/creaprompt/csv/${file}`);
            if (!res2.ok) continue;

            const content = await res2.text();
            const lines = content.split("\n").map(l => l.trim()).filter(Boolean);
            const values = ["disabled", "🎲random", ...lines];

            node._crea_dynamicValues[label] = "disabled";

            node.addWidget("combo", label, "disabled", (val) => {
                node._crea_dynamicValues[label] = val;
                node._crea_updateCsvJson?.();
            }, {
                values: values,
                serialize: false
            });
        }

        node._crea_updateCsvJson?.();
        node.widgets_changed = true;

    } catch (e) {
        console.warn("⚠️ Erreur lors du chargement des combos par défaut :", e);
    }
}

window._crea_prompt_refresh_done = true;
waitAndRestore();