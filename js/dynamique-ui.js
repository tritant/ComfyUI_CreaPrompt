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
            //console.log("🧭 Fin période de refresh (isRefresh = false)");
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
            const jsonIndex = node.widgets.indexOf(jsonWidget);

            function updateCsvJson() {
                const jsonText = JSON.stringify(node._crea_dynamicValues);
                if (node.widgets_values) node.widgets_values[jsonIndex] = jsonText;
                node.widgets[jsonIndex].value = jsonText;
                node.graph?.setDirtyCanvas(true, true);
            }

            node._crea_updateCsvJson = updateCsvJson;
            node._crea_jsonIndex = jsonIndex;
            node._crea_dynamicValues = {};

            for (const w of node.widgets) {
                if (w.name === "__csv_json") {
                    console.log("🔒 Widget __csv_json trouvé dans node.widgets");
                    w.readonly = true;
                    w.disabled = true;
                    if (w.options) {
                        w.options.readonly = true;
                        w.options.disabled = true;
                        w.options.hidden = true;
                    }

                    // 🔬 Diagnostic avancé : afficher tous les input et textarea avec leurs noms
                    console.log("🔬 Diagnostic : recherche manuelle de tous les input et textarea");
                    document.querySelectorAll("input, textarea").forEach((el, i) => {
                        console.log(`#${i}`, el.tagName, el.name, el.value, el);
                    });

                    // ✅ Masquage par détection du contenu JSON probable (avec retry même si vide au début)
                    let attempt = 0;
                    const hideByTextContent = () => {
                        const textareas = document.querySelectorAll("textarea");
                        for (const t of textareas) {
                            const val = t.value.trim();
                            const wrapper = t.closest("div");
                            if (val.startsWith("{") && val.includes(":") && wrapper) {
                                wrapper.style.display = "none";
                                wrapper.style.visibility = "hidden";
                                wrapper.style.height = "0px";
                                wrapper.style.padding = "0";
                                wrapper.style.margin = "0";
								console.log("🧼 Widget __csv_json masqué par analyse de contenu (tentative", attempt, ")");
                                return;
                            }
                        }
                        if (attempt < 50) {
                            attempt++;
                            requestAnimationFrame(hideByTextContent);
                        } else {
                            console.warn("⏳ Abandon du masquage de __csv_json après 50 tentatives.");
                        }
                    };
                    setTimeout(() => hideByTextContent(), 100);

                    break;
                }
            }


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
                    // 🔄 Fermer l'ancien menu s'il existe
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

                    // ❌ Bouton pour fermer le menu
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

                                // 🧼 Supprimer tous les widgets combo existants
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
                                //alert(`✅ Preset "${label}" chargé.`);
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
                                //alert(`✅ Preset \"${label}\" supprimé.`);
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
                        console.log("🧹 Combo supprimé:", name);
                    }
                    node._crea_updateCsvJson?.();
                    node.widgets_changed = true;
                    node.onResize?.();
                }, { serialize: false });
            }

            // 🗑️ Bouton Remove a Category
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
                        node.onResize?.();
                        menu.remove();
                        //console.log("🗑️ Combo supprimé via menu:", name);
                    };
                    item.onmouseover = () => item.style.background = "#555";
                    item.onmouseout = () => item.style.background = "#222";
                    menu.appendChild(item);
                });
                document.body.appendChild(menu);
            }, { serialize: false });

            waitForJsonToBeReady(node, jsonIndex);

            setTimeout(() => {
                const jsonRaw = node.widgets?.[jsonIndex]?.value;
                const now = performance.now();
                const isRefresh = (now - window._crea_prompt_launch_time) < 3000;

                //console.log("⏱️ Post-création — jsonRaw =", jsonRaw);
                //console.log("⏱️ Post-création — isRefresh =", isRefresh);

                if (!isRefresh) {
                    //console.log("📦 Chargement des combos par défaut (reload)");
                    tryLoadDefaultCombos(node);
                } else {
                    //console.log("🔁 Node restauré (refresh) — preset ignoré");
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
                    //console.error("❌ Erreur de récupération CSV :", err);
                    alert("Error when try to find CSV files.");
                }
            }, { serialize: false });

            button.label = "➕ Add a Category";
        };
    }
});

function waitForJsonToBeReady(node, jsonIndex) {
    let attempts = 0;
    const check = () => {
        const raw = node.widgets[jsonIndex]?.value;
        if (!raw || raw.trim() === "" || raw.trim() === "{}") {
            attempts++;
            if (attempts < 50) return setTimeout(check, 100);
            console.warn("⏳ Échec : __csv_json toujours vide après 5s");
            return;
        }

        try {
            const parsed = JSON.parse(raw);
            node._crea_dynamicValues = parsed;

            const rawIsJson = typeof raw === "string" && raw.trim().startsWith("{") && raw.includes(":");
            if (rawIsJson && !node._crea_restored) {
                node._crea_restored = true;
                window.creaPromptRestores.push(node);
                console.log("✅ Node CreaPrompt prêt pour restauration :", parsed);
            } else {
                console.log("ℹ️ JSON présent, mais pas une vraie restauration (cas reload)");
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

    if (!nodes.length) {
        console.warn("⏳ Aucun node CreaPrompt détecté après 5s — restauration annulée");
        return;
    }

    window._crea_prompt_refresh_done = true;
    console.log(`🔁 Début de la restauration CreaPrompt (tentative ${attempt})`);

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
            console.log("⏩ Des combos existent déjà, skip default_combos.txt");
            return;
        }

        const res = await fetch("/custom_nodes/creaprompt/presets/default_combos.txt");
        if (!res.ok) {
            console.warn("⚠️ default_combos.txt non trouvé");
            return;
        }

        const text = await res.text();
        const labels = text.split("\n").map(l => l.trim()).filter(Boolean);
        //console.log("📥 Contenu du fichier default_combos.txt :", labels);

        const resList = await fetch("/custom_nodes/creaprompt/csv_list");
        if (!resList.ok) {
            console.warn("⚠️ Unable to load csv_list");
            return;
        }
        const allFiles = await resList.json();

        const fileMap = {};
        for (const f of allFiles) {
            const base = f.replace(/^\d+_\d*/, "").replace(/\.csv$/, "");
            fileMap[base] = f;
        }

        for (const label of labels) {
            console.log(`🔎 Traitement du label "${label}"`);

            if (node.widgets.some(w => w.name === label)) {
                console.warn(`⏩ Le combo "${label}" est déjà présent, ignoré.`);
                continue;
            }

            const file = fileMap[label];
            if (!file) {
                console.warn(`⚠️ Fichier CSV introuvable pour "${label}"`);
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

            console.log(`✅ Combo ajouté : ${label} (depuis ${file})`);
        }

        node._crea_updateCsvJson?.();
        node.widgets_changed = true;
        node.onResize?.();
        console.log("📦 Combos par défaut injectés depuis default_combos.txt");
    } catch (e) {
        console.warn("⚠️ Erreur lors du chargement des combos par défaut :", e);
    }
}

window._crea_prompt_refresh_done = true;
waitAndRestore();
