class IDCard extends HTMLElement {
  static htmlTemplate = null;
  static cssSheet = null;
  static loadingPromise = null;

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  async connectedCallback() {
    try {
      // Load HTML + CSS only once globally
      if (!IDCard.loadingPromise) {
        IDCard.loadingPromise = this.loadResources();
      }
      await IDCard.loadingPromise;

      // Clone template content (fast, no network fetch)
      this.shadowRoot.innerHTML = IDCard.htmlTemplate;

      // Attach CSS (already parsed once)
      this.shadowRoot.adoptedStyleSheets = [IDCard.cssSheet];

      // Fill student data
      this.updateContent();

    } catch (error) {
      console.error("Error loading ID card:", error);
      this.shadowRoot.innerHTML = `
        <div style="padding: 20px; color: red; border: 1px solid red; border-radius: 8px;">
          <h3>Error Loading ID Card</h3>
          <p>${error.message}</p>
        </div>
      `;
    }
  }

  async loadResources() {
    // Load HTML once
    const htmlResponse = await fetch("/static/pdf-components/icards/hanging_image_icard.html");
    if (!htmlResponse.ok) throw new Error(`Failed to load HTML: ${htmlResponse.status}`);
    IDCard.htmlTemplate = await htmlResponse.text();

    // Load CSS once
    const cssResponse = await fetch("/static/pdf-components/icards/hanging_image_icard.css");
    if (!cssResponse.ok) throw new Error(`Failed to load CSS: ${cssResponse.status}`);
    const cssText = await cssResponse.text();

    IDCard.cssSheet = new CSSStyleSheet();
    IDCard.cssSheet.replaceSync(cssText);
  }

  updateContent() {
    const set = (attr, id) => {
      const el = this.shadowRoot.getElementById(id);
      if (!el) return;
      const value = this.getAttribute(attr) || "Unknown";
      if (el.tagName.toLowerCase() === "img") {
        el.src = value;
      } else {
        el.textContent = value;
      }
    };

    set("school-name", "school-name");
    set("school-UDISE", "school-UDISE");
    set("school-logo", "school-logo");
    set("session-logo", "session-logo");

    set("student-image", "student-image");
    set("student-name", "student-name");
    set("student-father", "student-father");

    set("student-class-roll", "student-class-roll");
    set("student-DOB", "student-DOB");
    set("student-phone", "student-phone");
    set("student-address", "student-address");

    set("teacher-sign", "teacher-sign");
    set("principal-sign", "principal-sign");
    set("school-address", "school-address");
    set("school-phone", "school-phone");
  }
}

customElements.define("hanging-image-icard", IDCard);
