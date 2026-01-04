import { NextRequest, NextResponse } from 'next/server';
import { BACKEND_URL, FRONTEND_URL } from '@/config';

export async function GET() {
  const scriptContent = `(function () {
  const BACKEND_URL = "${BACKEND_URL}";
  const FRONTEND_URL = "${FRONTEND_URL}";

  // Find script with data-widget-id
  let currentScript = null;
  for (const script of document.getElementsByTagName("script")) {
    if (script.dataset.widgetId) {
      currentScript = script;
      break;
    }
  }

  if (!currentScript) {
    console.error("Taimako.AI Widget: Missing data-widget-id on script tag.");
    return;
  }

  const widgetId = currentScript.dataset.widgetId;

  // Main container (launcher + iframe)
  const container = document.createElement("div");
  container.id = "taimako-widget-container";
  container.style.position = "fixed";
  container.style.bottom = "20px";
  container.style.right = "20px";
  container.style.zIndex = "999999";
  container.style.fontFamily = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
  container.style.pointerEvents = "none"; // Allow clicks to pass through container when closed
  document.body.appendChild(container);

  // Fetch widget config
  fetch(\`\${BACKEND_URL}/widgets/config/\${widgetId}\`)
    .then(res => {
      if (!res.ok) throw new Error("Failed to load widget config");
      return res.json();
    })
    .then(config => {
      if (config.is_active === false) {
          console.log("Taimako.AI Widget: Widget is currently disabled.");
          return;
      }
      initWidget(config);
    })
    .catch(err => console.error("Taimako.AI Widget Error:", err));

  function initWidget(config) {
    const primaryColor = config.primary_color || "#000000";

    // Launcher Button
    const button = document.createElement("div");
    button.style.width = "60px";
    button.style.height = "60px";
    button.style.borderRadius = "50%";
    button.style.backgroundColor = primaryColor;
    button.style.boxShadow = "0 4px 20px rgba(0,0,0,0.2)";
    button.style.cursor = "pointer";
    button.style.display = "flex";
    button.style.alignItems = "center";
    button.style.justifyContent = "center";
    button.style.transition = "all 0.2s ease";
    button.style.pointerEvents = "auto"; // Button always clickable
    button.style.transform = "scale(1)";
    button.onmouseover = () => button.style.transform = "scale(1.05)";
    button.onmouseout = () => button.style.transform = "scale(1)";

    const iconImg = document.createElement("img");
    iconImg.src = config.icon_url || "https://api.iconify.design/lucide:message-circle.svg?color=white";
    iconImg.style.width = "32px";
    iconImg.style.height = "32px";
    iconImg.alt = "Chat";
    button.appendChild(iconImg);
    container.appendChild(button);

    // Iframe Container (hidden by default)
    const iframeContainer = document.createElement("div");
    iframeContainer.style.width = "380px";
    iframeContainer.style.height = "580px";
    iframeContainer.style.maxHeight = "calc(100dvh - 100px)";
    iframeContainer.style.maxWidth = "calc(100vw - 40px)";
    iframeContainer.style.position = "absolute";
    iframeContainer.style.bottom = "80px";
    iframeContainer.style.right = "0";
    iframeContainer.style.borderRadius = "16px";
    iframeContainer.style.boxShadow = "0 12px 40px rgba(0,0,0,0.25)";
    iframeContainer.style.overflow = "hidden";
    iframeContainer.style.opacity = "0";
    iframeContainer.style.visibility = "hidden";
    iframeContainer.style.transform = "translateY(20px) translateZ(0)";
    iframeContainer.style.transition = "opacity 0.25s ease, transform 0.25s ease, visibility 0s linear 0.25s";
    iframeContainer.style.pointerEvents = "auto"; // ALWAYS auto — never none!
    iframeContainer.style.contain = "layout style paint"; // Critical for Chrome focus bug
    iframeContainer.style.transform = "translateZ(0)"; // Force GPU layer
    iframeContainer.style.backfaceVisibility = "hidden";

    // Capture context
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const referrer = document.referrer;
    const locationInfo = window.location.href;

    // Construct params
    const params = new URLSearchParams();
    if (referrer) params.append("ref", referrer);
    params.append("loc", locationInfo);
    params.append("tz", timezone);

    // Iframe
    const iframe = document.createElement("iframe");
    iframe.src = \`\${FRONTEND_URL}/widget/\${widgetId}?\${params.toString()}\`;
    iframe.title = "Taimako.AI Chat Widget";
    iframe.allow = "clipboard-write";
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "none";
    iframe.style.display = "block";
    iframe.style.backgroundColor = "transparent";
    iframe.style.touchAction = "manipulation";
    iframeContainer.appendChild(iframe);

    container.appendChild(iframeContainer);

    // Toggle state
    let isOpen = false;

    const openWidget = () => {
      isOpen = true;
      iframeContainer.style.opacity = "1";
      iframeContainer.style.visibility = "visible";
      iframeContainer.style.transform = "translateY(0) translateZ(0)";
      iframeContainer.style.transition = "opacity 0.25s ease, transform 0.25s ease, visibility 0s linear 0s";

      // Triple-focus attack — defeats Chrome DevTools iframe bug
      setTimeout(() => {
        iframe.focus();
        if (iframe.contentWindow) {
          iframe.contentWindow.focus();
        }
        // Tell React app to focus the first input
        iframe.contentWindow?.postMessage({ type: "TAIMAKO_WIDGET_FOCUS" }, "*");
      }, 200);
    };

    const closeWidget = () => {
      isOpen = false;
      iframeContainer.style.opacity = "0";
      iframeContainer.style.transform = "translateY(20px) translateZ(0)";
      iframeContainer.style.transition = "opacity 0.25s ease, transform 0.25s ease, visibility 0s linear 0.25s";
      setTimeout(() => {
        iframeContainer.style.visibility = "hidden";
      }, 250);
    };

    button.addEventListener("click", (e) => {
      e.stopPropagation();
      if (isOpen) closeWidget();
      else openWidget();
    });

    // Optional: Close when clicking outside
    document.addEventListener("click", (e) => {
      if (isOpen && !container.contains(e.target)) {
        closeWidget();
      }
    });

    // Prevent close when clicking inside widget
    iframeContainer.addEventListener("click", (e) => {
      e.stopPropagation();
    });
  }
})();`;

  return new NextResponse(scriptContent, {
    headers: {
      'Content-Type': 'application/javascript',
    },
  });
}
