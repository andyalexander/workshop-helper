// The token input's one keystroke: ⌫ on an empty box drops the last chip
// (spec §9).
//
// This creates no control of its own. The chip already carries a link that
// removes it, and the box carries that same href in `data-drop-last` — all this
// does is bind a key to a link that works when clicked. With JavaScript off you
// lose the shortcut and nothing else, which is the rule the whole shell is built
// to (ADR-0002).
document.addEventListener("keydown", function (event) {
  if (event.key !== "Backspace") return;
  var box = event.target;
  if (box.id !== "filter-q" || box.value !== "") return;
  var href = box.getAttribute("data-drop-last");
  if (!href) return;
  event.preventDefault();
  window.location.assign(href);
});
