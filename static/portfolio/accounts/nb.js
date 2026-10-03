/* Shared behaviour for every page under the accounts area (login, register,
   profile dashboard, password recovery). One file so the toggle logic
   isn't copy-pasted into five different templates. */
(function () {
  function toggle(btn) {
    var wrap = btn.closest('.nb-input-wrap');
    var input = wrap && wrap.querySelector('input');
    if (!input) return;
    var showing = input.type === 'text';
    input.type = showing ? 'password' : 'text';
    btn.setAttribute('aria-pressed', String(!showing));
    btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.nb-pw-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () { toggle(btn); });
    });
  });
})();
