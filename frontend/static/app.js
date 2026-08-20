'use strict';

/**
 * StegoCrypt frontend logic.
 * Vanilla JS, no build step. Talks to /api/capacity, /api/encode, /api/decode.
 *
 * Security note: never console.log password/message contents.
 */

/* ---------------------------------------------------------------------- */
/* Constants + helpers                                                     */
/* ---------------------------------------------------------------------- */

const BLOCK_SIZE = 16;
const SALT_SIZE = 16;
const IV_SIZE = 16;
const MAC_SIZE = 32;

/** Mirrors api/routes.py's MAX_IMAGE_BYTES / MAX_MESSAGE_BYTES. */
const MAX_IMAGE_BYTES = 25 * 1024 * 1024;
const MAX_MESSAGE_BYTES = 1 * 1024 * 1024;

/** Mirrors core.crypto.encrypted_length on the backend. */
function encryptedLength(byteLen) {
  const paddedLen = (Math.floor(byteLen / BLOCK_SIZE) + 1) * BLOCK_SIZE;
  return SALT_SIZE + IV_SIZE + paddedLen + MAC_SIZE;
}

function utf8ByteLength(str) {
  return new TextEncoder().encode(str).length;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} bayt`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(2)} MB`;
}

function qs(id) {
  return document.getElementById(id);
}

function show(el) {
  el.classList.remove('hidden');
}

function hide(el) {
  el.classList.add('hidden');
}

/**
 * Shows a fallback error note (and hides the broken image) if imgEl fails to
 * load, and clears it again once a subsequent valid image loads.
 */
function guardImagePreview(imgEl, errorNoteEl) {
  imgEl.addEventListener('error', () => {
    hide(imgEl);
    show(errorNoteEl);
  });
  imgEl.addEventListener('load', () => {
    show(imgEl);
    hide(errorNoteEl);
  });
}

const ICON_ERROR = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5 shrink-0 mt-0.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m0 3h.008v.008H12v-.008ZM21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>`;
const ICON_SUCCESS = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-5 h-5 shrink-0 mt-0.5" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m9 12.75 2.25 2.25 4.5-4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>`;

/**
 * Attempts to parse a fetch Response body as our standard error shape
 * `{ detail, error_type }`. Falls back to a generic message if parsing fails.
 */
async function parseErrorResponse(response) {
  try {
    const data = await response.json();
    if (data && typeof data.detail === 'string') {
      return { detail: data.detail, errorType: data.error_type || null };
    }
  } catch (_err) {
    /* body wasn't JSON — fall through to generic message */
  }
  return {
    detail: `Beklenmeyen bir hata olustu (HTTP ${response.status}).`,
    errorType: null,
  };
}

/* ---------------------------------------------------------------------- */
/* Tabs                                                                     */
/* ---------------------------------------------------------------------- */

function initTabs() {
  const tabEncode = qs('tab-encode');
  const tabDecode = qs('tab-decode');
  const panelEncode = qs('panel-encode');
  const panelDecode = qs('panel-decode');

  const activeClasses = ['bg-amber', 'text-bg'];
  const inactiveClasses = ['text-slate-200', 'hover:bg-white/5'];

  function activate(tab, panel, otherTab, otherPanel) {
    tab.setAttribute('aria-selected', 'true');
    tab.classList.add(...activeClasses);
    tab.classList.remove(...inactiveClasses);

    otherTab.setAttribute('aria-selected', 'false');
    otherTab.classList.remove(...activeClasses);
    otherTab.classList.add(...inactiveClasses);

    show(panel);
    hide(otherPanel);
  }

  tabEncode.addEventListener('click', () => activate(tabEncode, panelEncode, tabDecode, panelDecode));
  tabDecode.addEventListener('click', () => activate(tabDecode, panelDecode, tabEncode, panelEncode));
}

/* ---------------------------------------------------------------------- */
/* Encode panel                                                            */
/* ---------------------------------------------------------------------- */

