import "./styles/main.css";
import "./login.ts";


fetch("/src/components/nav.html")
  .then(r => r.text())
  .then(html => {
    document.getElementById("site-nav")!.innerHTML = html;
  });