// SecureShare frontend behavior.
// Note: CSP is script-src 'self', so everything lives in this file — no inline JS.

document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  // ---- 1. Auto-submit 6-digit TOTP inputs ----
  document.querySelectorAll("input[data-autosubmit]").forEach((inp) => {
    inp.addEventListener("input", () => {
      // Recovery codes contain a dash; only strip non-digits for pure numeric input.
      const numericOnly = inp.value.replace(/\D/g, "");
      if (/^\d*$/.test(inp.value.replace(/ /g, ""))) {
        inp.value = numericOnly.slice(0, 6);
        if (inp.value.length === 6) inp.form.submit();
      }
    });
  });

  // ---- 2. Confirm dialogs for destructive forms (delete / revoke) ----
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // ---- 3. Copy-to-clipboard buttons (share links) ----
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const text = btn.dataset.copy;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = "Copied!";
      } catch {
        // Fallback for older browsers / non-secure contexts
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
        btn.textContent = "Copied!";
      }
      setTimeout(() => (btn.textContent = "Copy"), 1500);
    });
  });

  // ---- 4. Drag-and-drop upload with progress bar ----
  const zone = document.getElementById("dropzone");
  if (!zone) return;

  const input = document.getElementById("file-input");
  const bar = document.getElementById("upload-progress");
  const status = document.getElementById("upload-status");
  const MAX_BYTES = 100 * 1024 * 1024; // matches server MAX_CONTENT_LENGTH

  function upload(file) {
    if (file.size > MAX_BYTES) {
      status.textContent = `"${file.name}" exceeds the 100 MB limit.`;
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/upload");
    xhr.setRequestHeader("X-CSRFToken", csrfToken);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        bar.style.width = Math.round((e.loaded / e.total) * 100) + "%";
      }
    });
    xhr.onload = () => {
      if (xhr.status < 400) {
        status.textContent = "Encrypted and stored. Refreshing…";
        window.location.reload();
      } else {
        status.textContent = "Upload failed. Please try again.";
        bar.style.width = "0";
      }
    };
    xhr.onerror = () => {
      status.textContent = "Network error during upload.";
      bar.style.width = "0";
    };

    status.textContent = `Uploading & encrypting "${file.name}"…`;
    xhr.send(formData);
  }

  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => {
    if (input.files[0]) upload(input.files[0]);
  });

  ["dragover", "dragenter"].forEach((ev) =>
    zone.addEventListener(ev, (e) => {
      e.preventDefault();
      zone.classList.add("drag");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    zone.addEventListener(ev, (e) => {
      e.preventDefault();
      zone.classList.remove("drag");
    })
  );
  zone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  });
});