function initEncodePanel() {
  const form = qs('encode-form');
  const imageInput = qs('encode-image');
  const imageLabel = qs('encode-image-label');
  const previewWrap = qs('encode-preview-wrap');
  const previewImg = qs('encode-preview');
  const capacityText = qs('encode-capacity');
  const capacityErrorText = qs('encode-capacity-error');

  const messageInput = qs('encode-message');
  const byteCounter = qs('encode-byte-counter');
  const capacityWarning = qs('encode-capacity-warning');

  const passwordInput = qs('encode-password');
  const passwordConfirmInput = qs('encode-password-confirm');
  const passwordMismatch = qs('encode-password-mismatch');

  const submitBtn = qs('encode-submit');
  const submitSpinner = qs('encode-submit-spinner');
  const submitLabel = qs('encode-submit-label');
  const loadingNote = qs('encode-loading-note');

  const errorBanner = qs('encode-error');
  const successBanner = qs('encode-success');

  const resultWrap = qs('encode-result-wrap');
  const resultImg = qs('encode-result-image');
  const downloadLink = qs('encode-download-link');

  let capacityBytes = null;
  let previewObjectUrl = null;
  let resultObjectUrl = null;

  function clearBanners() {
    hide(errorBanner);
    errorBanner.textContent = '';
    hide(successBanner);
    successBanner.innerHTML = '';
  }

  function showError(message) {
    hide(successBanner);
    errorBanner.innerHTML = '';
    const icon = document.createElement('span');
    icon.innerHTML = ICON_ERROR;
    const text = document.createElement('span');
    text.textContent = message;
    errorBanner.appendChild(icon.firstElementChild);
    errorBanner.appendChild(text);
    show(errorBanner);
  }

  function showSuccess(message) {
    hide(errorBanner);
    successBanner.innerHTML = '';
    const icon = document.createElement('span');
    icon.innerHTML = ICON_SUCCESS;
    const text = document.createElement('span');
    text.textContent = message;
    successBanner.appendChild(icon.firstElementChild);
    successBanner.appendChild(text);
    show(successBanner);
  }

  /**
   * Recomputes validity, updates the warning/mismatch UI, and returns whether
   * the form is currently submittable. This is the single source of truth for
   * "can submit" — the submit handler re-checks this same result rather than
   * a separate, weaker set of conditions, so disabling the button and
   * rejecting a submit can never drift apart.
   */
  function updateSubmitEnabled() {
    const messageBytes = utf8ByteLength(messageInput.value);
    const needed = encryptedLength(messageBytes);

    let overCapacity = false;
    if (capacityBytes !== null && needed > capacityBytes) {
      overCapacity = true;
      capacityWarning.textContent = `Mesaj cok buyuk: sifrelenmis boyut ${formatBytes(needed)}, gorsel en fazla ${formatBytes(capacityBytes)} tasiyabilir.`;
      show(capacityWarning);
    } else {
      hide(capacityWarning);
    }

    const passwordsFilled = passwordInput.value.length > 0 && passwordConfirmInput.value.length > 0;
    const passwordsMatch = passwordInput.value === passwordConfirmInput.value;
    if (passwordsFilled && !passwordsMatch) {
      show(passwordMismatch);
    } else {
      hide(passwordMismatch);
    }

    const file = imageInput.files && imageInput.files[0];
    const hasImage = Boolean(file);
    const hasMessage = messageBytes > 0;
    const hasPassword = passwordInput.value.length > 0;
    const messageTooLarge = messageBytes > MAX_MESSAGE_BYTES;
    const imageTooLarge = Boolean(file && file.size > MAX_IMAGE_BYTES);

    const canSubmit =
      hasImage &&
      hasMessage &&
      hasPassword &&
      passwordsMatch &&
      passwordsFilled &&
      !overCapacity &&
      !messageTooLarge &&
      !imageTooLarge &&
      capacityBytes !== null;

    submitBtn.disabled = !canSubmit;
    return canSubmit;
  }

  byteCounter.dataset.needsCapacity = 'true';

  function updateByteCounter() {
    const messageBytes = utf8ByteLength(messageInput.value);
    const needed = encryptedLength(messageBytes);
    if (capacityBytes !== null) {
      byteCounter.textContent = `${messageBytes} bayt (sifrelenmis: ${formatBytes(needed)} / ${formatBytes(capacityBytes)})`;
    } else {
      byteCounter.textContent = `${messageBytes} bayt`;
    }
  }

  imageInput.addEventListener('change', async () => {
    clearBanners();
    hide(resultWrap);
    capacityBytes = null;
    hide(capacityErrorText);
    capacityErrorText.textContent = '';

    const file = imageInput.files && imageInput.files[0];
    if (!file) {
      imageLabel.textContent = 'Gorsel secmek icin tiklayin';
      hide(previewWrap);
      updateByteCounter();
      updateSubmitEnabled();
      return;
    }

    imageLabel.textContent = file.name;

    if (previewObjectUrl) {
      URL.revokeObjectURL(previewObjectUrl);
    }
    previewObjectUrl = URL.createObjectURL(file);
    previewImg.src = previewObjectUrl;
    show(previewWrap);

    if (file.size > MAX_IMAGE_BYTES) {
      capacityText.textContent = '';
      capacityErrorText.textContent = `Gorsel cok buyuk (azami ${formatBytes(MAX_IMAGE_BYTES)}).`;
      show(capacityErrorText);
      capacityBytes = null;
      updateByteCounter();
      updateSubmitEnabled();
      return;
    }

    capacityText.textContent = 'Kapasite hesaplaniyor...';

    try {
      const formData = new FormData();
      formData.append('image', file);
      const response = await fetch('/api/capacity', { method: 'POST', body: formData });

      if (!response.ok) {
        const err = await parseErrorResponse(response);
        capacityText.textContent = '';
        capacityErrorText.textContent = err.detail;
        show(capacityErrorText);
        capacityBytes = null;
        updateByteCounter();
        updateSubmitEnabled();
        return;
      }

      const data = await response.json();
      if (typeof data.capacity_bytes !== 'number') {
        throw new Error('Beklenmeyen yanit sekli');
      }
      capacityBytes = data.capacity_bytes;
      capacityText.textContent = `Kapasite: ${formatBytes(capacityBytes)}`;
    } catch (_err) {
      capacityText.textContent = '';
      capacityErrorText.textContent = 'Kapasite hesaplanamadi: sunucuya ulasilamiyor veya beklenmeyen bir yanit alindi.';
      show(capacityErrorText);
      capacityBytes = null;
    }

    updateByteCounter();
    updateSubmitEnabled();
  });

  messageInput.addEventListener('input', () => {
    updateByteCounter();
    updateSubmitEnabled();
  });
  passwordInput.addEventListener('input', updateSubmitEnabled);
  passwordConfirmInput.addEventListener('input', updateSubmitEnabled);

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    imageInput.disabled = isLoading;
    messageInput.disabled = isLoading;
    passwordInput.disabled = isLoading;
    passwordConfirmInput.disabled = isLoading;

    if (isLoading) {
      show(submitSpinner);
      submitLabel.textContent = 'Sifreleniyor...';
      show(loadingNote);
    } else {
      hide(submitSpinner);
      submitLabel.textContent = 'Sifrele ve Gizle';
      hide(loadingNote);
      updateSubmitEnabled();
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearBanners();
    hide(resultWrap);

    const file = imageInput.files && imageInput.files[0];
    if (!updateSubmitEnabled()) {
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('message', messageInput.value);
      formData.append('password', passwordInput.value);

      const response = await fetch('/api/encode', { method: 'POST', body: formData });

      if (!response.ok) {
        const err = await parseErrorResponse(response);
        showError(err.detail);
        return;
      }

      const blob = await response.blob();

      if (resultObjectUrl) {
        URL.revokeObjectURL(resultObjectUrl);
      }
      resultObjectUrl = URL.createObjectURL(blob);

      resultImg.src = resultObjectUrl;
      show(resultWrap);

      downloadLink.href = resultObjectUrl;
      downloadLink.download = 'stego.png';
      downloadLink.click();

      showSuccess('Mesaj basariyla gizlendi. Indirme baslatildi (stego.png).');
    } catch (_err) {
      showError('Sunucuya ulasilamadi. Baglantinizi kontrol edip tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  });

  guardImagePreview(previewImg, qs('encode-preview-error'));
  guardImagePreview(resultImg, qs('encode-result-error'));

  updateByteCounter();
  updateSubmitEnabled();
}

/* ---------------------------------------------------------------------- */
/* Decode panel                                                            */
/* ---------------------------------------------------------------------- */

function initDecodePanel() {
  const form = qs('decode-form');
  const imageInput = qs('decode-image');
  const imageLabel = qs('decode-image-label');
  const previewWrap = qs('decode-preview-wrap');
  const previewImg = qs('decode-preview');

  const passwordInput = qs('decode-password');

  const submitBtn = qs('decode-submit');
  const submitSpinner = qs('decode-submit-spinner');
  const submitLabel = qs('decode-submit-label');
  const loadingNote = qs('decode-loading-note');

  const errorBanner = qs('decode-error');

  const resultWrap = qs('decode-result-wrap');
  const resultMessage = qs('decode-result-message');
  const copyBtn = qs('decode-copy-btn');
  const copyLabel = qs('decode-copy-label');

  let previewObjectUrl = null;
  let copyResetTimer = null;

  function clearBanner() {
    hide(errorBanner);
    errorBanner.textContent = '';
  }

  function showError(message) {
    errorBanner.innerHTML = '';
    const icon = document.createElement('span');
    icon.innerHTML = ICON_ERROR;
    const text = document.createElement('span');
    text.textContent = message;
    errorBanner.appendChild(icon.firstElementChild);
    errorBanner.appendChild(text);
    show(errorBanner);
  }

  imageInput.addEventListener('change', () => {
    clearBanner();
    hide(resultWrap);
    resultMessage.value = '';

    const file = imageInput.files && imageInput.files[0];
    if (!file) {
      imageLabel.textContent = 'Gorsel secmek icin tiklayin';
      hide(previewWrap);
      return;
    }

    imageLabel.textContent = file.name;

    if (previewObjectUrl) {
      URL.revokeObjectURL(previewObjectUrl);
    }
    previewObjectUrl = URL.createObjectURL(file);
    previewImg.src = previewObjectUrl;
    show(previewWrap);
  });

  guardImagePreview(previewImg, qs('decode-preview-error'));

  function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    imageInput.disabled = isLoading;
    passwordInput.disabled = isLoading;

    if (isLoading) {
      show(submitSpinner);
      submitLabel.textContent = 'Cozuluyor...';
      show(loadingNote);
    } else {
      hide(submitSpinner);
      submitLabel.textContent = 'Cikar ve Coz';
      hide(loadingNote);
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearBanner();
    hide(resultWrap);

    const file = imageInput.files && imageInput.files[0];
    if (!file) {
      showError('Lutfen bir stego gorseli secin.');
      return;
    }
    if (file.size > MAX_IMAGE_BYTES) {
      showError(`Gorsel cok buyuk (azami ${formatBytes(MAX_IMAGE_BYTES)}).`);
      return;
    }
    if (!passwordInput.value) {
      showError('Lutfen parolayi girin.');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('password', passwordInput.value);

      const response = await fetch('/api/decode', { method: 'POST', body: formData });

      if (!response.ok) {
        const err = await parseErrorResponse(response);
        showError(err.detail);
        return;
      }

      const data = await response.json();
      if (typeof data.message !== 'string') {
        throw new Error('Beklenmeyen yanit sekli');
      }
      resultMessage.value = data.message;
      show(resultWrap);
      copyLabel.textContent = 'Kopyala';
    } catch (_err) {
      showError('Sunucuya ulasilamadi veya beklenmeyen bir yanit alindi. Baglantinizi kontrol edip tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  });

  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(resultMessage.value);
      copyLabel.textContent = 'Kopyalandi!';
    } catch (_err) {
      resultMessage.select();
      copyLabel.textContent = 'Secildi, Ctrl+C ile kopyalayin';
    }

    if (copyResetTimer) {
      clearTimeout(copyResetTimer);
    }
    copyResetTimer = setTimeout(() => {
      copyLabel.textContent = 'Kopyala';
    }, 2000);
  });
}

/* ---------------------------------------------------------------------- */
/* Bootstrap                                                                */
/* ---------------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initEncodePanel();
  initDecodePanel();
});
